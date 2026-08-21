import os

from django.db import models

# --- Choices ---
class TipoLocalizacao(models.TextChoices):
    pallet = 'PALLET', 'Pallet'
    prateleira = 'PRATELEIRA', 'Prateleira'


class TipoSetor(models.TextChoices):
    dimms = 'DIMMS', 'DIMMS — Bens de Consumo'
    dimrcbp = 'DIMRCBP', 'DIMRCBP — Bens Permanentes'


# --- Upload paths ---
def path_video_painel_tv(instance, filename):
    ext = os.path.splitext(filename)[1]
    return f'painel_tv/video{ext}'