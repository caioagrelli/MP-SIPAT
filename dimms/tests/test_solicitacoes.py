from django.test import TestCase, Client
from django.urls import reverse

from dimms.models import Solicitacao
from .helpers import make_user, make_ua, make_solicitacao


# ══════════════════════════════════════════════════════════════════════════════
# Minhas Solicitações de Consumo
# ══════════════════════════════════════════════════════════════════════════════

class MinhasSolicitacoesConsumoViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.ua = make_ua()
        self.url = reverse('dimms:minhas_solicitacoes_consumo')

    def test_redireciona_sem_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_exibe_apenas_solicitacoes_do_usuario(self):
        outro = make_user('outro')
        make_solicitacao(self.user, self.ua)
        make_solicitacao(outro, self.ua)
        self.client.login(username='usuario', password='senha123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['solicitacoes'].count(), 1)


# ══════════════════════════════════════════════════════════════════════════════
# Painel de Aprovações
# ══════════════════════════════════════════════════════════════════════════════

class PainelSolicitacoesConsumoViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user_comum = make_user('comum')
        self.user_admin = make_user('gestor', perms=['change_catalogoconsumo'])
        self.ua = make_ua()
        self.url = reverse('dimms:painel_solicitacoes_consumo')

    def test_nega_sem_permissao(self):
        self.client.login(username='comum', password='senha123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_acessivel_com_permissao(self):
        self.client.login(username='gestor', password='senha123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_filtro_status_pendente_por_padrao(self):
        make_solicitacao(self.user_comum, self.ua, status='PENDENTE')
        make_solicitacao(self.user_comum, self.ua, status='ATENDIDA')
        self.client.login(username='gestor', password='senha123')
        response = self.client.get(self.url)
        self.assertEqual(response.context['solicitacoes'].count(), 1)


# ══════════════════════════════════════════════════════════════════════════════
# Analisar Solicitação (atender / rejeitar)
# ══════════════════════════════════════════════════════════════════════════════

class AnalisarSolicitacaoConsumoViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.solicitante = make_user('solicitante')
        self.gestor = make_user('gestor', perms=['change_catalogoconsumo'])
        self.ua = make_ua()

    def _url(self, sol):
        return reverse('dimms:analisar_solicitacao_consumo', args=[sol.pk])

    def test_atender_muda_status_para_atendida(self):
        sol = make_solicitacao(self.solicitante, self.ua, status='PENDENTE')
        self.client.login(username='gestor', password='senha123')
        self.client.post(self._url(sol), {'acao': 'atender', 'obs_decisao': ''})
        sol.refresh_from_db()
        self.assertEqual(sol.status, 'ATENDIDA')

    def test_rejeitar_muda_status_para_rejeitada(self):
        sol = make_solicitacao(self.solicitante, self.ua, status='PENDENTE')
        self.client.login(username='gestor', password='senha123')
        self.client.post(self._url(sol), {'acao': 'rejeitar', 'obs_decisao': 'Sem estoque'})
        sol.refresh_from_db()
        self.assertEqual(sol.status, 'REJEITADA')

    def test_atender_registra_decidido_por(self):
        sol = make_solicitacao(self.solicitante, self.ua, status='PENDENTE')
        self.client.login(username='gestor', password='senha123')
        self.client.post(self._url(sol), {'acao': 'atender', 'obs_decisao': ''})
        sol.refresh_from_db()
        self.assertEqual(sol.decidido_por, self.gestor)

    def test_nao_pode_atender_solicitacao_ja_atendida(self):
        sol = make_solicitacao(self.solicitante, self.ua, status='ATENDIDA')
        self.client.login(username='gestor', password='senha123')
        self.client.post(self._url(sol), {'acao': 'atender', 'obs_decisao': ''})
        sol.refresh_from_db()
        self.assertEqual(sol.status, 'ATENDIDA')

    def test_nega_sem_permissao(self):
        sol = make_solicitacao(self.solicitante, self.ua)
        self.client.login(username='solicitante', password='senha123')
        response = self.client.get(self._url(sol))
        self.assertEqual(response.status_code, 403)

    def test_pk_inexistente_retorna_404(self):
        self.client.login(username='gestor', password='senha123')
        response = self.client.get(reverse('dimms:analisar_solicitacao_consumo', args=[9999]))
        self.assertEqual(response.status_code, 404)


# ══════════════════════════════════════════════════════════════════════════════
# Processing (Solicitações de estoque / SBC)
# ══════════════════════════════════════════════════════════════════════════════

class ProcessingViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user()

    def test_redireciona_sem_login(self):
        response = self.client.get(reverse('dimms:processing'))
        self.assertEqual(response.status_code, 302)

    def test_acessivel_com_login(self):
        self.client.login(username='usuario', password='senha123')
        response = self.client.get(reverse('dimms:processing'))
        self.assertEqual(response.status_code, 200)

    def test_filtro_status(self):
        self.client.login(username='usuario', password='senha123')
        Solicitacao.objects.create(situation='ATENDIMENTO')
        Solicitacao.objects.create(situation='CANCELADA')
        response = self.client.get(reverse('dimms:processing'), {'status': 'ATENDIMENTO'})
        self.assertEqual(response.context['tramitacoes'].count(), 1)
