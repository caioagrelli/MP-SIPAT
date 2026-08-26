"""
Envia os gastos (por item e por UA) de um mês pra uma planilha Google — pra
alimentar um BI externo (ex.: Looker Studio) sem precisar expor o banco nem
depender de licença do Power BI.

Idempotente por mês: antes de escrever, remove quaisquer linhas já existentes
daquele Ano/Mês nas duas abas, então roda de novo sem duplicar.

Configuração (.env): GOOGLE_SHEETS_ID e GOOGLE_SHEETS_CREDENTIALS_PATH
(veja .env.example). Se GOOGLE_SHEETS_ID estiver vazio, o comando é pulado
com um aviso — não quebra o deploy.

Uso:
    python manage.py enviar_gastos_google_sheets                  # mês anterior ao atual
    python manage.py enviar_gastos_google_sheets --mes 2026-08    # mês específico (backfill)
    python manage.py enviar_gastos_google_sheets --dry-run
"""
import calendar
from datetime import date
from types import SimpleNamespace

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.http import QueryDict

from dempam.views.root import _montar_gastos_por_ua
from dimms.views.relatorios import _montar_gastos_por_item, MESES_PT
from dimms.utils import GrupoConsumo

CABECALHO_ITEM = ['Ano', 'Mês', 'E-Fisco', 'Descrição', 'Grupo', 'Quantidade', 'Preço Médio', 'Gasto']
CABECALHO_UA = ['Ano', 'Mês', 'UA', 'Sigla', 'Município', 'Código IBGE', 'Circunscrição', 'Solicitações', 'Quantidade', 'Gasto']


def _mes_anterior(hoje):
    primeiro_dia_mes_atual = hoje.replace(day=1)
    ultimo_dia_mes_anterior = primeiro_dia_mes_atual.fromordinal(primeiro_dia_mes_atual.toordinal() - 1)
    return ultimo_dia_mes_anterior.year, ultimo_dia_mes_anterior.month


def _request_do_mes(ano, mes):
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    qd = QueryDict(mutable=True)
    qd['data_de'] = date(ano, mes, 1).isoformat()
    qd['data_ate'] = date(ano, mes, ultimo_dia).isoformat()
    return SimpleNamespace(GET=qd)


class Command(BaseCommand):
    help = 'Envia os gastos por item e por UA de um mês pra uma planilha Google (BI externo)'

    def add_arguments(self, parser):
        parser.add_argument('--mes', help='Mês a enviar, formato AAAA-MM (padrão: mês anterior ao atual)')
        parser.add_argument('--dry-run', action='store_true', help='Não grava na planilha, só mostra o que seria enviado')

    def handle(self, *args, **options):
        if not settings.GOOGLE_SHEETS_ID:
            self.stdout.write(self.style.WARNING(
                '[--] GOOGLE_SHEETS_ID não configurado no .env — envio pulado.'
            ))
            return

        if options['mes']:
            try:
                ano, mes = (int(p) for p in options['mes'].split('-'))
            except ValueError:
                raise CommandError('--mes precisa estar no formato AAAA-MM, ex.: 2026-08')
        else:
            ano, mes = _mes_anterior(date.today())

        req = _request_do_mes(ano, mes)
        dados_item = _montar_gastos_por_item(req)
        dados_ua = _montar_gastos_por_ua(req)
        labels_grupo = dict(GrupoConsumo.choices)

        linhas_item = [
            [
                ano, MESES_PT[mes],
                linha['item'].efisco,
                linha['item'].descricao_efisco,
                labels_grupo.get(linha['item'].grupo_consumo, linha['item'].grupo_consumo),
                float(linha['total_qtd']),
                float(linha['item'].preco_medio) if linha['item'].preco_medio is not None else '',
                float(linha['total_gasto']),
            ]
            for linha in dados_item['linhas']
        ]
        linhas_ua = [
            [
                ano, MESES_PT[mes],
                linha['ua'].ua,
                linha['ua'].sigla or '',
                linha['ua'].municipio.nome if linha['ua'].municipio else '',
                linha['ua'].municipio.codigo_ibge if linha['ua'].municipio else '',
                linha['ua'].municipio.circunscricao if linha['ua'].municipio else '',
                linha['total_pedidos'],
                float(linha['total_qtd']),
                float(linha['total_gasto']),
            ]
            for linha in dados_ua['linhas']
        ]

        self.stdout.write(f'Mês de referência: {MESES_PT[mes]}/{ano}')
        self.stdout.write(f'Linhas — Gastos por Item: {len(linhas_item)} | Gastos por UA: {len(linhas_ua)}')

        if options['dry_run']:
            self.stdout.write(self.style.SUCCESS('[DRY-RUN] Nada foi enviado.'))
            return

        try:
            import gspread
            from google.oauth2.service_account import Credentials
        except ImportError:
            raise CommandError('Dependência "gspread" não instalada — rode "pip install -r requirements.txt".')

        try:
            creds = Credentials.from_service_account_file(
                settings.GOOGLE_SHEETS_CREDENTIALS_PATH,
                scopes=['https://www.googleapis.com/auth/spreadsheets'],
            )
        except FileNotFoundError:
            raise CommandError(
                f'Arquivo de credenciais não encontrado em "{settings.GOOGLE_SHEETS_CREDENTIALS_PATH}". '
                'Configure GOOGLE_SHEETS_CREDENTIALS_PATH no .env.'
            )

        gc = gspread.authorize(creds)
        planilha = gc.open_by_key(settings.GOOGLE_SHEETS_ID)

        self._enviar_aba(planilha, 'Gastos por Item', CABECALHO_ITEM, linhas_item, ano, mes)
        self._enviar_aba(planilha, 'Gastos por UA', CABECALHO_UA, linhas_ua, ano, mes)

        self.stdout.write(self.style.SUCCESS(f'[OK] Gastos de {MESES_PT[mes]}/{ano} enviados pro Google Sheets.'))

    def _enviar_aba(self, planilha, nome_aba, cabecalho, linhas_novas, ano, mes):
        try:
            aba = planilha.worksheet(nome_aba)
        except Exception:
            aba = planilha.add_worksheet(title=nome_aba, rows=1000, cols=len(cabecalho))
            aba.append_row(cabecalho)

        valores = aba.get_all_values()
        if not valores:
            aba.append_row(cabecalho)
            valores = [cabecalho]

        # remove linhas já existentes do mesmo Ano/Mês (idempotência), preservando o resto
        mes_nome = MESES_PT[mes]
        linhas_restantes = [valores[0]] + [
            linha for linha in valores[1:]
            if not (len(linha) >= 2 and linha[0] == str(ano) and linha[1] == mes_nome)
        ]

        if len(linhas_restantes) != len(valores):
            aba.clear()
            aba.append_rows(linhas_restantes)

        if linhas_novas:
            aba.append_rows(linhas_novas)
