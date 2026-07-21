from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import Feedback, StatusFeedback


class FeedbackCodigoTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('joao', password='x')

    def test_codigo_gerado_automaticamente(self):
        fb = Feedback.objects.create(user=self.user, tipo='bug', descricao='algo quebrado')
        self.assertRegex(fb.codigo, r'^RBS-\d{4}-\d{4}$')

    def test_codigo_sequencial(self):
        fb1 = Feedback.objects.create(user=self.user, tipo='bug', descricao='um')
        fb2 = Feedback.objects.create(user=self.user, tipo='sugestao', descricao='dois')
        num1 = int(fb1.codigo.rsplit('-', 1)[1])
        num2 = int(fb2.codigo.rsplit('-', 1)[1])
        self.assertEqual(num2, num1 + 1)

    def test_codigo_nao_e_regenerado_ao_salvar_de_novo(self):
        fb = Feedback.objects.create(user=self.user, tipo='bug', descricao='algo')
        codigo_original = fb.codigo
        fb.status = StatusFeedback.finalizado
        fb.save(update_fields=['status'])
        fb.refresh_from_db()
        self.assertEqual(fb.codigo, codigo_original)

    def test_status_default_e_aberto(self):
        fb = Feedback.objects.create(user=self.user, tipo='bug', descricao='algo')
        self.assertEqual(fb.status, StatusFeedback.aberto)

    def test_labels_de_status(self):
        self.assertEqual(dict(StatusFeedback.choices)['FINALIZADO'], 'Finalizada')
        self.assertEqual(dict(StatusFeedback.choices)['RECUSADO'], 'Recusada')
        self.assertEqual(dict(StatusFeedback.choices)['EM_ANDAMENTO'], 'Em Andamento')


class FeedbackListaViewTests(TestCase):
    def setUp(self):
        self.gerente = User.objects.create_user('gerente', password='x', is_staff=True)
        self.comum = User.objects.create_user('comum', password='x')
        self.fb = Feedback.objects.create(user=self.comum, tipo='bug', descricao='bug legal')

    def test_anonimo_e_redirecionado_para_login(self):
        r = self.client.get(reverse('accounts:lista_feedback'))
        self.assertEqual(r.status_code, 302)

    def test_usuario_comum_nao_acessa(self):
        self.client.force_login(self.comum)
        r = self.client.get(reverse('accounts:lista_feedback'))
        self.assertEqual(r.status_code, 403)

    def test_staff_acessa(self):
        self.client.force_login(self.gerente)
        r = self.client.get(reverse('accounts:lista_feedback'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, self.fb.codigo)

    def test_membro_grupo_gerencia_acessa(self):
        grupo, _ = Group.objects.get_or_create(name='Gerencia')
        self.comum.groups.add(grupo)
        self.client.force_login(self.comum)
        r = self.client.get(reverse('accounts:lista_feedback'))
        self.assertEqual(r.status_code, 200)

    def test_filtro_por_status(self):
        self.client.force_login(self.gerente)
        Feedback.objects.create(
            user=self.comum, tipo='bug', descricao='finalizado ja',
            status=StatusFeedback.finalizado,
        )
        r = self.client.get(reverse('accounts:lista_feedback'), {'status': 'FINALIZADO'})
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, self.fb.codigo)


