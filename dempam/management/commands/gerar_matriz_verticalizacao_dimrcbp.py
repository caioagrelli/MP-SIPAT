"""
Cadastra as localizações do setor "DIMRCBP VERTICALIZAÇÃO": corredores de A
até J, cada um com 6 estantes de 6 níveis (prateleiras) — códigos de "A11" a
"A66" (e o mesmo padrão repetido em B, C, ..., J).

Idempotente — se um código já existir no setor, é ignorado.

Uso:
    python manage.py gerar_matriz_verticalizacao_dimrcbp
    python manage.py gerar_matriz_verticalizacao_dimrcbp --dry-run
"""
import string

from django.core.management.base import BaseCommand, CommandError

from dempam.models import SetorDEMPAM, LocalizacaoDEMPAM
from dempam.utils import TipoLocalizacao

SETOR_NOME = 'DIMRCBP VERTICALIZAÇÃO'
CORREDORES = list(string.ascii_uppercase[:10])  # A até J
ESTANTES = 6
NIVEIS = 6


class Command(BaseCommand):
    help = 'Cadastra os corredores A-J (6 estantes x 6 níveis cada) no setor DIMRCBP VERTICALIZAÇÃO'

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

        planejadas = [
            (f'{corredor}{estante}{nivel}', corredor, str(estante), str(nivel))
            for corredor in CORREDORES
            for estante in range(1, ESTANTES + 1)
            for nivel in range(1, NIVEIS + 1)
        ]

        novas = [p for p in planejadas if p[0] not in existentes]
        ja_existiam = len(planejadas) - len(novas)

        if not dry_run:
            LocalizacaoDEMPAM.objects.bulk_create([
                LocalizacaoDEMPAM(
                    setor_sala=setor,
                    prateleira_pallet=codigo,
                    tipo_localizacao=TipoLocalizacao.prateleira,
                    corredor=corredor,
                    estante=estante,
                    prateleira=prateleira,
                )
                for codigo, corredor, estante, prateleira in novas
            ])

        self.stdout.write(self.style.SUCCESS(
            f'[{"DRY-RUN " if dry_run else ""}OK] Localizações criadas: {len(novas)} (de {len(planejadas)})'
        ))
        if ja_existiam:
            self.stdout.write(self.style.WARNING(f'[--] Já existiam (ignoradas): {ja_existiam}'))
