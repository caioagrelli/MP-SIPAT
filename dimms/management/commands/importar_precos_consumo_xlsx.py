"""
Management command para importar preço médio e almoxarifado (Geral/Reservado)
dos bens de consumo, a partir de planilha .xlsx.

Colunas esperadas (por posição):
  0  E-Fisco
  1  Preço          (formato "R$ 12,34")
  2  Almoxarifado   (Geral / Reservado)

Um mesmo E-Fisco pode aparecer mais de uma vez na planilha (preço diferente
por almoxarifado). Como BensConsumo guarda só um preço/almoxarifado por
E-Fisco, quando houver mais de uma linha válida (com preço) pro mesmo
E-Fisco, prevalece a última linha da planilha.

Uso:
    python manage.py importar_precos_consumo_xlsx "docs/preço consumo.xlsx"
"""
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from dimms.models import BensConsumo
from dimms.utils import TipoAlmoxarifado


def _cel(row, idx):
    try:
        val = row[idx].value
    except IndexError:
        return None
    if val is None:
        return None
    return val


def _efisco(val):
    if val is None:
        return ''
    texto = str(val).strip()
    return re.sub(r'\.0$', '', texto)[:20]


def _preco(val):
    if val is None:
        return None
    texto = str(val).strip()
    if not texto:
        return None
    texto = texto.replace('R$', '').strip()
    # remove separador de milhar e troca vírgula decimal por ponto
    texto = texto.replace('.', '').replace(',', '.')
    try:
        preco = Decimal(texto)
    except InvalidOperation:
        return None
    return preco if preco > 0 else None


_ALMOXARIFADO_MAP = {
    'geral': TipoAlmoxarifado.geral,
    'reservado': TipoAlmoxarifado.reservado,
}


def _almoxarifado(val):
    if val is None:
        return None
    return _ALMOXARIFADO_MAP.get(str(val).strip().lower())


class Command(BaseCommand):
    help = 'Importa preço médio e almoxarifado (Geral/Reservado) dos bens de consumo a partir de planilha .xlsx'

    def add_arguments(self, parser):
        parser.add_argument('arquivo', type=str, help='Caminho para o arquivo .xlsx')

    def handle(self, *args, **options):
        caminho = Path(options['arquivo'])
        if not caminho.exists():
            raise CommandError(f'Arquivo não encontrado: {caminho}')
        if caminho.suffix.lower() != '.xlsx':
            raise CommandError('Apenas arquivos .xlsx são aceitos.')

        try:
            import openpyxl
        except ImportError:
            raise CommandError('openpyxl não instalado. Execute: pip install openpyxl')

        self.stdout.write(f'Abrindo {caminho.name}...')
        wb = openpyxl.load_workbook(caminho, read_only=True, data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows())
        dados = [r for r in rows[1:] if any(c.value is not None for c in r)]
        self.stdout.write(f'Total de linhas com dados: {len(dados)}')
        self.stdout.write('')

        # --- 1. Resolve conflitos: mantém a última linha válida (com preço) por E-Fisco ---
        por_efisco = {}
        sem_efisco = 0
        for row in dados:
            efisco = _efisco(_cel(row, 0))
            if not efisco:
                sem_efisco += 1
                continue

            preco = _preco(_cel(row, 1))
            almoxarifado = _almoxarifado(_cel(row, 2))

            if preco is None:
                por_efisco.setdefault(efisco, None)
                continue
            por_efisco[efisco] = (preco, almoxarifado)

        # --- 2. Aplica no BensConsumo ---
        atualizados = 0
        sem_preco = 0
        nao_encontrados = []

        for efisco, dado in por_efisco.items():
            if dado is None:
                sem_preco += 1
                continue
            preco, almoxarifado = dado

            bem = BensConsumo.objects.filter(efisco=efisco).first()
            if not bem:
                nao_encontrados.append(efisco)
                continue

            bem.preco_medio = preco
            update_fields = ['preco_medio']
            if almoxarifado:
                bem.almoxarifado = almoxarifado
                update_fields.append('almoxarifado')
            bem.save(update_fields=update_fields)
            atualizados += 1

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'[OK] Bens atualizados (preço + almoxarifado): {atualizados}'))
        self.stdout.write(self.style.WARNING(f'[--] E-Fiscos sem preço na planilha (ignorados): {sem_preco}'))
        self.stdout.write(self.style.WARNING(f'[--] Linhas sem E-Fisco (ignoradas): {sem_efisco}'))

        if nao_encontrados:
            self.stdout.write(self.style.ERROR(f'[XX] E-Fiscos não cadastrados no sistema: {len(nao_encontrados)}'))
            for efisco in nao_encontrados[:30]:
                self.stdout.write(f'  {efisco}')
            if len(nao_encontrados) > 30:
                self.stdout.write(f'  ... e mais {len(nao_encontrados) - 30}')
