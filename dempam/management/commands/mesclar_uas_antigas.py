"""
Management command para mesclar UAs antigas (sem codigo) com UAs da planilha (com codigo).

Uso:
    python manage.py mesclar_uas_antigas          # dry-run (apenas simula)
    python manage.py mesclar_uas_antigas --apply  # aplica as mesclas

Padrao das UAs antigas: NPRMJUS [TIPO] CIDADE
Padrao das UAs planilha: GAB N PROM JUSTICA [TIPO] CIDADE
                         GAB N PJ CRIMINAL/CIVEL/DEFESA DA CIDADANIA CIDADE
                         GAB N PJDC CIDADE
                         GAB N PJ CIDADE (sem tipo, generico)
"""

import re
import unicodedata

from django.core.management.base import BaseCommand
from django.db import transaction

from dempam.models import InfoUA


# ---------------------------------------------------------------------------
# Utilitarios
# ---------------------------------------------------------------------------

def normalizar(texto):
    """Remove acentos, uppercase, espacos multiplos."""
    texto = texto.upper().strip()
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    texto = re.sub(r'\s+', ' ', texto)
    return texto


ABREVIACOES_CIDADE = {
    'JAB GUARARAP': 'JABOATAO DOS GUARARAPES',
    'JAB GUARARAPES': 'JABOATAO DOS GUARARAPES',
    'J GRARARAPES': 'JABOATAO DOS GUARARAPES',
    'JAB GRARARAPES': 'JABOATAO DOS GUARARAPES',
    'S LOURENCO MATA': 'SAO LOURENCO DA MATA',
    'VIT STO ANTAO': 'VITORIA DE SANTO ANTAO',
    'STA CRUZ CAPIBARIBE': 'SANTA CRUZ DO CAPIBARIBE',
    'CABO S AGOSTINHO': 'CABO DE SANTO AGOSTINHO',
    'SAO JOSE EGITO': 'SAO JOSE DO EGITO',
    'AFOGADOS INGAZEIRA': 'AFOGADOS DA INGAZEIRA',
    'AFOGADOS DA INGAZEIRA': 'AFOGADOS DA INGAZEIRA',
}

# Cidades cujo nome no indice PJ difere do nome expandido
CIDADE_PROM_TO_PJ = {
    'JABOATAO DOS GUARARAPES': 'JABOATAO GUARARAPES',
    'CABO DE SANTO AGOSTINHO': 'CABO STO AGOSTINHO',
    'SANTA CRUZ DO CAPIBARIBE': 'STA CRUZ DO CAPIBARIBE',
}


def expandir_cidade(cidade_abrev):
    """Converte abreviacao de cidade para nome completo normalizado."""
    cidade_norm = normalizar(cidade_abrev)
    for abrev, completo in ABREVIACOES_CIDADE.items():
        if normalizar(abrev) == cidade_norm:
            return normalizar(completo)
    return cidade_norm


def parse_ua_antiga(nome):
    """
    Extrai (numero, tipo_completo, cidade_normalizada) de uma UA antiga.

    tipo_completo:
        'CRIMINAL', 'CIVEL', 'DEFESA DA CIDADANIA', '' (generico), 'CIV_DC' (especial)

    Retorna None se nao reconhecer o padrao ou for promotoria substituta.
    """
    nome_norm = normalizar(nome)
    m = re.match(r'^(\d+)PRM\s+JUS\s+(.+)$', nome_norm)
    if not m:
        return None

    numero = int(m.group(1))
    resto = m.group(2).strip()

    if resto.startswith('DEF CID '):
        return (numero, 'DEFESA DA CIDADANIA', expandir_cidade(resto[8:].strip()))
    if resto == 'DEF CID':
        return (numero, 'DEFESA DA CIDADANIA', '')
    if resto.startswith('CIV/DC '):
        return (numero, 'CIV_DC', expandir_cidade(resto[7:].strip()))
    if resto.startswith('CRIM '):
        return (numero, 'CRIMINAL', expandir_cidade(resto[5:].strip()))
    if resto.startswith('CIV '):
        return (numero, 'CIVEL', expandir_cidade(resto[4:].strip()))
    if resto.startswith('CID '):
        return (numero, 'DEFESA DA CIDADANIA', expandir_cidade(resto[4:].strip()))
    if resto.startswith('SUB DA '):
        return None  # promotoria substituta — sem correspondencia direta

    # sem tipo (generico)
    return (numero, '', expandir_cidade(resto))


