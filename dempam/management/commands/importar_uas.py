import openpyxl
from django.core.management.base import BaseCommand
from dempam.models import InfoUA, CircunscricaoPredio


def _find_parent_code(codigo):
    """Deriva o código da UA pai com base na hierarquia do código."""
    code_str = str(codigo).zfill(12)
    prefix = code_str[:6]
    suffix = code_str[6:]
    stripped = suffix.rstrip('0')
    if not stripped:
        return None
    parent_suffix = stripped[:-1].ljust(6, '0')
    return prefix + parent_suffix


class Command(BaseCommand):
    help = 'Importa UAs da planilha de Centro de Custos'

    def add_arguments(self, parser):
        parser.add_argument(
            'arquivo',
            nargs='?',
            default='docs/CENTRO DE CUSTOS 10-06-26.xlsx',
            help='Caminho da planilha .xlsx',
        )
        parser.add_argument(
            '--sobrescrever',
            action='store_true',
            help='Atualiza UAs já existentes pelo código',
        )

    def handle(self, *args, **options):
        arquivo = options['arquivo']
        sobrescrever = options['sobrescrever']

        try:
            wb = openpyxl.load_workbook(arquivo)
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f'Arquivo não encontrado: {arquivo}'))
            return

        ws = wb.active
        circunscricao_padrao, _ = CircunscricaoPredio.objects.get_or_create(
            local='A Definir'
        )

        # --- Passo 1: cria/atualiza todas as UAs ---
        criadas = 0
        atualizadas = 0
        codigos_importados = {}

        for row in ws.iter_rows(values_only=True):
            if not isinstance(row[0], int):
                continue

            nome = str(row[1]).strip() if row[1] else ''
            sigla = str(row[2]).strip() if row[2] else ''
            nivel = int(row[4]) if row[4] else None
            codigo = str(row[5]).zfill(12) if row[5] else None

            if not codigo or not nome:
                continue

            ua_qs = InfoUA.objects.filter(codigo=codigo)

            if ua_qs.exists():
                if sobrescrever:
                    ua = ua_qs.first()
                    ua.ua = nome
                    ua.sigla = sigla
                    ua.nivel = nivel
                    ua.save(update_fields=['ua', 'sigla', 'nivel'])
                    atualizadas += 1
                else:
                    ua = ua_qs.first()
            else:
                ua = InfoUA.objects.create(
                    circunscricao_predio=circunscricao_padrao,
                    ua=nome,
                    sigla=sigla,
                    nivel=nivel,
                    codigo=codigo,
                )
                criadas += 1

            codigos_importados[codigo] = ua.pk

        self.stdout.write(f'Passo 1 — {criadas} criadas, {atualizadas} atualizadas.')

        # --- Passo 2: vincula parents ---
        vinculadas = 0
        for codigo, pk in codigos_importados.items():
            parent_code = _find_parent_code(codigo)
            if parent_code and parent_code in codigos_importados:
                InfoUA.objects.filter(pk=pk).update(
                    parent_id=codigos_importados[parent_code]
                )
                vinculadas += 1

        self.stdout.write(f'Passo 2 — {vinculadas} vínculos de hierarquia definidos.')
        self.stdout.write(self.style.SUCCESS('Importação concluída.'))
