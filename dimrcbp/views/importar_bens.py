"""
Importação de bens permanentes a partir de planilha e-fisco (.xlsx).

Colunas esperadas (por posição — formato padrão do e-fisco):
  0  TITULARIDADE
  1  CÓDIGO DO E-FISCO
  2  DESCRIÇÃO
  3  FORMA DE CONTROLE
  4  TIPO DO BEM
  5  IMOBILIZADO
  6  MARCA
  7  FABRICANTE
  8  MODELO
  9  NÚMERO DE SÉRIE
 10  SITUAÇÃO JURÍDICA
 11  SITUAÇÃO FÍSICA
 12  ESTADO DE CONSERVAÇÃO
 13  FORMA DE INGRESSO
 14  NÚMERO DO DOCUMENTO
 15  TIPO DO DOCUMENTO
 16  CÓDIGO UNIDADE COMPRADORA
 17  CNPJ FORNECEDOR
 18  DATA AQUISICAO
 19  MODALIDADE
 20  NÚMERO DO PROCESSO
 21  DATA DA ENTREGA
 22  CÓD. NATUREZA DE DESPESA
 23  MOEDA
 24  NÚMERO DA AF
 25  NÚMERO DO EMPENHO
 26  GARANTIA EM DIAS
 27  VALOR UNITÁRIO
 28  QTDE.
 29  OBSERVAÇÃO
 30  CENTRO DE CUSTO
 31  CONTA CONTÁBIL
 32  TOMBAMENTO LEGADO
 33  UNIDADE GESTORA
 34  NOME RESPONSÁVEL
"""
import re
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.shortcuts import render

from dimrcbp.models import (
    BensPermanentes, Description, Groups, HistoryUas,
    Supplier, Type, sincronizar_atribuicao,
)
from dimrcbp.utils import EstadoConservacao, SituacaoFisica
from dempam.models import CircunscricaoPredio, InfoUA


# ---------------------------------------------------------------------------
# Índices das colunas no arquivo e-fisco (não confiar nos nomes — encoding quebrado)
# ---------------------------------------------------------------------------
COL_EFISCO        = 1
COL_DESCRICAO     = 2
COL_TIPO          = 4
COL_MARCA         = 6
COL_FABRICANTE    = 7
COL_MODELO        = 8
COL_N_SERIE       = 9
COL_SITUACAO      = 11
COL_ESTADO        = 12
COL_FORMA_INGR    = 13
COL_CNPJ          = 17
COL_DT_AQUISICAO  = 18
COL_MODALIDADE    = 19
COL_N_PROCESSO    = 20
COL_DT_ENTREGA    = 21
COL_N_EMPENHO     = 25
COL_GARANTIA_DIAS = 26
COL_VALOR         = 27
COL_CENTRO_CUSTO  = 30   # nome descritivo da UA (ex: "PROMOTORIAS DE CARUARU")
COL_TOMBO         = 32
COL_RESPONSAVEL   = 34   # nome do responsável da UA


# ---------------------------------------------------------------------------
# Mapeamento de texto livre → choices
# ---------------------------------------------------------------------------
_SITUACAO_MAP = {
    'em uso':        SituacaoFisica.em_uso,
    'ocioso':        SituacaoFisica.ocioso,
    'recuperavel':   SituacaoFisica.recuperavel,
    'recuperável':   SituacaoFisica.recuperavel,
    'irrecuperavel': SituacaoFisica.irrecuperavel,
    'irrecuperável': SituacaoFisica.irrecuperavel,
    'antieconomico': SituacaoFisica.antieconomico,
    'antieconômico': SituacaoFisica.antieconomico,
}

_ESTADO_MAP = {
    'novo':     EstadoConservacao.novo,
    'bom':      EstadoConservacao.bom,
    'regular':  EstadoConservacao.regular,
    'precario': EstadoConservacao.precario,
    'precário': EstadoConservacao.precario,
    'sucata':   EstadoConservacao.sucata,
    # valores que aparecem no e-fisco mas não têm equivalente direto
    'em uso':   EstadoConservacao.bom,
    'otimo':    EstadoConservacao.novo,
    'ótimo':    EstadoConservacao.novo,
}


# ---------------------------------------------------------------------------
# Helpers de conversão
# ---------------------------------------------------------------------------
def _cel(row, idx: int) -> str:
    """Extrai célula por índice e retorna string limpa."""
    try:
        val = row[idx].value
    except IndexError:
        return ''
    if val is None:
        return ''
    return str(val).strip()


