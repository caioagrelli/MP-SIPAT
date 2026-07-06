"""
Management command para importar bens de consumo a partir de planilha .xlsx.

Colunas esperadas (por posição):
  0  ESSENCIAL         (SIM / vazio)
  1  Índice            (ignorado)
  2  Almoxarifado      (ignorado)
  3  Grupo
  4  E-fisco
  5  Descrição
  6  Unidade de medida
  7  Endereço          (ignorado)
  8  Marca
  9  Cons. mes. hist.  (ignorado)
 10  Consumo mensal
 11  Custo unit.       (ignorado)
 12  Duração           (ignorado — calculado)
 13  Validade
 14  Qtd. Estoque

Uso:
    python manage.py importar_bens_consumo_xlsx <caminho_do_arquivo.xlsx> [--sobrescrever]

Exemplo:
    python manage.py importar_bens_consumo_xlsx "Migração Bens de Consumo.xlsx"
    python manage.py importar_bens_consumo_xlsx planilha.xlsx --sobrescrever
"""
import re
import unicodedata
from datetime import date, datetime
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from dimms.models import BensConsumo, Estoque
from dimms.utils import GrupoConsumo, UnidadesMedida


# ---------------------------------------------------------------------------
# Mapeamento de grupos da planilha → GrupoConsumo choices
# ---------------------------------------------------------------------------
def _normalizar(texto: str) -> str:
    """Remove acentos e coloca em minúsculas para comparação robusta."""
    return ''.join(
        c for c in unicodedata.normalize('NFD', str(texto))
        if unicodedata.category(c) != 'Mn'
    ).lower().strip()


_GRUPO_MAP = {
    'alimentos':                     GrupoConsumo.alimento,
    'alimento':                      GrupoConsumo.alimento,
    'confeccao':                     GrupoConsumo.confeccao,
    'copa-cozinha':                  GrupoConsumo.copa_cozinha,
    'copa cozinha':                  GrupoConsumo.copa_cozinha,
    'domissanitarios':               GrupoConsumo.domissanitario,
    'domissanitario':                GrupoConsumo.domissanitario,
    'eletrica':                      GrupoConsumo.eletrica,
    'epi':                           GrupoConsumo.epi,
    'hidrossanitario':               GrupoConsumo.hidrosanitario,
    'hidrosanitario':                GrupoConsumo.hidrosanitario,
    'informatica':                   GrupoConsumo.informatica,
    'limpeza':                       GrupoConsumo.limpeza,
    'manutencao comum':              GrupoConsumo.manutencao,
    'manutencao':                    GrupoConsumo.manutencao,
    'marcenaria':                    GrupoConsumo.marcenaria,
    'pintura':                       GrupoConsumo.pintura,
    'papeis para expediente':        GrupoConsumo.papeis_expediente,
    'papeis de expediente':          GrupoConsumo.papeis_expediente,
    'expediente':                    GrupoConsumo.papeis_expediente,
    'papeis para limpeza':           GrupoConsumo.papeis_limpeza,
    'papeis de limpeza':             GrupoConsumo.papeis_limpeza,
    'refrigeracao':                  GrupoConsumo.refrigeracao,
    'toners':                        GrupoConsumo.toner,
    'toner':                         GrupoConsumo.toner,
    # grupos sem equivalente direto → mapeados para o mais próximo
    'construcao civil':              GrupoConsumo.manutencao,
    'bens permanentes transferidos': GrupoConsumo.manutencao,
    'estocagem':                     GrupoConsumo.manutencao,
    'telecom':                       GrupoConsumo.informatica,
}


def _mapear_grupo(raw) -> str:
    if not raw:
        return GrupoConsumo.manutencao
    return _GRUPO_MAP.get(_normalizar(str(raw)), GrupoConsumo.manutencao)


# ---------------------------------------------------------------------------
# Mapeamento de unidades da planilha → UnidadesMedida choices
# ---------------------------------------------------------------------------
def _mapear_unidade(raw) -> str:
    if not raw:
        return UnidadesMedida.unidade
    s = _normalizar(str(raw))

    if s.startswith('quilograma') or s in ('kg',) or s.startswith('sc ') or s.startswith('sc'):
        return UnidadesMedida.quilograma
    if s.startswith('litro') or s.startswith('lt') or s.startswith('gl') or s.startswith('lto') or s == 'bombona' or s.startswith('fs'):
        return UnidadesMedida.litro
    if s.startswith('pacote') or s in ('pct', 'pct.', 'pc', 'pc 100 un'):
        return UnidadesMedida.pacote
    if s.startswith('caixa') or s in ('cx', 'cx 10 und', 'cx 100 um', 'cx 100 und.', 'cx 3 und', 'crt 2 und', 'crt 4 und'):
        return UnidadesMedida.caixa
    if s in ('m', 'm2', 'm²', 'rolo') or s.startswith('rl') or s.startswith('vara') or s.startswith('p 100') or s.startswith('p100') or 'metro' in s:
        return UnidadesMedida.metro
    # UNIDADE e variantes (UN, UND, UNID, etc.)
    return UnidadesMedida.unidade


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _cel(row, idx: int) -> str:
    try:
        val = row[idx].value
    except IndexError:
        return ''
    if val is None:
        return ''
    return str(val).strip()


def _inteiro(val) -> int:
    if val is None or val == '':
        return 0
    try:
        return max(0, int(float(str(val))))
    except (ValueError, TypeError):
        return 0


