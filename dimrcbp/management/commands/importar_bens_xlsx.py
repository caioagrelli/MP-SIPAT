"""
Management command para importar bens permanentes a partir de planilha e-fisco.

Uso:
    python manage.py importar_bens_xlsx <caminho_do_arquivo.xlsx> [--sobrescrever]

Exemplo:
    python manage.py importar_bens_xlsx "Planilha de Migração Patrimonio Movel.xlsx"
    python manage.py importar_bens_xlsx planilha.xlsx --sobrescrever
"""
import sys
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from dimrcbp.views.importar_bens import (
    _ImportCache, _process_row, COL_TOMBO, COL_EFISCO,
)


class Command(BaseCommand):
    help = 'Importa bens permanentes a partir de planilha .xlsx do e-fisco'

    def add_arguments(self, parser):
        parser.add_argument('arquivo', type=str, help='Caminho para o arquivo .xlsx')
        parser.add_argument(
            '--sobrescrever',
            action='store_true',
            default=False,
            help='Sobrescreve bens que já existem no banco (pelo tombo)',
        )

    def handle(self, *args, **options):
        caminho = Path(options['arquivo'])
        if not caminho.exists():
            raise CommandError(f'Arquivo não encontrado: {caminho}')
        if caminho.suffix.lower() != '.xlsx':
            raise CommandError('Apenas arquivos .xlsx são aceitos.')

        sobrescrever = options['sobrescrever']

        try:
            import openpyxl
        except ImportError:
            raise CommandError('openpyxl não instalado. Execute: pip install openpyxl')

        self.stdout.write(f'Abrindo {caminho.name}...')
        wb = openpyxl.load_workbook(caminho, read_only=True, data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows())

        if len(rows) < 2:
            raise CommandError('Planilha vazia ou sem dados.')

        total     = sum(1 for r in rows[1:] if any(c.value is not None for c in r))
        self.stdout.write(f'Total de linhas com dados: {total}')
        self.stdout.write('')

        cache     = _ImportCache()
        criados   = 0
        pulados   = 0
        erros     = []
        processados = 0

        for row in rows[1:]:
            if all(c.value is None for c in row):
                continue

            resultado = _process_row(row, cache, sobrescrever)
            processados += 1

            if resultado['status'] == 'criado':
                criados += 1
            elif resultado['status'] == 'pulado':
                pulados += 1
            else:
                erros.append(resultado)

            # Progresso a cada 500 linhas
            if processados % 500 == 0:
                pct = processados * 100 // total
                self.stdout.write(
                    f'  [{pct:3d}%] {processados}/{total} — '
                    f'criados: {criados}  pulados: {pulados}  erros: {len(erros)}',
                    ending='\r',
                )
                self.stdout.flush()

        self.stdout.write('')
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'[OK] Importados:  {criados}'))
        self.stdout.write(self.style.WARNING(f'[--] Pulados:     {pulados}'))

        if erros:
            self.stdout.write(self.style.ERROR(f'[XX] Erros:       {len(erros)}'))
            self.stdout.write('')
            self.stdout.write('Detalhes dos erros:')
            for e in erros:
                self.stdout.write(f'  Tombo {e["tombo"]}: {e["msg"]}')
        else:
            self.stdout.write(self.style.SUCCESS('[OK] Sem erros!'))
