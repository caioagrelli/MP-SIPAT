# Importações do Python
import os
from decimal import Decimal, InvalidOperation

# Importações do Django
from django.db import models, transaction, IntegrityError
from django.utils import timezone

# =================================
# UTILS DA DIMMS (BENS DE CONSUMO)
# =================================



''' Paths '''
def path_photo_catalogo_consumo(instance, filename):
    ext = os.path.splitext(filename)[1]
    return f'bens/catalogo_consumo/{instance.pk or "novo"}{ext}'


def path_photo_bens(instance, filename):
    item_shock = instance.item_shock or 'sem_efisco'
    ext = os.path.splitext(filename)[1]
    nome_aquivo = f'{item_shock}{ext}'
    
    return f'bens/consumo/{nome_aquivo}'

# Solicitações
def path_solicitation(instance, filename):
    n_movimentacao = instance.id
    ext = os.path.splitext(filename)[1]
    nome_aquivo = f'{n_movimentacao}{ext}'
    
    return f'documentos/movimentacao_consumo/{nome_aquivo}'

# Documento atualização tramitações
def path_solicitation_update(instance, filename):
    n_update = instance.id
    ext = os.path.splitext(filename)[1]
    nome_aquivo = f'{n_update}{ext}'
    
    return f'documentos/consumo/atualizacao_anexo/{nome_aquivo}'

# Foto atualização tramitações
def path_solicitation_photo(instance, filename):
    n_update = instance.id
    ext = os.path.splitext(filename)[1]
    nome_aquivo = f'{n_update}{ext}'

    return f'documentos/consumo/atualizacao_foto/{nome_aquivo}'

# Assinatura de quem recebeu (capturada na tela, recebimento em lote)
def path_solicitation_assinatura(instance, filename):
    n_update = instance.id
    ext = os.path.splitext(filename)[1]
    nome_aquivo = f'{n_update}{ext}'

    return f'documentos/consumo/atualizacao_assinatura/{nome_aquivo}'

# Documentação dos Artefatos (base)
def path_documents_artifacts(instance, filename, tipo):
    code = instance.artifacts_code
    ext = os.path.splitext(filename)[1].lower()

    return f'artefatos/{code}/{tipo}{ext}'

# TR (derivado)
def path_tr(instance, filename):
    return path_documents_artifacts(instance, filename, 'tr')

# ETP (derivado)
def path_etp(instance, filename):
    return path_documents_artifacts(instance, filename, 'etp')

# RGPP (derivado)
def path_rgpp(instance, filename):
    return path_documents_artifacts(instance, filename, 'rgpp')

# DODE (derivado)
def path_dode(instance, filename):
    return path_documents_artifacts(instance, filename, 'dode')

# TAPP (derivado)
def path_tapp(instance, filename):
    return path_documents_artifacts(instance, filename, 'tapp')

# ANALISE DE RISCO (derivado)
def path_risk_analysis(instance, filename):
    return path_documents_artifacts(instance, filename, 'risk_analysis')

def path_comprovante_remessa(instance, filename):
    ext = os.path.splitext(filename)[1]
    return f'saldo_ativo/remessas/comprovantes/{instance.pk or "novo"}{ext}'

def path_nota_fiscal_solicitacao(instance, filename):
    ext = os.path.splitext(filename)[1]
    codigo = (instance.codigo or 'novo').replace('/', '-')
    return f'saldo_ativo/solicitacoes/nota_fiscal/{codigo}{ext}'

def path_empenho_solicitacao(instance, filename):
    ext = os.path.splitext(filename)[1]
    codigo = (instance.codigo or 'novo').replace('/', '-')
    return f'saldo_ativo/solicitacoes/empenho/{codigo}{ext}'

def path_termo_recebimento_solicitacao(instance, filename):
    ext = os.path.splitext(filename)[1]
    codigo = (instance.codigo or 'novo').replace('/', '-')
    return f'saldo_ativo/solicitacoes/termo_recebimento/{codigo}{ext}'

def path_documento_aditivo(instance, filename):
    ext = os.path.splitext(filename)[1]
    numero = (instance.numero or 'novo').replace('/', '-')
    return f'saldo_ativo/aditivos/{numero}{ext}'