def _date(val) -> date | None:
    if val is None or val == '':
        return None
    if isinstance(val, (date, datetime)):
        return val.date() if isinstance(val, datetime) else val
    s = str(val).strip()
    for fmt in ('%Y-%m-%d %H:%M:%S', '%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y'):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


# ---------------------------------------------------------------------------
# Processamento de uma linha
# ---------------------------------------------------------------------------
def _process_row(row, sobrescrever: bool) -> dict:
    # Layout da planilha: ALMOXARIFADO | GRUPO | E-FISCO | DESCRIÇÃO | UNIDADE | MARCA | PREÇO | VALIDADE | QTD.ESTOQUE | ...
    efisco_raw = _cel(row, 2)
    # Remove decimais que o Excel adiciona em números (ex: "4809661.0" → "4809661")
    efisco = re.sub(r'\.0$', '', efisco_raw)[:20]

    if not efisco or efisco.lower() in ('none', ''):
        return {'status': 'erro', 'efisco': '—', 'msg': 'Sem código E-fisco'}

    descricao = _cel(row, 3) or efisco
    grupo     = _mapear_grupo(_cel(row, 1))
    unidade   = _mapear_unidade(_cel(row, 4))
    marca     = _cel(row, 5)[:40] or 'Não informada'
    validade  = _date(_cel(row, 7) or None)
    qtd       = _inteiro(_cel(row, 8))
    essencial = str(_cel(row, 0)).strip().lower() == 'essencial'

    try:
        with transaction.atomic():
            try:
                bem = BensConsumo.objects.get(efisco=efisco)
                if not sobrescrever:
                    return {'status': 'pulado', 'efisco': efisco, 'msg': 'Já existe, pulado'}
                # Atualiza o BensConsumo sem deletar (mantém FKs protegidas)
                bem.descricao_efisco = descricao
                bem.medida = unidade
                bem.grupo_consumo = grupo
                bem.save(update_fields=['descricao_efisco', 'medida', 'grupo_consumo'])
                # Atualiza o Estoque vinculado
                for e in bem.bem_estoque.all():
                    e.amount_shock = qtd
                    e.mark = marca
                    e.essential = essencial
                    e.validity = validade
                    e.description_manual = descricao[:90]
                    e.save(update_fields=['amount_shock', 'mark', 'essential', 'validity', 'description_manual'])
            except BensConsumo.DoesNotExist:
                bem = BensConsumo.objects.create(
                    efisco=efisco,
                    descricao_efisco=descricao,
                    medida=unidade,
                    grupo_consumo=grupo,
                )
                Estoque.objects.create(
                    item_shock=bem,
                    description_manual=descricao[:90],
                    mark=marca,
                    amount_shock=qtd,
                    essential=essencial,
                    validity=validade,
                    form_input='Importação',
                )

    except Exception as exc:
        return {'status': 'erro', 'efisco': efisco, 'msg': str(exc)}

    return {'status': 'criado', 'efisco': efisco, 'msg': 'Importado com sucesso'}


# ---------------------------------------------------------------------------
# Management Command
# ---------------------------------------------------------------------------
class Command(BaseCommand):
    help = 'Importa bens de consumo a partir de planilha .xlsx'

    def add_arguments(self, parser):
        parser.add_argument('arquivo', type=str, help='Caminho para o arquivo .xlsx')
        parser.add_argument(
            '--sobrescrever',
            action='store_true',
            default=False,
            help='Sobrescreve bens que já existem no banco (pelo código E-fisco)',
        )

    def handle(self, *args, **options):
        caminho = Path(options['arquivo'])
        if not caminho.exists():
            raise CommandError(f'Arquivo não encontrado: {caminho}')
        if caminho.suffix.lower() != '.xlsx':
            raise CommandError('Apenas arquivos .xlsx são aceitos.')

        sobrescrever = options['sobrescrever']

        try:
            import openpyxl
        except ImportError:
            raise CommandError('openpyxl não instalado. Execute: pip install openpyxl')

        self.stdout.write(f'Abrindo {caminho.name}...')
        wb = openpyxl.load_workbook(caminho, read_only=True, data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows())

        # Linha 0 = cabeçalho, dados a partir da linha 1
        dados = [r for r in rows[1:] if any(c.value is not None for c in r)]
        total = len(dados)

        if total == 0:
            raise CommandError('Planilha sem dados.')

        self.stdout.write(f'Total de linhas com dados: {total}')
        self.stdout.write('')

        criados     = 0
        pulados     = 0
        erros       = []
        processados = 0

        for row in dados:
            resultado = _process_row(row, sobrescrever)
            processados += 1

            if resultado['status'] == 'criado':
                criados += 1
            elif resultado['status'] == 'pulado':
                pulados += 1
            else:
                erros.append(resultado)

            if processados % 100 == 0:
                pct = processados * 100 // total
                self.stdout.write(
                    f'  [{pct:3d}%] {processados}/{total} — '
                    f'criados: {criados}  pulados: {pulados}  erros: {len(erros)}',
                    ending='\r',
                )
                self.stdout.flush()

        self.stdout.write('')
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'[OK] Importados:  {criados}'))
        self.stdout.write(self.style.WARNING(f'[--] Pulados:     {pulados}'))

        if erros:
            self.stdout.write(self.style.ERROR(f'[XX] Erros:       {len(erros)}'))
            self.stdout.write('')
            self.stdout.write('Detalhes dos erros:')
            for e in erros:
                self.stdout.write(f'  E-fisco {e["efisco"]}: {e["msg"]}')
        else:
            self.stdout.write(self.style.SUCCESS('[OK] Sem erros!'))
