import json
import re
import unicodedata
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from dempam.models import InfoUA, Municipio


def normalizar(texto):
    """Maiúsculas, sem acento, espaços colapsados — pra comparar nomes com segurança."""
    sem_acento = unicodedata.normalize('NFKD', texto or '').encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'\s+', ' ', sem_acento).strip().upper()


class Command(BaseCommand):
    help = (
        'Cadastra os municípios de Pernambuco (a partir de static/data/pe_municipios.geojson) '
        'e associa automaticamente as UAs cujo nome contém o nome do município.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostra o que seria feito, sem salvar nada.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        modo = '[DRY-RUN] ' if dry_run else ''

        geojson_path = Path(settings.BASE_DIR) / 'static' / 'data' / 'pe_municipios.geojson'
        with open(geojson_path, encoding='utf-8') as f:
            geo = json.load(f)

        # --- 1. Cadastra os municípios (get_or_create real, mesmo em dry-run,
        #        senão a comparação abaixo não tem contra o que comparar) ---
        criados = 0
        municipios_por_codigo = {}
        for feature in geo['features']:
            nome = feature['properties']['nome']
            codigo_ibge = feature['properties']['codigo_ibge']

            existente = Municipio.objects.filter(codigo_ibge=codigo_ibge).first()
            if existente:
                municipios_por_codigo[codigo_ibge] = existente
                continue

            criados += 1
            if dry_run:
                # objeto não salvo, só pra ter nome/código disponíveis na comparação
                municipios_por_codigo[codigo_ibge] = Municipio(nome=nome, codigo_ibge=codigo_ibge)
            else:
                municipios_por_codigo[codigo_ibge] = Municipio.objects.create(nome=nome, codigo_ibge=codigo_ibge)

        self.stdout.write(f'{modo}{criados} município(s) novo(s) cadastrado(s).')

        # --- 2. Associa as UAs cujo nome contém o nome do município ---
        municipios_norm = [(m, normalizar(m.nome)) for m in municipios_por_codigo.values()]

        uas_sem_municipio = list(InfoUA.objects.filter(municipio__isnull=True).order_by('ua'))

        associadas = 0
        ambiguas = []

        for ua in uas_sem_municipio:
            ua_norm = normalizar(ua.ua)
            encontrados = [
                m for m, nome_norm in municipios_norm
                if nome_norm and re.search(r'\b' + re.escape(nome_norm) + r'\b', ua_norm)
            ]

            if len(encontrados) == 1:
                municipio = encontrados[0]
                self.stdout.write(f'  {ua.ua!r}  ->  {municipio.nome}')
                if not dry_run:
                    ua.municipio = municipio
                    ua.save(update_fields=['municipio'])
                associadas += 1
            elif len(encontrados) > 1:
                ambiguas.append((ua, encontrados))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'{modo}{associadas} UA(s) associada(s) por nome.'))

        restantes = len(uas_sem_municipio) - associadas
        self.stdout.write(f'{modo}{restantes} UA(s) sem município seguem para associação manual.')

        if ambiguas:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING(f'{len(ambiguas)} UA(s) bateram com mais de um município (não associadas):'))
            for ua, encontrados in ambiguas:
                nomes = ', '.join(m.nome for m in encontrados)
                self.stdout.write(f'  {ua.ua!r}  ->  {nomes}')
