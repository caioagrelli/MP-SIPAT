import os 
from django.db import models

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
    processamento = 'PROCESSAMENTO', 'EM Processamento'
    separada = 'SEPARADA', 'Separada'
    para_envio = 'ENVIO', 'Para Envio'
    em_tramitacao = 'TRAMITACAO', 'Em Tramitação'
    recebida = 'RECEBIDA', 'Recebida'
    cancelada = 'CANCELADA', 'Cancelada'