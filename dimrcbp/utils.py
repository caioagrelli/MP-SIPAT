import os
from django.db import models

# --- Paths ---

def caminho_benspermanentes(instance, filename):
    tombamento = instance.tombo or 'sem_tombo'
    ext = os.path.splitext(filename)[1]
    nome_aquivo = f'{tombamento}{ext}'

    return f'bens/permanentes/{nome_aquivo}'

def caminho_catalogo(instance, filename):
    efisco = instance.efisco or 'sem_efisco'
    ext = os.path.splitext(filename)[1]
    nome_aquivo = f'{efisco}{ext}'

    return f'bens/permanentes/catalogo/{nome_aquivo}'

def caminho_inventario(instance, filename):
    periodo = getattr(instance, 'n_inventario', None)
    year = periodo.inicio.year if periodo and periodo.inicio else 'sem_data'
    tombo = instance.bem.tombo if getattr(instance, 'bem', None) else 'sem_tombo'
    ext = os.path.splitext(filename)[1]
    return f'bens/permanentes/inventarios/{year}/{tombo}{ext}'


# --- Choices ---
class AcaoPermanente(models.TextChoices):
    solicitacao = 'SOLICITACAO', 'Solicitação'
    devolucao = 'DEVOLUCAO', 'Devolução'
    tranferencia = 'TRANSFERENCIA', 'Transferência'

class SituacaoFisica(models.TextChoices):
    antieconomico = 'ANTIECONOMICO', 'Antieconômico'
    em_uso = 'EM_USO', 'Em Uso'
    irrecuperavel = 'IRRECUPERAVEL', 'Irrecuperável'
    ocioso = 'OCIOSO', 'Ocioso'
    recuperavel = 'RECUPERAVEL', 'Recuperável'
    
class EstadoConservacao(models.TextChoices):
    bom = 'BOM', 'Bom'
    novo = 'NOVO', 'Novo'
    precario = 'PRECARIO', 'Precário'
    regular = 'REGULAR', 'Regular'
    sucata = 'SUCATA', 'Sucata'

class SituacaoInventario(models.TextChoices):
    bom = 'BOM', 'Bom'
    regular = 'REGULAR', 'Regular'
    precario = 'PRECARIO', 'Precário'
    sucata = 'SUCATA', 'Sucata'

class GruposPermanentes(models.TextChoices):
    condicionador = 'CONDICIONADOR', 'Condicionador de Ar'
    eletroeletronico = 'ELETROELETRONICO', 'Eletroeletrônico'
    tic = 'TIC', 'Equipammentos de TIC'
    mobiliario = 'MOBILIARIO', 'Mobiliário'
    outros = 'OUTROS', 'Outros'
    
class StatusSolicitacaoCatalogo(models.TextChoices):
    pendente  = 'PENDENTE',  'Pendente'
    aprovada  = 'APROVADA',  'Aprovada'
    rejeitada = 'REJEITADA', 'Rejeitada'
    cancelada = 'CANCELADA', 'Cancelada'

class StatusSolicitacaoTransferencia(models.TextChoices):
    pendente  = 'PENDENTE',  'Pendente'
    aprovada  = 'APROVADA',  'Aprovada'
    rejeitada = 'REJEITADA', 'Rejeitada'
    cancelada = 'CANCELADA', 'Cancelada'

class Cores(models.TextChoices):
    BRANCO = 'BRANCO', 'Branco'
    PRETO = 'PRETO', 'Preto'
    CINZA = 'CINZA', 'Cinza'
    VERMELHO = 'VERMELHO', 'Vermelho'
    AZUL = 'AZUL', 'Azul'
    VERDE = 'VERDE', 'Verde'
    AMARELO = 'AMARELO', 'Amarelo'
    LARANJA = 'LARANJA', 'Laranja'
    ROXO = 'ROXO', 'Roxo'
    ROSA = 'ROSA', 'Rosa'
    MARROM = 'MARROM', 'Marrom'
    AZUL_CLARO = 'AZUL_CLARO', 'Azul claro'
    AZUL_ESCURO = 'AZUL_ESCURO', 'Azul escuro'
    VERDE_CLARO = 'VERDE_CLARO', 'Verde claro'
    VERDE_ESCURO = 'VERDE_ESCURO', 'Verde escuro'
    VERMELHO_ESCURO = 'VERMELHO_ESCURO', 'Vermelho escuro'
    AMARELO_CLARO = 'AMARELO_CLARO', 'Amarelo claro'
    CINZA_CLARO = 'CINZA_CLARO', 'Cinza claro'
    CINZA_ESCURO = 'CINZA_ESCURO', 'Cinza escuro'
    BEGE = 'BEGE', 'Bege'
    CREME = 'CREME', 'Creme'
    VINHO = 'VINHO', 'Vinho'
    BORDO = 'BORDO', 'Bordô'
    TURQUESA = 'TURQUESA', 'Turquesa'
    LILAS = 'LILAS', 'Lilás'
    SALMAO = 'SALMAO', 'Salmão'
    DOURADO = 'DOURADO', 'Dourado'
    PRATEADO = 'PRATEADO', 'Prateado'
    BRANCO_GELO = 'BRANCO_GELO', 'Branco gelo'
    BRANCO_FOSCO = 'BRANCO_FOSCO', 'Branco fosco'
    BRANCO_BRILHANTE = 'BRANCO_BRILHANTE', 'Branco brilhante'
    PRETO_FOSCO = 'PRETO_FOSCO', 'Preto fosco'
    PRETO_BRILHANTE = 'PRETO_BRILHANTE', 'Preto brilhante'
    GRAFITE = 'GRAFITE', 'Grafite'
    INOX = 'INOX', 'Inox'
    CROMADO = 'CROMADO', 'Cromado'
    AMADEIRADO = 'AMADEIRADO', 'Amadeirado'
    CARVALHO = 'CARVALHO', 'Carvalho'
    IMBUIA = 'IMBUIA', 'Imbuia'
    MOGNO = 'MOGNO', 'Mogno'
    NOGUEIRA = 'NOGUEIRA', 'Nogueira'
    