def find_parent_code(codigo):
    """Retorna o codigo do parent esperado, ou None se for raiz."""
    code_str = str(codigo).zfill(12)
    suffix = code_str[6:].rstrip('0')
    if not suffix:
        return None
    return code_str[:6] + suffix[:-1].ljust(6, '0')


# ---------------------------------------------------------------------------
# Construcao dos indices
# ---------------------------------------------------------------------------

def build_indices(stdout=None):
    """
    Constrói dois dicionarios (numero, tipo, cidade) -> InfoUA:
        indice_prom : padrao GAB N PROM JUSTICA [TIPO] CIDADE
        indice_pj   : padrao GAB N PJ [TIPO] CIDADE / GAB N PJDC CIDADE / GAB N PJ CIDADE
    """
    indice_prom = {}
    indice_pj = {}

    for ua in InfoUA.objects.filter(codigo__isnull=False):
        nome_norm = normalizar(ua.ua)

        # --- GAB N PROM JUSTICA [TIPO] CIDADE ---
        m = re.match(
            r'^GAB\s+(\d+)\s+PROM\s+JUSTICA\s*'
            r'(CRIMINAL|CIVEL|CIVIL|DEFESA DA CIDADANIA|DEFESA CIDADANIA)?\s*(.+)$',
            nome_norm,
        )
        if m:
            numero = int(m.group(1))
            tipo = (m.group(2) or '').strip()
            cidade = m.group(3).strip()
            cidade = re.sub(r'^DE\s+', '', cidade)
            # normalizar variacoes de tipo
            if tipo == 'DEFESA CIDADANIA':
                tipo = 'DEFESA DA CIDADANIA'
            if tipo == 'CIVIL':
                tipo = 'CIVEL'
            chave = (numero, tipo, cidade)
            if chave not in indice_prom:
                indice_prom[chave] = ua
            continue

        # --- GAB N PJ CRIMINAL|CIVEL|DEFESA DA CIDADANIA [DE] CIDADE ---
        m2 = re.match(
            r'^GAB\s+(\d+)\s+PJ\s+(CRIMINAL|CIVEL|CIVIL|DEFESA DA CIDADANIA)\s+(?:DE\s+)?(.+)$',
            nome_norm,
        )
        if m2:
            numero = int(m2.group(1))
            tipo = m2.group(2).strip()
            if tipo == 'CIVIL':
                tipo = 'CIVEL'
            cidade = m2.group(3).strip()
            chave = (numero, tipo, cidade)
            if chave not in indice_pj:
                indice_pj[chave] = ua
            continue

        # --- GAB N PJDC [DE] CIDADE ---
        m3 = re.match(r'^GAB\s+(\d+)\s+PJDC\s+(?:DE\s+)?(.+)$', nome_norm)
        if m3:
            numero = int(m3.group(1))
            cidade = m3.group(2).strip()
            chave = (numero, 'DEFESA DA CIDADANIA', cidade)
            if chave not in indice_pj:
                indice_pj[chave] = ua
            continue

        # --- GAB N PJ CIDADE (sem tipo, generico) ---
        m4 = re.match(r'^GAB\s+(\d+)\s+PJ\s+(?:DE\s+)?(.+)$', nome_norm)
        if m4:
            numero = int(m4.group(1))
            cidade = m4.group(2).strip()
            chave = (numero, '', cidade)
            if chave not in indice_pj:
                indice_pj[chave] = ua
            continue

        # --- GAB N PJCR CIDADE (criminal compacto) ---
        m5 = re.match(r'^GAB\s+(\d+)\s+PJCR\s+(?:DE\s+)?(.+)$', nome_norm)
        if m5:
            numero = int(m5.group(1))
            cidade = m5.group(2).strip()
            chave = (numero, 'CRIMINAL', cidade)
            if chave not in indice_pj:
                indice_pj[chave] = ua
            continue

        # --- GAB N PJCV CIDADE (civel compacto) ---
        m6 = re.match(r'^GAB\s+(\d+)\s+PJCV\s+(?:DE\s+)?(.+)$', nome_norm)
        if m6:
            numero = int(m6.group(1))
            cidade = m6.group(2).strip()
            chave = (numero, 'CIVEL', cidade)
            if chave not in indice_pj:
                indice_pj[chave] = ua

    if stdout:
        stdout.write(f'Indice PROM: {len(indice_prom)} entradas')
        stdout.write(f'Indice PJ:   {len(indice_pj)} entradas')

    return indice_prom, indice_pj


