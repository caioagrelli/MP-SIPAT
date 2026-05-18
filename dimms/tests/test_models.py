from django.test import TestCase
from django.utils import timezone

from dimms.models import (
    CatalogoConsumo,
    SolicitacaoCatalogoConsumo,
    ItemSolicitacaoCatalogoConsumo,
    Solicitacao,
)
from .helpers import make_user, make_ua, make_catalogo, make_solicitacao


# ══════════════════════════════════════════════════════════════════════════════
# CatalogoConsumo
# ══════════════════════════════════════════════════════════════════════════════

class CatalogoConsumoModelTest(TestCase):

    def test_str_retorna_descricao(self):
        item = make_catalogo('Caneta Azul')
        self.assertEqual(str(item), 'Caneta Azul')

    def test_ativo_por_padrao(self):
        item = CatalogoConsumo.objects.create(
            description='Item Novo',
            grupo_consumo='LIMPEZA',
        )
        self.assertTrue(item.ativo)

    def test_ordenacao_por_grupo_e_descricao(self):
        make_catalogo('Zebra', 'LIMPEZA')
        make_catalogo('Alfa', 'LIMPEZA')
        make_catalogo('Caneta', 'PAPEIS_EXPEDIENTE')
        itens = list(CatalogoConsumo.objects.values_list('description', flat=True))
        self.assertEqual(itens, ['Alfa', 'Zebra', 'Caneta'])

    def test_item_inativo_nao_aparece_no_filtro_ativo(self):
        make_catalogo('Ativo', ativo=True)
        make_catalogo('Inativo', ativo=False)
        self.assertEqual(CatalogoConsumo.objects.filter(ativo=True).count(), 1)


# ══════════════════════════════════════════════════════════════════════════════
# SolicitacaoCatalogoConsumo
# ══════════════════════════════════════════════════════════════════════════════

class SolicitacaoCatalogoConsumoModelTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.ua = make_ua()

    def test_codigo_gerado_automaticamente(self):
        sol = make_solicitacao(self.user, self.ua)
        self.assertTrue(sol.codigo.startswith('SCC-'))

    def test_codigo_formato_correto(self):
        sol = make_solicitacao(self.user, self.ua)
        ano = timezone.now().year
        self.assertRegex(sol.codigo, rf'SCC-{ano}-\d{{4}}')

    def test_codigos_sequenciais(self):
        sol1 = make_solicitacao(self.user, self.ua)
        sol2 = make_solicitacao(self.user, self.ua)
        num1 = int(sol1.codigo.split('-')[-1])
        num2 = int(sol2.codigo.split('-')[-1])
        self.assertEqual(num2, num1 + 1)

    def test_status_padrao_pendente(self):
        sol = SolicitacaoCatalogoConsumo.objects.create(
            solicitante=self.user,
            ua_destino=self.ua,
        )
        self.assertEqual(sol.status, 'PENDENTE')

    def test_total_itens_property(self):
        sol = make_solicitacao(self.user, self.ua)
        item = make_catalogo()
        ItemSolicitacaoCatalogoConsumo.objects.create(solicitacao=sol, catalogo=item, quantidade=2)
        ItemSolicitacaoCatalogoConsumo.objects.create(solicitacao=sol, catalogo=item, quantidade=1)
        self.assertEqual(sol.total_itens, 2)

    def test_str_retorna_codigo(self):
        sol = make_solicitacao(self.user, self.ua)
        self.assertEqual(str(sol), sol.codigo)


# ══════════════════════════════════════════════════════════════════════════════
# Solicitacao (processing / SBC)
# ══════════════════════════════════════════════════════════════════════════════

class SolicitacaoModelTest(TestCase):

    def test_codigo_sbc_gerado_automaticamente(self):
        sol = Solicitacao.objects.create(situation='RASCUNHO')
        self.assertTrue(sol.request_code.startswith('SBC-'))

    def test_codigo_sbc_formato_correto(self):
        sol = Solicitacao.objects.create(situation='RASCUNHO')
        ano = timezone.now().year
        self.assertRegex(sol.request_code, rf'SBC-{ano}-\d{{4}}')

    def test_codigos_sbc_sequenciais(self):
        sol1 = Solicitacao.objects.create(situation='RASCUNHO')
        sol2 = Solicitacao.objects.create(situation='RASCUNHO')
        num1 = int(sol1.request_code.split('-')[-1])
        num2 = int(sol2.request_code.split('-')[-1])
        self.assertEqual(num2, num1 + 1)
