import os

from django.db import models

# --- Choices ---
class TipoLocalizacao(models.TextChoices):
    pallet = 'PALLET', 'Pallet'
    prateleira = 'PRATELEIRA', 'Prateleira'


# --- Upload paths ---
def path_video_painel_tv(instance, filename):
    ext = os.path.splitext(filename)[1]
    return f'painel_tv/video{ext}'