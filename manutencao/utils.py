import os

from django.db import models


''' Paths '''
def path_photo_bem_manutencao(instance, filename):
    efisco = instance.item.efisco if instance.item_id else 'sem_efisco'
    ext = os.path.splitext(filename)[1]
    return f'manutencao/estoque/{efisco}{ext}'


''' Choices '''
class UnidadesMedida(models.TextChoices):
    metro = 'METRO', 'Metro'
    unidade = 'UNIDADE', 'Unidade'
    quilograma = 'QUILOGRAMA', 'Quilograma'
    litro = 'LITRO', 'Litro'
    pacote = 'PACOTE', 'Pacote'
    caixa = 'CAIXA', 'Caixa'


class GrupoManutencao(models.TextChoices):
    eletrica = 'ELETRICA', 'Elétrica'
    hidraulica = 'HIDRAULICA', 'Hidráulica'
    marcenaria = 'MARCENARIA', 'Marcenaria'
    pintura = 'PINTURA', 'Pintura'
    refrigeracao = 'REFRIGERACAO', 'Refrigeração'
    serralheria = 'SERRALHERIA', 'Serralheria'
    alvenaria = 'ALVENARIA', 'Alvenaria'
    ferramentas = 'FERRAMENTAS', 'Ferramentas'
    epi = 'EPI', 'EPI'
    outros = 'OUTROS', 'Outros'
