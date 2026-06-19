import re
from django.core.management.base import BaseCommand
from dempam.models import InfoUA


# Substituições de palavras inteiras (case-insensitive, maiúsculas na saída)
ABREVIACOES = [
    # (?<![A-Za-z]) = não precedido por letra; (?![A-Za-z]) = não seguido de letra
    # Isso permite que o número fique colado: 10PRM -> 10PROMOTORIA
    (r'(?<![A-Za-z])DIV(?![A-Za-z])',   'DIVISÃO'),
    (r'(?<![A-Za-z])DEPTO(?![A-Za-z])', 'DEPARTAMENTO'),
    (r'(?<![A-Za-z])DEP(?![A-Za-z])',   'DEPARTAMENTO'),
    (r'(?<![A-Za-z])PRM(?![A-Za-z])',   'PROMOTORIA'),
    (r'(?<![A-Za-z])PROM(?![A-Za-z])',  'PROMOTORIA'),
]

# Palavras sem acento → com acento (palavra inteira)
ACENTOS = [
    (r'\bADMINISTRACAO\b',   'ADMINISTRAÇÃO'),
    (r'\bAUTUACAO\b',        'AUTUAÇÃO'),
    (r'\bCIDADANIA\b',       'CIDADANIA'),
    (r'\bCOMISSAO\b',        'COMISSÃO'),
    (r'\bCOORDENACAO\b',     'COORDENAÇÃO'),
    (r'\bDIRECAO\b',         'DIREÇÃO'),
    (r'\bDIVISAO\b',         'DIVISÃO'),
    (r'\bEXECUCAO\b',        'EXECUÇÃO'),
    (r'\bFORMACAO\b',        'FORMAÇÃO'),
    (r'\bINFORMACAO\b',      'INFORMAÇÃO'),
    (r'\bINFORMACOES\b',     'INFORMAÇÕES'),
    (r'\bINSTRUCAO\b',       'INSTRUÇÃO'),
    (r'\bINSTRUCOES\b',      'INSTRUÇÕES'),
    (r'\bINVESTIGACAO\b',    'INVESTIGAÇÃO'),
    (r'\bJUSTICA\b',         'JUSTIÇA'),
    (r'\bOPERACAO\b',        'OPERAÇÃO'),
    (r'\bOPERAcOES\b',       'OPERAÇÕES'),
    (r'\bPRODUCAO\b',        'PRODUÇÃO'),
    (r'\bPROMOCAO\b',        'PROMOÇÃO'),
    (r'\bRELACAO\b',         'RELAÇÃO'),
    (r'\bSECAO\b',           'SEÇÃO'),
    (r'\bSITUACAO\b',        'SITUAÇÃO'),
    (r'\bSOLUCAO\b',         'SOLUÇÃO'),
    (r'\bTRANSICAO\b',       'TRANSIÇÃO'),
    (r'\bAVALIACAO\b',       'AVALIAÇÃO'),
    (r'\bGESTAO\b',          'GESTÃO'),
    (r'\bAUDITORIA\b',       'AUDITORIA'),
    (r'\bATUACAO\b',         'ATUAÇÃO'),
    (r'\bREDACOES\b',        'REDAÇÕES'),
    (r'\bNEGOCIACAO\b',      'NEGOCIAÇÃO'),
    (r'\bPROTECAO\b',        'PROTEÇÃO'),
    (r'\bFISCALIZACAO\b',    'FISCALIZAÇÃO'),
    (r'\bREGULACAO\b',       'REGULAÇÃO'),
    (r'\bPLANIFICACAO\b',    'PLANIFICAÇÃO'),
    (r'\bCOMUNICACAO\b',     'COMUNICAÇÃO'),
    (r'\bORGANIZACAO\b',     'ORGANIZAÇÃO'),
]

ALL_RULES = ABREVIACOES + ACENTOS


def normalizar(nome):
    resultado = nome
    for padrao, substituto in ALL_RULES:
        resultado = re.sub(padrao, substituto, resultado, flags=re.IGNORECASE)
    return resultado


class Command(BaseCommand):
    help = 'Normaliza nomes das UAs: expande abreviações e adiciona acentos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas exibe as mudanças sem salvar',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        alteradas = 0
        inalteradas = 0

        for ua in InfoUA.objects.all().order_by('ua'):
            novo = normalizar(ua.ua)
            if novo != ua.ua:
                self.stdout.write(f'  {ua.ua!r}  ->  {novo!r}')
                if not dry_run:
                    ua.ua = novo
                    ua.save(update_fields=['ua'])
                alteradas += 1
            else:
                inalteradas += 1

        modo = '[DRY-RUN] ' if dry_run else ''
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'{modo}{alteradas} UAs alteradas, {inalteradas} inalteradas.'
        ))