class AtualizarStatusViewTests(TestCase):
    def setUp(self):
        self.gerente = User.objects.create_user('gerente2', password='x', is_staff=True)
        self.comum = User.objects.create_user('comum2', password='x')
        self.fb = Feedback.objects.create(user=self.comum, tipo='bug', descricao='algo quebrado')

    def _url(self, fb=None):
        return reverse('accounts:atualizar_status_feedback', args=[(fb or self.fb).pk])

    def test_requer_login(self):
        r = self.client.post(self._url(), {'status': 'FINALIZADO'})
        self.assertEqual(r.status_code, 302)

    def test_requer_permissao_de_gerencia(self):
        self.client.force_login(self.comum)
        r = self.client.post(self._url(), {'status': 'FINALIZADO'})
        self.assertEqual(r.status_code, 403)

    def test_requer_metodo_post(self):
        self.client.force_login(self.gerente)
        r = self.client.get(self._url())
        self.assertEqual(r.status_code, 405)

    def test_atualiza_status_com_sucesso(self):
        self.client.force_login(self.gerente)
        r = self.client.post(self._url(), {'status': 'EM_ANDAMENTO'})
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data['ok'])
        self.assertEqual(data['status'], 'EM_ANDAMENTO')
        self.assertEqual(data['label'], 'Em Andamento')
        self.fb.refresh_from_db()
        self.assertEqual(self.fb.status, StatusFeedback.em_andamento)

    def test_status_invalido_e_rejeitado(self):
        self.client.force_login(self.gerente)
        r = self.client.post(self._url(), {'status': 'NAO_EXISTE'})
        self.assertEqual(r.status_code, 400)
        self.assertFalse(r.json()['ok'])
        self.fb.refresh_from_db()
        self.assertEqual(self.fb.status, StatusFeedback.aberto)

    def test_marca_como_finalizada_com_nota_opcional(self):
        self.client.force_login(self.gerente)
        r = self.client.post(self._url(), {
            'status': 'FINALIZADO',
            'resolucao': 'Corrigido o botão que não respondia.',
        })
        data = r.json()
        self.assertTrue(data['ok'])
        self.assertEqual(data['status'], 'FINALIZADO')
        self.assertEqual(data['label'], 'Finalizada')
        self.assertEqual(data['resolucao'], 'Corrigido o botão que não respondia.')
        self.fb.refresh_from_db()
        self.assertEqual(self.fb.resolucao, 'Corrigido o botão que não respondia.')

    def test_nota_e_opcional_e_preserva_valor_anterior(self):
        self.client.force_login(self.gerente)
        self.client.post(self._url(), {'status': 'FINALIZADO', 'resolucao': 'nota original'})
        r = self.client.post(self._url(), {'status': 'EM_ANDAMENTO'})
        self.assertTrue(r.json()['ok'])
        self.fb.refresh_from_db()
        self.assertEqual(self.fb.status, StatusFeedback.em_andamento)
        self.assertEqual(self.fb.resolucao, 'nota original')

    def test_fluxo_completo_com_csrf_real_como_no_navegador(self):
        """Reproduz exatamente o que o JS faz: pega o token do cookie
        setado pelo {% csrf_token %} do base.html e manda no header."""
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.gerente)
        client.get(reverse('accounts:lista_feedback'))
        token = client.cookies['csrftoken'].value

        r = client.post(
            self._url(),
            {'status': 'FINALIZADO', 'resolucao': ''},
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()['ok'])


class ReportarFeedbackViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('reporter', password='x')

    def test_requer_login(self):
        r = self.client.post(reverse('accounts:reportar_feedback'), {
            'tipo': 'bug', 'descricao': 'algo',
        })
        self.assertEqual(r.status_code, 302)

    def test_cria_feedback_com_sucesso(self):
        self.client.force_login(self.user)
        r = self.client.post(reverse('accounts:reportar_feedback'), {
            'tipo': 'bug', 'descricao': 'botão quebrado', 'pagina': '/dimms/',
        })
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()['ok'])
        fb = Feedback.objects.get(user=self.user)
        self.assertEqual(fb.tipo, 'bug')
        self.assertTrue(fb.codigo)
        self.assertEqual(fb.status, StatusFeedback.aberto)

    def test_tipo_invalido_e_rejeitado(self):
        self.client.force_login(self.user)
        r = self.client.post(reverse('accounts:reportar_feedback'), {
            'tipo': 'lixo', 'descricao': 'algo',
        })
        self.assertEqual(r.status_code, 400)
        self.assertFalse(Feedback.objects.filter(user=self.user).exists())

    def test_descricao_vazia_e_rejeitada(self):
        self.client.force_login(self.user)
        r = self.client.post(reverse('accounts:reportar_feedback'), {
            'tipo': 'bug', 'descricao': '',
        })
        self.assertEqual(r.status_code, 400)
        self.assertFalse(Feedback.objects.filter(user=self.user).exists())
