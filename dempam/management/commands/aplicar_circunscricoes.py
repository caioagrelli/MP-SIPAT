"""
Aplica a divisão oficial das 14 Circunscrições do MPPE (+ Capital) aos
municípios já cadastrados, pra alimentar o filtro de circunscrição do mapa
do Painel Gerencial.

Fonte: composição confirmada pelo próprio MPPE (publicações institucionais
por circunscrição), conforme fornecida manualmente.

Uso:
    python manage.py aplicar_circunscricoes
"""
import re
import unicodedata

from django.core.management.base import BaseCommand

from dempam.models import Municipio


def _normalizar(texto):
    sem_acento = unicodedata.normalize('NFKD', texto or '').encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'\s+', ' ', sem_acento).strip().lower()


# Nomes da planilha oficial que não batem letra-por-letra com o cadastro
# (nome_oficial_do_usuario -> nome_no_cadastro)
_ALIASES = {
    'sao caetano': 'sao caitano',
    'itamaraca': 'ilha de itamaraca',
    'belem de sao francisco': 'belem do sao francisco',
}

CIRCUNSCRICOES = {
    ('1', 'Salgueiro'): [
        'Araripina', 'Bodocó', 'Cedro', 'Exu', 'Granito', 'Ipubi', 'Moreilândia',
        'Ouricuri', 'Parnamirim', 'Salgueiro', 'Santa Cruz', 'Santa Filomena',
        'Serrita', 'Terra Nova', 'Trindade', 'Verdejante',
    ],
    ('2', 'Petrolina'): [
        'Afrânio', 'Cabrobó', 'Dormentes', 'Lagoa Grande', 'Orocó', 'Petrolina',
        'Santa Maria da Boa Vista',
    ],
    ('3', 'Afogados da Ingazeira'): [
        'Afogados da Ingazeira', 'Brejinho', 'Carnaíba', 'Iguaracy', 'Ingazeira',
        'Itapetim', 'Quixaba', 'Santa Terezinha', 'São José do Egito', 'Sertânia',
        'Solidão', 'Tabira', 'Tuparetama',
    ],
    ('4', 'Arcoverde'): [
        'Alagoinha', 'Arcoverde', 'Belo Jardim', 'Buíque', 'Ibimirim', 'Inajá',
        'Manari', 'Pedra', 'Pesqueira', 'Poção', 'Sanharó', 'São Bento do Una',
        'Tupanatinga', 'Venturosa',
    ],
    ('5', 'Garanhuns'): [
        'Águas Belas', 'Angelim', 'Bom Conselho', 'Brejão', 'Caetés', 'Calçado',
        'Canhotinho', 'Capoeiras', 'Correntes', 'Garanhuns', 'Iati', 'Itaíba',
        'Jucati', 'Jupi', 'Jurema', 'Lagoa do Ouro', 'Lajedo', 'Palmeirina',
        'Paranatama', 'Saloá', 'São João', 'Terezinha',
    ],
    ('6', 'Caruaru'): [
        'Agrestina', 'Altinho', 'Bezerros', 'Brejo da Madre de Deus', 'Cachoeirinha',
        'Camocim de São Félix', 'Caruaru', 'Cupira', 'Ibirajuba', 'Jataúba',
        'Panelas', 'Riacho das Almas', 'Sairé', 'Santa Cruz do Capibaribe',
        'São Caetano', 'Tacaimbó', 'Taquaritinga do Norte', 'Toritama',
    ],
    ('7', 'Palmares'): [
        'Água Preta', 'Belém de Maria', 'Catende', 'Jaqueira', 'Joaquim Nabuco',
        'Lagoa dos Gatos', 'Maraial', 'Palmares', 'Quipapá', 'São Benedito do Sul',
        'Xexéu',
    ],
    ('8', 'Cabo de Santo Agostinho'): [
        'Amaraji', 'Barreiros', 'Cabo de Santo Agostinho', 'Cortês', 'Escada',
        'Gameleira', 'Ipojuca', 'Primavera', 'Ribeirão', 'Rio Formoso',
        'São José da Coroa Grande', 'Sirinhaém', 'Tamandaré',
    ],
    ('9', 'Olinda'): [
        'Abreu e Lima', 'Araçoiaba', 'Goiana', 'Igarassu', 'Itamaracá',
        'Itapissuma', 'Olinda', 'Paulista',
    ],
    ('10', 'Nazaré da Mata'): [
        'Aliança', 'Buenos Aires', 'Camutanga', 'Condado', 'Ferreiros', 'Itambé',
        'Itaquitinga', 'Macaparana', 'Nazaré da Mata', 'São Vicente Férrer',
        'Timbaúba', 'Tracunhaém', 'Vicência',
    ],
    ('11', 'Limoeiro'): [
        'Bom Jardim', 'Carpina', 'Casinhas', 'Cumaru', 'Feira Nova', 'Frei Miguelinho',
        'João Alfredo', 'Lagoa do Carro', 'Lagoa de Itaenga', 'Limoeiro', 'Machados',
        'Orobó', 'Passira', 'Paudalho', 'Salgadinho', 'Santa Maria do Cambucá',
        'Surubim', 'Vertente do Lério', 'Vertentes',
    ],
    ('12', 'Vitória de Santo Antão'): [
        'Barra de Guabiraba', 'Bonito', 'Chã de Alegria', 'Chã Grande',
        'Glória do Goitá', 'Gravatá', 'Moreno', 'Pombos', 'São Joaquim do Monte',
        'Vitória de Santo Antão',
    ],
    ('13', 'Jaboatão dos Guararapes'): [
        'Camaragibe', 'Jaboatão dos Guararapes', 'São Lourenço da Mata',
    ],
    ('14', 'Serra Talhada'): [
        'Belém de São Francisco', 'Betânia', 'Calumbi', 'Carnaubeira da Penha',
        'Custódia', 'Flores', 'Floresta', 'Itacuruba', 'Jatobá', 'Mirandiba',
        'Petrolândia', 'Santa Cruz da Baixa Verde', 'São José do Belmonte',
        'Serra Talhada', 'Tacaratu', 'Triunfo',
    ],
}

