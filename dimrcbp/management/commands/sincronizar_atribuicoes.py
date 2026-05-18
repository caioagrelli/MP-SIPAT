from django.core.management.base import BaseCommand

from dimrcbp.models import HistoryUas, sincronizar_atribuicao


class Command(BaseCommand):
    help = 'Sincroniza AtribuicaoBem para todos os bens com base no gestor da UA atual.'

    def handle(self, *args, **kwargs):
        historicos = (
            HistoryUas.objects
            .filter(current_ua__gestor__isnull=False)
            .select_related('tombo', 'current_ua__gestor')
        )

        total = historicos.count()
        if not total:
            self.stdout.write(self.style.WARNING('Nenhum bem com UA que tenha gestor cadastrado.'))
            return

        atualizados = 0
        for hist in historicos:
            sincronizar_atribuicao(hist.tombo, hist.current_ua)
            atualizados += 1
            self.stdout.write(f'  Tombo {hist.tombo.tombo} → {hist.current_ua.gestor.username}')

        self.stdout.write(self.style.SUCCESS(f'\n{atualizados}/{total} bens sincronizados.'))