# ---------------------------------------------------------------------------
# Match
# ---------------------------------------------------------------------------

def find_matches(indice_prom, indice_pj, stdout=None):
    """
    Retorna (matches, sem_match, colisoes_reais).

    matches         : lista de (old_ua, planilha_ua)
    sem_match       : lista de (old_ua, motivo_str)
    colisoes_reais  : dict planilha_id -> [old_ua, ...]  (len > 1)
    """
    old_uas = list(
        InfoUA.objects.filter(
            codigo__isnull=True,
            ua__iregex=r'^\d+PRM\s+JUS',
        ).order_by('id')
    )

    matches = []
    sem_match = []
    planilha_to_olds = {}

    for old_ua in old_uas:
        parsed = parse_ua_antiga(old_ua.ua)
        if parsed is None:
            sem_match.append((old_ua, 'nao parseaval (SUB ou padrao desconhecido)'))
            continue

        numero, tipo_completo, cidade = parsed

        def buscar(tipo_busca, cidade_busca):
            """Busca nos dois indices (PROM primeiro, depois PJ)."""
            k = (numero, tipo_busca, cidade_busca)
            if k in indice_prom:
                return indice_prom[k]
            # Tentar cidade no formato PJ (pode ser diferente)
            cidade_pj = CIDADE_PROM_TO_PJ.get(cidade_busca, cidade_busca)
            k2 = (numero, tipo_busca, cidade_pj)
            if k2 in indice_pj:
                return indice_pj[k2]
            return None

        found = None
        if tipo_completo == 'CIV_DC':
            for t in ['CIVEL', 'DEFESA DA CIDADANIA']:
                found = buscar(t, cidade)
                if found:
                    break
        else:
            found = buscar(tipo_completo, cidade)

        if found:
            matches.append((old_ua, found))
            pid = found.id
            planilha_to_olds.setdefault(pid, []).append(old_ua)
        else:
            sem_match.append(
                (old_ua, f'chave nao encontrada: ({numero}, {tipo_completo!r}, {cidade!r})')
            )

    colisoes_reais = {pid: olds for pid, olds in planilha_to_olds.items() if len(olds) > 1}

    return matches, sem_match, colisoes_reais


# ---------------------------------------------------------------------------
# Mescla
# ---------------------------------------------------------------------------

def apply_merge(matches, colisoes_set, stdout):
    """Aplica a mescla para cada match valido. Retorna (aplicados, erros)."""
    aplicados = 0
    erros = []

    for old_ua, planilha_ua in matches:
        if old_ua.id in colisoes_set:
            continue

        try:
            with transaction.atomic():
                old_id = old_ua.id
                planilha_id = planilha_ua.id
                codigo = planilha_ua.codigo
                sigla = planilha_ua.sigla
                nivel = planilha_ua.nivel

                # 1. Reparenta filhos da planilha_ua para old_ua
                InfoUA.objects.filter(parent_id=planilha_id).update(parent_id=old_id)

                # 2. Zera codigo da planilha_ua (libera unique constraint)
                InfoUA.objects.filter(pk=planilha_id).update(codigo=None)

                # 3. Atualiza old_ua com dados da planilha
                InfoUA.objects.filter(pk=old_id).update(
                    codigo=codigo,
                    sigla=sigla,
                    nivel=nivel,
                )

                # 4. Deleta planilha_ua
                InfoUA.objects.filter(pk=planilha_id).delete()

                # 5. Ajusta parent do old_ua pelo codigo
                parent_code = find_parent_code(codigo)
                if parent_code:
                    try:
                        parent_ua = InfoUA.objects.get(codigo=parent_code)
                        InfoUA.objects.filter(pk=old_id).update(parent_id=parent_ua.id)
                    except InfoUA.DoesNotExist:
                        pass  # parent ainda nao importado

                aplicados += 1

        except Exception as exc:
            erros.append((old_ua, planilha_ua, str(exc)))
            stdout.write(
                f'  ERRO ao mesclar id={old_ua.id} ({old_ua.ua!r}) '
                f'<- id={planilha_ua.id} ({planilha_ua.ua!r}): {exc}'
            )

    return aplicados, erros


# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------

class Command(BaseCommand):
    help = 'Mescla UAs antigas (sem codigo) com UAs importadas da planilha (com codigo)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            default=False,
            help='Aplica as mesclas. Sem esta flag, apenas simula (dry-run).',
        )
        parser.add_argument(
            '--verbose-sem-match',
            action='store_true',
            default=False,
            help='Exibe todos os registros sem match.',
        )

    def handle(self, *args, **options):
        apply = options['apply']
        verbose_sem_match = options['verbose_sem_match']

        self.stdout.write('=== Mescla de UAs Antigas ===')
        self.stdout.write(f'Modo: {"APLICAR" if apply else "DRY-RUN (use --apply para aplicar)"}')
        self.stdout.write('')

        # 1. Construir indices
        indice_prom, indice_pj = build_indices(stdout=self.stdout)

        # 2. Fazer match
        matches, sem_match, colisoes_reais = find_matches(indice_prom, indice_pj, stdout=self.stdout)

        self.stdout.write(f'Matches encontrados: {len(matches)}')
        self.stdout.write(f'Sem match: {len(sem_match)}')
        self.stdout.write(
            f'Colisoes (planilha_ua apontada por multiplas old_uas): {len(colisoes_reais)}'
        )

        # Detalhar colisoes
        if colisoes_reais:
            self.stdout.write('\nDetalhes das colisoes:')
            for pid, olds in colisoes_reais.items():
                planilha_ua = InfoUA.objects.get(pk=pid)
                self.stdout.write(f'  planilha: id={pid} ua={planilha_ua.ua!r}')
                for o in olds:
                    self.stdout.write(f'    -> old: id={o.id} ua={o.ua!r}')

        # Detalhar sem match
        if verbose_sem_match:
            self.stdout.write('\nSem match (todos):')
            for old_ua, motivo in sem_match:
                self.stdout.write(f'  id={old_ua.id} ua={old_ua.ua!r}  [{motivo}]')
        else:
            self.stdout.write(f'\nPrimeiros 30 sem match:')
            for old_ua, motivo in sem_match[:30]:
                self.stdout.write(f'  id={old_ua.id} ua={old_ua.ua!r}  [{motivo}]')

        # Calcular matches validos
        colisoes_set = set()
        for pid, olds in colisoes_reais.items():
            for o in olds:
                colisoes_set.add(o.id)

        matches_validos = [(o, p) for o, p in matches if o.id not in colisoes_set]
        matches_colisao = [(o, p) for o, p in matches if o.id in colisoes_set]

        self.stdout.write(f'\nMatches validos para mescla: {len(matches_validos)}')
        self.stdout.write(f'Matches pulados por colisao: {len(matches_colisao)}')

        if not apply:
            self.stdout.write(
                '\n[DRY-RUN] Nenhuma alteracao foi feita. Use --apply para aplicar.'
            )
            sem_codigo_atual = InfoUA.objects.filter(codigo__isnull=True).count()
            self.stdout.write(f'UAs sem codigo atualmente: {sem_codigo_atual}')
            return

        # 3. Aplicar mescla
        self.stdout.write('\nAplicando mesclas...')
        aplicados, erros = apply_merge(matches_validos, colisoes_set, self.stdout)

        # 4. Resultado final
        self.stdout.write('\n=== RESULTADO FINAL ===')
        self.stdout.write(f'Mesclas aplicadas: {aplicados}')
        self.stdout.write(f'Colisoes detectadas e ignoradas: {len(matches_colisao)}')
        self.stdout.write(f'Erros durante mescla: {len(erros)}')

        sem_codigo_final = InfoUA.objects.filter(codigo__isnull=True).count()
        self.stdout.write(f'UAs sem codigo apos mescla: {sem_codigo_final}')
