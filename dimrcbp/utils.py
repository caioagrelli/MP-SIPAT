import os
from django.db import models

# --- Paths ---

def caminho_benspermanentes(instance, filename):
    tombamento = instance.tombamento_legado or 'sem_tombo'
    ext = os.path.splitext(filename)[1]
    nome_aquivo = f'{tombamento}{ext}'
    
    return f'bens/permanentes/{nome_aquivo}'

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