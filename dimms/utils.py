import os 
from django.db import models
from django.utils import timezone

# --- Paths ---

def caminho_bensconsumo(instance, filename):
    item_shock = instance.item_shock or 'sem_efisco'
    ext = os.path.splitext(filename)[1]
    nome_aquivo = f'{item_shock}{ext}'
    
    return f'bens/consumo/{nome_aquivo}'

def caminho_movimentacao_consumo(instance, filename):
    n_movimentacao = instance.id
    ext = os.path.splitext(filename)[1]
    nome_aquivo = f'{n_movimentacao}{ext}'
    
    return f'documentos/movimentacao_consumo/{nome_aquivo}'

def caminho_nf_compraindividual(instance, filename):
    n_nf = instance.id
    ext = os.path.splitext(filename)[1]
    nome_aquivo = f'{n_nf}{ext}'
    
    return f'documentos/consumo/nf_individual/{nome_aquivo}'

def caminho_consum_update(instance, filename):
    n_update = instance.id
    ext = os.path.splitext(filename)[1]
    nome_aquivo = f'{n_update}{ext}'
    
    return f'documentos/consumo/anexo_atualizacao/{nome_aquivo}'

# documentação dos artefatos
def path_documents_artifacts(instance, filename, tipo):
    code = instance.artifacts_code
    ext = os.path.splitext(filename)[1].lower()

    return f'artefatos/{code}/{tipo}{ext}'


def path_tr(instance, filename):
    return path_documents_artifacts(instance, filename, 'tr')

def path_etp(instance, filename):
    return path_documents_artifacts(instance, filename, 'etp')

def path_rgpp(instance, filename):
    return path_documents_artifacts(instance, filename, 'rgpp')

def path_dode(instance, filename):
    return path_documents_artifacts(instance, filename, 'dode')

def path_tapp(instance, filename):
    return path_documents_artifacts(instance, filename, 'tapp')

def path_risk_analysis(instance, filename):
    return path_documents_artifacts(instance, filename, 'risk_analysis')


# --- Choices ---
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
    
class Cota(models.TextChoices):
    principal = 'PRINCIPAL', 'Principal'
    reservada = 'RESERVADA', 'Reservada'
    
class UnidadesMedida(models.TextChoices):
    metro = 'METRO', 'Metro'
    unidade = 'UNIDADE', 'Unidade' 
    quilograma = 'QUILOGRAMA', 'Quilograma'
    litro = 'LITRO', 'Litro'
    pacote = 'PACOTE', 'Pacote'
    caixa = 'CAIXA', 'Caixa'

class Status(models.TextChoices):
    rascunho = 'RASCUNHO', 'Rascunho'
    atendida = 'ATENDIDA', 'Atendida'
    cancelada = 'CANCELADA', 'Cancelada'
    analise = 'EM ANÁLISE', 'Em análise'
    
class StatusTramitacao(models.TextChoices):
    atendimento = 'ATENDIMENTO', 'Em Atendimento'
    aguar_separada = 'AGUAR_SEPARACAO', 'Aguardando Separação'
    separada = 'SEPARADA', 'Separada'   
    em_expedicao = 'EXPEDICAO', 'Em Expedicação'
    recebida = 'RECEBIDA', 'Recebida'
    cancelada = 'CANCELADA', 'Cancelada'
    rascunho = 'RASCUNHO', 'Rascunho'
    

# --- Utils ---
def calcular_duracao(amount_shock, monthly_consumption):
    if amount_shock is None or monthly_consumption in (None, 0):
        return None

    meses = amount_shock / monthly_consumption

    if meses < 1:
        dias = round(meses * 30)
        return f"{dias} dias"

    return f"{round(meses, 1)} meses"
