# Importações do Django
from django.apps import AppConfig

# =================================
# APPS DA DIMMS (BENS DE CONSUMO)
# =================================



class DimmsConfig(AppConfig):
    name = 'dimms'

    def ready(self):
        import dimms.signals  # noqa: F401
