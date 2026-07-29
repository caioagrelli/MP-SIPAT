import re

from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


def profile_photo_path(instance, filename):
    return f'profiles/{instance.user.username}/{filename}'


class Profile(models.Model):
    user  = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    photo = models.ImageField(upload_to=profile_photo_path, blank=True, null=True, verbose_name='Foto de Perfil')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Telefone')
    bio   = models.TextField(blank=True, verbose_name='Sobre mim')

    # UAs às quais o usuário pertence (pode receber atribuições)
    uas = models.ManyToManyField(
        'dempam.InfoUA',
        blank=True,
        related_name='members',
        verbose_name='UAs que pertence',
    )

    # UAs que o usuário gerencia (pode criar demandas, atribuir e ver tudo)
    managed_uas = models.ManyToManyField(
        'dempam.InfoUA',
        blank=True,
        related_name='managers',
        verbose_name='UAs que gerencia',
    )

    must_change_password = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfis'

    def __str__(self):
        return f'Perfil de {self.user.username}'


# Cria o perfil automaticamente quando um novo usuário é criado
@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()


# Registro de acesso: um registro por login, usado para contar acessos no mês
class RegistroAcesso(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='registros_acesso')
    data = models.DateTimeField(auto_now_add=True, verbose_name='Data e Hora do Acesso')

    class Meta:
        verbose_name = 'Registro de Acesso'
        verbose_name_plural = 'Registros de Acesso'
        ordering = ['-data']

    def __str__(self):
        return f'{self.user.username} em {self.data:%d/%m/%Y %H:%M}'


@receiver(user_logged_in)
def registrar_acesso(sender, user, request, **kwargs):
    RegistroAcesso.objects.create(user=user)


class StatusFeedback(models.TextChoices):
    aberto       = 'ABERTO',       'Aberto'
    em_andamento = 'EM_ANDAMENTO', 'Em Andamento'
    finalizado   = 'FINALIZADO',   'Finalizada'
    recusado     = 'RECUSADO',     'Recusada'


class Feedback(models.Model):
    TIPO_BUG      = 'bug'
    TIPO_SUGESTAO = 'sugestao'
    TIPO_CHOICES  = [
        (TIPO_BUG,      'Bug'),
        (TIPO_SUGESTAO, 'Sugestão'),
    ]

    codigo    = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        unique=True,
        editable=False,
        verbose_name='Código',
    )
    user      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Usuário')
    tipo      = models.CharField(max_length=10, choices=TIPO_CHOICES, verbose_name='Tipo')
    status    = models.CharField(max_length=15, choices=StatusFeedback.choices, default=StatusFeedback.aberto, verbose_name='Status')
    descricao = models.TextField(verbose_name='Descrição')
    pagina    = models.CharField(max_length=500, blank=True, verbose_name='Página')
    imagem    = models.ImageField(upload_to='feedback/', blank=True, null=True, verbose_name='Print')
    resolucao = models.TextField(blank=True, verbose_name='O que foi feito')
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name='Enviado em')

    class Meta:
        verbose_name        = 'Feedback'
        verbose_name_plural = 'Feedbacks'
        ordering            = ['-criado_em']

    def save(self, *args, **kwargs):
        if not self.codigo:
            ano = timezone.now().year
            prefixo = f'RBS-{ano}-'
            existentes = Feedback.objects.filter(
                codigo__startswith=prefixo
            ).values_list('codigo', flat=True)
            numeros = []
            for cod in existentes:
                m = re.search(r'(\d+)$', cod)
                if m:
                    numeros.append(int(m.group(1)))
            proximo = (max(numeros) + 1) if numeros else 1
            self.codigo = f'{prefixo}{proximo:04d}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.codigo} [{self.get_tipo_display()}] {self.user} — {self.criado_em:%d/%m/%Y %H:%M}'
