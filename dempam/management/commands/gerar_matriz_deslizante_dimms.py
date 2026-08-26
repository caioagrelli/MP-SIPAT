"""
Cadastra as localizações do setor "DIMMS DESLIZANTE": corredores de A até H,
cada um com 3 posições — 1 e 3 são vãos únicos (código "<corredor><vão>", ex.
"A1", "A3"), o vão 2 é uma prateleira de 5 níveis (código "<corredor>2<nível>",
ex. "A21"..."A25").

Idempotente — se um código já existir no setor, é ignorado.

Uso:
    python manage.py gerar_matriz_deslizante_dimms
    python manage.py gerar_matriz_deslizante_dimms --dry-run
"""
import string

from django.core.management.base import BaseCommand, CommandError

from dempam.models import SetorDEMPAM, LocalizacaoDEMPAM
from dempam.utils import TipoLocalizacao

SETOR_NOME = 'DIMMS DESLIZANTE'
CORREDORES = list(string.ascii_uppercase[:8])  # A até H
NIVEIS_VAO_2 = 5


class Command(BaseCommand):
    help = 'Cadastra os corredores A-H (vãos 1, 2 com 5 níveis, e 3) no setor DIMMS DESLIZANTE'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Não grava nada, só mostra o que seria criado')

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        setor = SetorDEMPAM.objects.filter(setor=SETOR_NOME).first()
        if not setor:
            raise CommandError(f'Setor "{SETOR_NOME}" não encontrado. Cadastre-o antes de rodar este comando.')

        existentes = set(
            LocalizacaoDEMPAM.objects
            .filter(setor_sala=setor)
            .values_list('prateleira_pallet', flat=True)
        )

        planejadas = []
        for corredor in CORREDORES:
            planejadas.append((f'{corredor}1', TipoLocalizacao.pallet, corredor, '1', ''))
            for nivel in range(1, NIVEIS_VAO_2 + 1):
                planejadas.append((f'{corredor}2{nivel}', TipoLocalizacao.prateleira, corredor, '2', str(nivel)))
            planejadas.append((f'{corredor}3', TipoLocalizacao.pallet, corredor, '3', ''))

        novas = [p for p in planejadas if p[0] not in existentes]
        ja_existiam = len(planejadas) - len(novas)

        if not dry_run:
            LocalizacaoDEMPAM.objects.bulk_create([
                LocalizacaoDEMPAM(
                    setor_sala=setor,
                    prateleira_pallet=codigo,
                    tipo_localizacao=tipo,
                    corredor=corredor,
                    estante=estante,
                    prateleira=prateleira,
                )
                for codigo, tipo, corredor, estante, prateleira in novas
            ])

        self.stdout.write(self.style.SUCCESS(
            f'[{"DRY-RUN " if dry_run else ""}OK] Localizações criadas: {len(novas)} (de {len(planejadas)})'
        ))
        if ja_existiam:
            self.stdout.write(self.style.WARNING(f'[--] Já existiam (ignoradas): {ja_existiam}'))