''' Choices'''
# Grupos dos bens de consumo 
class GrupoConsumo(models.TextChoices):
    alimento = 'ALIMENTO', 'Alimento'
    confeccao = 'CONFECCAO', 'Confecção'
    copa_cozinha = 'COPA_COZINHA', 'Copa / Cozinha'
    domissanitario = 'DOMISSANITARIO', 'Domissanitário'
    eletrica = 'ELETRICA', 'Elétrica'
    epi = 'EPI', 'EPI'
    hidrosanitario = 'HIDROSANITARIO', 'Hidrossanitário'
    informatica = 'INFORMATICA', 'Informática'
    limpeza = 'LIMPEZA', 'Limpeza'
    manutencao = 'MANUTENCAO', 'Manutenção'
    marcenaria = 'MARCENARIA', 'Marcenaria'
    pintura = 'PINTURA', 'Pintura'
    papeis_expediente = 'PAPEIS_EXPEDIENTE', 'Papéis de Expediente'
    papeis_limpeza = 'PAPEIS_LIMPEZA', 'Papéis de Limpeza'
    refrigeracao = 'REFRIGERACAO', 'Refrigeração'
    toner = 'TONER', 'Toner'

# Classificação do Almoxarifado
class TipoAlmoxarifado(models.TextChoices):
    geral     = 'GERAL',     'Almoxarifado Geral'
    reservado = 'RESERVADO', 'Almoxarifado Reservado'

# Cotas Existentes
class Cota(models.TextChoices):
    principal = 'PRINCIPAL', 'Principal'
    reservada = 'RESERVADA', 'Reservada'
    
# Unidades de medida
class UnidadesMedida(models.TextChoices):
    metro = 'METRO', 'Metro'
    unidade = 'UNIDADE', 'Unidade' 
    quilograma = 'QUILOGRAMA', 'Quilograma'
    litro = 'LITRO', 'Litro'
    pacote = 'PACOTE', 'Pacote'
    caixa = 'CAIXA', 'Caixa'

#Status 
class Status(models.TextChoices):
    rascunho = 'RASCUNHO', 'Rascunho'
    atendida = 'ATENDIDA', 'Atendida'
    cancelada = 'CANCELADA', 'Cancelada'
    analise = 'EM ANÁLISE', 'Em análise'
    
# Status das tramitações
class StatusTramitacao(models.TextChoices):
    atendimento = 'ATENDIMENTO', 'Em Atendimento'
    aguar_separada = 'AGUAR_SEPARACAO', 'Aguardando Separação'
    separada = 'SEPARADA', 'Separada'   
    em_expedicao = 'EXPEDICAO', 'Em Expedicação'
    recebida = 'RECEBIDA', 'Recebida'
    cancelada = 'CANCELADA', 'Cancelada'
    rascunho = 'RASCUNHO', 'Rascunho'

# Status das propostas
class StatusProposal(models.TextChoices):
    analise = 'ANALISE', 'Em Análise'
    aprovado = 'APROVADO', 'Aprovado'
    recusado = 'RECUSADO', 'Recusado'

# Status das solicitações do catálogo de consumo
class StatusSolicitacaoCatalogoConsumo(models.TextChoices):
    pendente  = 'PENDENTE',  'Pendente'
    atendida  = 'ATENDIDA',  'Atendida'
    rejeitada = 'REJEITADA', 'Rejeitada'
    cancelada = 'CANCELADA', 'Cancelada'

# Status do contrato (saldo ativo)
class StatusContrato(models.TextChoices):
    vigente   = 'VIGENTE',   'Vigente'
    cancelado = 'CANCELADO', 'Cancelado'

# Status do artefato
class StatusArtifacts(models.TextChoices):
    elaboracao = 'ELABORACAO', 'Em Elaboração'
    compras = 'COMPRAS', 'Encaminhado para GMEC'
    reencaminhado = 'REENCAMINHADO', 'Reencaminhado para Elaboração'
    licitacao = 'LICITACAO', 'Em Licitação'
    analise = 'ANALISE', 'Em Análise das Propostas'
    vencedora = 'VENCEDORA', 'Encaminhado Vencedora'
    homologado = 'HOMOLOGADO', 'Homologado'

