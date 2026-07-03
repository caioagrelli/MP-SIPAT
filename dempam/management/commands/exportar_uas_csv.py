from django.core.management.base import BaseCommand
from dempam.models import InfoUA


class Command(BaseCommand):
    help = 'Exporta todas as UAs para um arquivo XLSX'

    def add_arguments(self, parser):
        parser.add_argument('arquivo', nargs='?', default='uas_export.xlsx',
                            help='Caminho do arquivo XLSX de saída')

    def handle(self, *args, **options):
        import openpyxl
        from openpyxl.styles import Font

        arquivo = options['arquivo']
        qs = InfoUA.objects.select_related('circunscricao_predio', 'gestor').order_by('ua')

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'UAs'

        headers = [
            'ID', 'UA', 'Circunscricao/Predio', 'Contato', 'Responsavel',
            'Matricula Resp', 'Email', 'Sede', 'Gestor (ID)', 'Gestor (Username)',
        ]
        ws.append(headers)
        for cell in ws[1]:
            cell.font = Font(bold=True)

        for obj in qs:
            ws.append([
                obj.pk,
                obj.ua,
                obj.circunscricao_predio.local if obj.circunscricao_predio else '',
                obj.contato_ua or '',
                obj.responsavel_ua or '',
                obj.mat_resp_ua or '',
                obj.email_ua or '',
                'Sim' if obj.sede else 'Não',
                obj.gestor_id or '',
                obj.gestor.username if obj.gestor else '',
            ])

        ws.auto_filter.ref = ws.dimensions

        wb.save(arquivo)
        self.stdout.write(self.style.SUCCESS(f'Exportadas {qs.count()} UAs para {arquivo}'))
