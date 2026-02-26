from django.db import models

# --- Choices ---
class TipoLocalizacao(models.TextChoices):
    pallet = 'PALLET', 'Pallet'
    prateleira = 'PRATELEIRA', 'Prateleira'