def _date(val) -> date | None:
    if val is None or val == '':
        return None
    if isinstance(val, date):
        return val
    s = str(val).strip()
    for fmt in ('%Y-%m-%d %H:%M:%S', '%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y'):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _decimal(val) -> Decimal:
    if val is None or val == '':
        return Decimal('0.00')
    if isinstance(val, (int, float)):
        return Decimal(str(val)).quantize(Decimal('0.01'))
    s = str(val).strip().replace('.', '').replace(',', '.')
    try:
        return Decimal(s).quantize(Decimal('0.01'))
    except InvalidOperation:
        return Decimal('0.00')


def _clean_cnpj(raw) -> str:
    """Formata CNPJ, recuperando zero à esquerda perdido pelo Excel."""
    digits = re.sub(r'\D', '', str(raw))
    # Excel armazena CNPJ como número e perde o zero inicial
    digits = digits.zfill(14)
    if len(digits) == 14:
        return f'{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}'
    return str(raw)[:22]


# ---------------------------------------------------------------------------
# Caches em memória para não repetir queries para cada linha
# ---------------------------------------------------------------------------
class _ImportCache:
    def __init__(self):
        self._grupo_importado = None
        self._types: dict[str, Type] = {}
        self._descs: dict[str, Description] = {}
        self._suppliers: dict[str, Supplier | None] = {}
        self._uas: dict[str, InfoUA | None] = {}

    def grupo_importado(self) -> Groups:
        if self._grupo_importado is None:
            self._grupo_importado, _ = Groups.objects.get_or_create(group='Importado')
        return self._grupo_importado

    def get_or_create_type(self, tipo_nome: str) -> Type:
        key = tipo_nome[:30] or 'Outros'
        if key not in self._types:
            tipo, _ = Type.objects.get_or_create(
                type=key,
                defaults={'gruop': self.grupo_importado()},
            )
            self._types[key] = tipo
        return self._types[key]

    def get_or_create_description(self, descricao: str, tipo_nome: str) -> Description:
        tipo = self.get_or_create_type(tipo_nome)
        key = descricao[:200] or tipo_nome[:30] or 'Sem descrição'
        if key not in self._descs:
            desc, _ = Description.objects.get_or_create(
                description=key,
                defaults={'type': tipo},
            )
            self._descs[key] = desc
        return self._descs[key]

    def get_or_create_supplier(self, cnpj_raw: str) -> Supplier | None:
        if not cnpj_raw:
            return None
        # CNPJ zerado (0, 00000000000000) → sem fornecedor
        digits = re.sub(r'\D', '', str(cnpj_raw)).zfill(14)
        if set(digits) == {'0'}:
            return None
        cnpj = _clean_cnpj(cnpj_raw)
        if cnpj not in self._suppliers:
            supplier, _ = Supplier.objects.get_or_create(
                cnpj=cnpj,
                defaults={'name': f'Fornecedor {cnpj}'},
            )
            self._suppliers[cnpj] = supplier
        return self._suppliers[cnpj]

    def _circunscricao_padrao(self) -> CircunscricaoPredio:
        circ, _ = CircunscricaoPredio.objects.get_or_create(local='A Definir')
        return circ

    def get_or_create_ua(self, centro_custo: str, responsavel: str = '') -> InfoUA | None:
        if not centro_custo:
            return None
        key = centro_custo
        if key not in self._uas:
            try:
                self._uas[key] = InfoUA.objects.get(ua=centro_custo)
            except InfoUA.DoesNotExist:
                self._uas[key] = InfoUA.objects.create(
                    ua=centro_custo[:100],
                    circunscricao_predio=self._circunscricao_padrao(),
                    responsavel_ua=responsavel[:60] if responsavel else 'Não Consta',
                )
            except InfoUA.MultipleObjectsReturned:
                self._uas[key] = InfoUA.objects.filter(ua=centro_custo).first()
        return self._uas[key]