CAPITAL = ['Recife', 'Fernando de Noronha']


class Command(BaseCommand):
    help = 'Aplica a divisão oficial das 14 Circunscrições do MPPE (+ Capital) aos municípios cadastrados'

    def handle(self, *args, **options):
        municipios_por_norm = {_normalizar(m.nome): m for m in Municipio.objects.all()}

        atualizados = 0
        nao_encontrados = []

        def aplicar(nome_usuario, label):
            nonlocal atualizados
            chave = _normalizar(nome_usuario)
            chave = _ALIASES.get(chave, chave)
            municipio = municipios_por_norm.get(chave)
            if not municipio:
                nao_encontrados.append((label, nome_usuario))
                return
            if municipio.circunscricao != label:
                municipio.circunscricao = label
                municipio.save(update_fields=['circunscricao'])
            atualizados += 1

        for (numero, sede), nomes in CIRCUNSCRICOES.items():
            label = f'{numero}ª Circunscrição ({sede})'
            for nome in nomes:
                aplicar(nome, label)

        for nome in CAPITAL:
            aplicar(nome, 'Capital')

        total_municipios = Municipio.objects.count()
        self.stdout.write(self.style.SUCCESS(f'[OK] Municípios classificados: {atualizados} / {total_municipios}'))

        sem_circunscricao = Municipio.objects.filter(circunscricao='').order_by('nome')
        if sem_circunscricao.exists():
            self.stdout.write(self.style.WARNING(f'[--] Municípios sem circunscrição definida: {sem_circunscricao.count()}'))
            for m in sem_circunscricao:
                self.stdout.write(f'  {m.nome}')

        if nao_encontrados:
            self.stdout.write(self.style.ERROR(f'[XX] Nomes que não bateram com o cadastro: {len(nao_encontrados)}'))
            for label, nome in nao_encontrados:
                self.stdout.write(f'  [{label}] {nome!r}')
