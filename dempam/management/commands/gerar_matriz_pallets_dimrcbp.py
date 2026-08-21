"""
Cadastra uma matriz 15x15 (225) de localizações do tipo Pallet no setor
"DIMRCBP PALLETS", com códigos no formato L01-C01 até L15-C15 (linha-coluna).

Idempotente — se um código já existir no setor, é ignorado.

Uso:
    python manage.py gerar_matriz_pallets_dimrcbp
    python manage.py gerar_matriz_pallets_dimrcbp --dry-run
"""
from django.core.management.base import BaseCommand, CommandError

from dempam.models import SetorDEMPAM, LocalizacaoDEMPAM
from dempam.utils import TipoLocalizacao

SETOR_NOME = 'DIMRCBP PALLETS'
LINHAS = 15
COLUNAS = 15


class Command(BaseCommand):
    help = 'Cadastra uma matriz 15x15 de localizações Pallet no setor DIMRCBP PALLETS'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Não grava nada, só mostra o que seria criado')

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        setor = SetorDEMPAM.objects.filter(setor=SETOR_NOME).first()
        if not setor:
            raise CommandError(f'Setor "{SETOR_NOME}" não encontrado. Cadastre-o antes de rodar este comando.')

        existentes = set(
            LocalizacaoDEMPAM.objects
            .filter(setor_sala=setor, tipo_localizacao=TipoLocalizacao.pallet)
            .values_list('prateleira_pallet', flat=True)
        )

        criadas = 0
        ja_existiam = 0
        novas = []

        for linha in range(1, LINHAS + 1):
            for coluna in range(1, COLUNAS + 1):
                codigo = f'L{linha:02d}-C{coluna:02d}'
                if codigo in existentes:
                    ja_existiam += 1
                    continue
                novas.append(codigo)
                criadas += 1

        if not dry_run:
            LocalizacaoDEMPAM.objects.bulk_create([
                LocalizacaoDEMPAM(
                    setor_sala=setor,
                    prateleira_pallet=codigo,
                    tipo_localizacao=TipoLocalizacao.pallet,
                )
                for codigo in novas
            ])

        self.stdout.write(self.style.SUCCESS(
            f'[{"DRY-RUN " if dry_run else ""}OK] Localizações criadas: {criadas} (de {LINHAS * COLUNAS})'
        ))
        if ja_existiam:
            self.stdout.write(self.style.WARNING(f'[--] Já existiam (ignoradas): {ja_existiam}'))