# Status do acompanhamento de SEI
class StatusAcompanhamentoSei(models.TextChoices):
    em_andamento = 'EM_ANDAMENTO', 'Em Andamento'
    concluido = 'CONCLUIDO', 'Concluído'
    arquivado = 'ARQUIVADO', 'Arquivado'

# Decisão sobre uma divergência encontrada na conferência de inventário
class DecisaoAjusteEstoque(models.TextChoices):
    pendente = 'PENDENTE', 'Pendente'
    aprovado = 'APROVADO', 'Aprovado'
    rejeitado = 'REJEITADO', 'Rejeitado'


''' Funções Úteis (não que o resto não seja né)'''
# Calcular duração do estoque (quantidade / consumo mensal)
def calcular_duracao(amount_shock, monthly_consumption):
    if amount_shock is None or monthly_consumption in (None, 0):
        return None

    meses = amount_shock / monthly_consumption

    if meses < 1:
        dias = round(meses * 30)
        return f"{dias} dias"

    return f"{round(meses, 1)} meses"


# Converte texto de quantidade (aceita vírgula ou ponto decimal, ex: "2,3" ou "2.3")
# pra Decimal. Levanta ValueError se vazio/inválido — quem chama decide a mensagem.
def parse_quantidade(valor):
    if valor is None:
        raise ValueError('Quantidade vazia.')
    texto = str(valor).strip().replace(',', '.')
    if not texto:
        raise ValueError('Quantidade vazia.')
    try:
        return Decimal(texto)
    except InvalidOperation:
        raise ValueError(f'Quantidade inválida: "{valor}".')


# Só permite quantidade fracionada (com casas decimais) quando a unidade de medida é METRO.
# Levanta ValueError se a quantidade tiver parte decimal e a unidade não for METRO.
def validar_quantidade_por_unidade(quantidade, medida):
    if quantidade is None:
        return
    if medida == UnidadesMedida.metro:
        return
    if Decimal(quantidade) % 1 != 0:
        raise ValueError(
            'Quantidade fracionada só é permitida para itens com unidade de medida em metro.'
        )


# Formata Decimal pra exibição sem zeros à direita desnecessários (2.30 -> 2,3 | 5.00 -> 5)
def formatar_quantidade(valor):
    if valor is None:
        return '—'
    if not isinstance(valor, Decimal):
        try:
            valor = Decimal(str(valor))
        except InvalidOperation:
            return str(valor)
    texto = format(valor.normalize(), 'f')
    return texto.replace('.', ',')


# Gera o próximo código sequencial do ano (ex.: SBC-2026-0001) pra um campo único de um model.
# Baseado no MAIOR número já usado no ano — não em count() — pra não colidir quando algum
# código no meio da sequência foi apagado (deixando "buracos" que fariam count()+1 repetir
# um número que já existe).
def gerar_proximo_codigo(model, campo, prefixo, digitos=4):
    ano = timezone.now().year
    prefixo_ano = f'{prefixo}-{ano}-'
    ultimo_codigo = (
        model.objects
        .filter(**{f'{campo}__startswith': prefixo_ano})
        .order_by(f'-{campo}')
        .values_list(campo, flat=True)
        .first()
    )
    ultimo_numero = int(ultimo_codigo.rsplit('-', 1)[-1]) if ultimo_codigo else 0
    return f'{prefixo_ano}{ultimo_numero + 1:0{digitos}d}'


# Gera o código (via gerar_proximo_codigo) e chama save_callable dentro de uma transação,
# tentando de novo com o próximo número se colidir por causa de uma corrida entre requisições
# simultâneas. Só engole o IntegrityError se ele for mesmo sobre esse campo — qualquer outro
# erro (ex.: FK obrigatória faltando) sobe na hora, sem mascarar a causa real.
def salvar_com_codigo_sequencial(instance, campo, prefixo, save_callable, *args, digitos=4, tentativas=5, **kwargs):
    model = type(instance)
    for _ in range(tentativas):
        setattr(instance, campo, gerar_proximo_codigo(model, campo, prefixo, digitos))
        try:
            with transaction.atomic():
                save_callable(*args, **kwargs)
            return
        except IntegrityError as e:
            if campo not in str(e):
                raise
            setattr(instance, campo, '')
    raise IntegrityError(f'Não foi possível gerar um código único ({prefixo}) após {tentativas} tentativas.')
