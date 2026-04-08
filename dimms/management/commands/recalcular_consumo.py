from django.core.management.base import BaseCommand
from dimms.services import recalcular_consumo


class Command(BaseCommand):
    help = "Recalcula consumo mensal dos itens"

    def handle(self, *args, **kwargs):
        recalcular_consumo()
        self.stdout.write(self.style.SUCCESS("Consumo recalculado com sucesso."))