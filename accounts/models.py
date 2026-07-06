from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


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


class Feedback(models.Model):
    TIPO_BUG      = 'bug'
    TIPO_SUGESTAO = 'sugestao'
    TIPO_CHOICES  = [
        (TIPO_BUG,      'Bug'),
        (TIPO_SUGESTAO, 'Sugestão'),
    ]

    user      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Usuário')
    tipo      = models.CharField(max_length=10, choices=TIPO_CHOICES, verbose_name='Tipo')
    descricao = models.TextField(verbose_name='Descrição')
    pagina    = models.CharField(max_length=500, blank=True, verbose_name='Página')
    imagem    = models.ImageField(upload_to='feedback/', blank=True, null=True, verbose_name='Print')
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name='Enviado em')

    class Meta:
        verbose_name        = 'Feedback'
        verbose_name_plural = 'Feedbacks'
        ordering            = ['-criado_em']

    def __str__(self):
        return f'[{self.get_tipo_display()}] {self.user} — {self.criado_em:%d/%m/%Y %H:%M}'