# ---------------------------------------------------------------------------
# Processamento de uma linha
# ---------------------------------------------------------------------------
def _process_row(row, cache: _ImportCache, sobrescrever: bool) -> dict:
    tombo = _cel(row, COL_TOMBO) or _cel(row, COL_EFISCO)
    tombo = tombo[:20]
    if not tombo:
        return {'status': 'erro', 'tombo': '—', 'msg': 'Sem tombo/código identificador'}

    if BensPermanentes.objects.filter(tombo=tombo).exists():
        if not sobrescrever:
            return {'status': 'pulado', 'tombo': tombo, 'msg': 'Já existe, pulado'}
        # Remove HistoryUas primeiro (PROTECT impede delete direto do bem)
        HistoryUas.objects.filter(tombo__tombo=tombo).delete()
        BensPermanentes.objects.filter(tombo=tombo).delete()

    try:
        with transaction.atomic():
            supplier    = cache.get_or_create_supplier(_cel(row, COL_CNPJ))
            description = cache.get_or_create_description(
                _cel(row, COL_DESCRICAO),
                _cel(row, COL_TIPO),
            )

            marca = (_cel(row, COL_MARCA) or _cel(row, COL_FABRICANTE))[:60]

            dt_aquisicao = _date(row[COL_DT_AQUISICAO].value) or _date(row[COL_DT_ENTREGA].value)
            entrega      = _date(row[COL_DT_ENTREGA].value)
            garantia_vencimento = None
            garantia_raw = _cel(row, COL_GARANTIA_DIAS)
            if entrega and garantia_raw:
                try:
                    garantia_vencimento = entrega + timedelta(days=int(float(garantia_raw)))
                except (ValueError, TypeError):
                    pass

            situacion = _SITUACAO_MAP.get(_cel(row, COL_SITUACAO).lower(), SituacaoFisica.em_uso)
            state     = _ESTADO_MAP.get(_cel(row, COL_ESTADO).lower(), EstadoConservacao.bom)
            value     = _decimal(row[COL_VALOR].value)

            entry_method = _cel(row, COL_FORMA_INGR)[:15] or 'Compra'
            n_empenho    = _cel(row, COL_N_EMPENHO)[:20] or 'S/Número'
            n_process    = _cel(row, COL_N_PROCESSO)[:20] or 'S/Número'
            modality     = _cel(row, COL_MODALIDADE)[:25] or 'Pregão Eletrônico'

            bem = BensPermanentes.objects.create(
                tombo=tombo,
                description=description,
                mark=marca,
                model=_cel(row, COL_MODELO)[:60],
                n_series=_cel(row, COL_N_SERIE)[:30],
                acquisition_date=dt_aquisicao,
                garantia_vencimento=garantia_vencimento,
                value=value,
                state=state,
                situacion=situacion,
                entry_method=entry_method,
                n_empenho=n_empenho,
                n_process=n_process,
                modality=modality,
                supllier=supplier,
            )

            ua = cache.get_or_create_ua(
                _cel(row, COL_CENTRO_CUSTO),
                _cel(row, COL_RESPONSAVEL),
            )
            HistoryUas.objects.create(tombo=bem, current_ua=ua)
            sincronizar_atribuicao(bem, ua)

    except Exception as exc:
        return {'status': 'erro', 'tombo': tombo, 'msg': str(exc)}

    return {'status': 'criado', 'tombo': tombo, 'msg': 'Importado com sucesso'}


# ---------------------------------------------------------------------------
# View
# ---------------------------------------------------------------------------
@login_required
@permission_required('dimrcbp.add_benspermanentes', raise_exception=True)
def importar_bens(request):
    if request.method == 'GET':
        return render(request, 'dimrcbp/importar_bens.html')

    arquivo     = request.FILES.get('arquivo')
    sobrescrever = request.POST.get('sobrescrever') == '1'

    if not arquivo:
        messages.error(request, 'Selecione um arquivo .xlsx.')
        return render(request, 'dimrcbp/importar_bens.html')

    if not arquivo.name.lower().endswith('.xlsx'):
        messages.error(request, 'Apenas arquivos .xlsx são aceitos.')
        return render(request, 'dimrcbp/importar_bens.html')

    try:
        import openpyxl
        wb = openpyxl.load_workbook(arquivo, read_only=True, data_only=True)
        ws = wb.active
    except Exception as exc:
        messages.error(request, f'Erro ao abrir o arquivo: {exc}')
        return render(request, 'dimrcbp/importar_bens.html')

    rows = list(ws.iter_rows())
    if len(rows) < 2:
        messages.error(request, 'Planilha sem dados (apenas cabeçalho ou vazia).')
        return render(request, 'dimrcbp/importar_bens.html')

    cache      = _ImportCache()
    resultados = []

    for row in rows[1:]:
        if all(c.value is None for c in row):
            continue
        resultados.append(_process_row(row, cache, sobrescrever))

    criados = [r for r in resultados if r['status'] == 'criado']
    pulados = [r for r in resultados if r['status'] == 'pulado']
    erros   = [r for r in resultados if r['status'] == 'erro']

    return render(request, 'dimrcbp/importar_bens.html', {
        'resultados': resultados,
        'criados':    criados,
        'pulados':    pulados,
        'erros':      erros,
        'concluido':  True,
    })
