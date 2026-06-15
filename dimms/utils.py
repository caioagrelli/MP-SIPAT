# Importações do Python
import os 

# Importações do Django
from django.db import models
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

# Status do artefato
class StatusArtifacts(models.TextChoices):
    elaboracao = 'ELABORACAO', 'Em Elaboração'
    compras = 'COMPRAS', 'Encaminhado para GMEC'
    reencaminhado = 'REENCAMINHADO', 'Reencaminhado para Elaboração'
    licitacao = 'LICITACAO', 'Em Licitação'
    analise = 'ANALISE', 'Em Análise das Propostas'
    vencedora = 'VENCEDORA', 'Encaminhado Vencedora'
    homologado = 'HOMOLOGADO', 'Homologado'


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
