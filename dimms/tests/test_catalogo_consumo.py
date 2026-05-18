from django.test import TestCase, Client
from django.urls import reverse

from dimms.models import CatalogoConsumo
from .helpers import make_user, make_ua, make_catalogo, make_solicitacao


# ══════════════════════════════════════════════════════════════════════════════
# Lista pública
# ══════════════════════════════════════════════════════════════════════════════

class CatalogoConsumoListaViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.url = reverse('dimms:catalogo_consumo')

    def test_redireciona_sem_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response['Location'])

    def test_acessivel_com_login(self):
        self.client.login(username='usuario', password='senha123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_exibe_apenas_itens_ativos(self):
        make_catalogo('Ativo', ativo=True)
        make_catalogo('Inativo', ativo=False)
        self.client.login(username='usuario', password='senha123')
        response = self.client.get(self.url)
        self.assertContains(response, 'Ativo')
        self.assertNotContains(response, 'Inativo')

    def test_filtro_por_descricao(self):
        make_catalogo('Papel A4')
        make_catalogo('Caneta Azul')
        self.client.login(username='usuario', password='senha123')
        response = self.client.get(self.url, {'q': 'Papel'})
        self.assertContains(response, 'Papel A4')
        self.assertNotContains(response, 'Caneta Azul')

    def test_filtro_por_grupo(self):
        make_catalogo('Item Limpeza', grupo='LIMPEZA')
        make_catalogo('Item Papel', grupo='PAPEIS_EXPEDIENTE')
        self.client.login(username='usuario', password='senha123')
        response = self.client.get(self.url, {'grupo': 'LIMPEZA'})
        self.assertContains(response, 'Item Limpeza')
        self.assertNotContains(response, 'Item Papel')


# ══════════════════════════════════════════════════════════════════════════════
# Admin CRUD
# ══════════════════════════════════════════════════════════════════════════════

class CatalogoConsumoAdminViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user_comum = make_user('comum')
        self.user_admin = make_user('admin', perms=[
            'add_catalogoconsumo',
            'change_catalogoconsumo',
            'delete_catalogoconsumo',
        ])

    # ── Lista ─────────────────────────────────────────────────────────────────

    def test_lista_redireciona_sem_login(self):
        response = self.client.get(reverse('dimms:catalogo_consumo_admin'))
        self.assertEqual(response.status_code, 302)

    def test_lista_nega_sem_permissao(self):
        self.client.login(username='comum', password='senha123')
        response = self.client.get(reverse('dimms:catalogo_consumo_admin'))
        self.assertEqual(response.status_code, 403)

    def test_lista_acessivel_com_permissao(self):
        self.client.login(username='admin', password='senha123')
        response = self.client.get(reverse('dimms:catalogo_consumo_admin'))
        self.assertEqual(response.status_code, 200)

    # ── Criar ─────────────────────────────────────────────────────────────────

    def test_criar_get_retorna_200(self):
        self.client.login(username='admin', password='senha123')
        response = self.client.get(reverse('dimms:catalogo_consumo_criar'))
        self.assertEqual(response.status_code, 200)

    def test_criar_post_valido_cria_item(self):
        self.client.login(username='admin', password='senha123')
        self.client.post(reverse('dimms:catalogo_consumo_criar'), {
            'description': 'Caneta Bic',
            'grupo_consumo': 'PAPEIS_EXPEDIENTE',
            'medida': 'UNIDADE',
            'ativo': 'on',
        })
        self.assertTrue(CatalogoConsumo.objects.filter(description='Caneta Bic').exists())

    def test_criar_post_valido_redireciona(self):
        self.client.login(username='admin', password='senha123')
        response = self.client.post(reverse('dimms:catalogo_consumo_criar'), {
            'description': 'Caneta Bic',
            'grupo_consumo': 'PAPEIS_EXPEDIENTE',
            'medida': 'UNIDADE',
            'ativo': 'on',
        })
        self.assertRedirects(response, reverse('dimms:catalogo_consumo_admin'))

    def test_criar_sem_descricao_nao_salva(self):
        self.client.login(username='admin', password='senha123')
        self.client.post(reverse('dimms:catalogo_consumo_criar'), {
            'grupo_consumo': 'LIMPEZA',
            'medida': 'UNIDADE',
        })
        self.assertEqual(CatalogoConsumo.objects.count(), 0)

    def test_criar_sem_grupo_nao_salva(self):
        self.client.login(username='admin', password='senha123')
        self.client.post(reverse('dimms:catalogo_consumo_criar'), {
            'description': 'Sem Grupo',
            'medida': 'UNIDADE',
        })
        self.assertEqual(CatalogoConsumo.objects.count(), 0)

    def test_criar_nega_sem_permissao(self):
        self.client.login(username='comum', password='senha123')
        response = self.client.get(reverse('dimms:catalogo_consumo_criar'))
        self.assertEqual(response.status_code, 403)

    # ── Editar ────────────────────────────────────────────────────────────────

    def test_editar_get_retorna_200(self):
        item = make_catalogo()
        self.client.login(username='admin', password='senha123')
        response = self.client.get(reverse('dimms:catalogo_consumo_editar', args=[item.pk]))
        self.assertEqual(response.status_code, 200)

    def test_editar_post_atualiza_item(self):
        item = make_catalogo('Antes')
        self.client.login(username='admin', password='senha123')
        self.client.post(reverse('dimms:catalogo_consumo_editar', args=[item.pk]), {
            'description': 'Depois',
            'grupo_consumo': 'LIMPEZA',
            'medida': 'UNIDADE',
            'ativo': 'on',
        })
        item.refresh_from_db()
        self.assertEqual(item.description, 'Depois')

    def test_editar_pk_inexistente_retorna_404(self):
        self.client.login(username='admin', password='senha123')
        response = self.client.get(reverse('dimms:catalogo_consumo_editar', args=[9999]))
        self.assertEqual(response.status_code, 404)

    # ── Excluir ───────────────────────────────────────────────────────────────

    def test_excluir_get_retorna_200(self):
        item = make_catalogo()
        self.client.login(username='admin', password='senha123')
        response = self.client.get(reverse('dimms:catalogo_consumo_excluir', args=[item.pk]))
        self.assertEqual(response.status_code, 200)

    def test_excluir_post_remove_item(self):
        item = make_catalogo()
        self.client.login(username='admin', password='senha123')
        self.client.post(reverse('dimms:catalogo_consumo_excluir', args=[item.pk]))
        self.assertFalse(CatalogoConsumo.objects.filter(pk=item.pk).exists())

    def test_excluir_nega_sem_permissao(self):
        item = make_catalogo()
        self.client.login(username='comum', password='senha123')
        response = self.client.post(reverse('dimms:catalogo_consumo_excluir', args=[item.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(CatalogoConsumo.objects.filter(pk=item.pk).exists())
