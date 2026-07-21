from django.conf import settings
from django.db import models

from .utils import GrupoManutencao, UnidadesMedida, path_photo_bem_manutencao


class ManutencaoAcesso(models.Model):
    """Model sem tabela — existe só para o app 'manutencao' ter um
    app_label com permissão própria antes de haver entidades reais."""

    class Meta:
        managed = False
        default_permissions = ()
        permissions = [
            ('access_manutencao', 'Pode acessar o módulo de Manutenção'),
        ]


# Estoque de bens de manutenção — um único registro por E-Fisco
# (sem catálogo separado: dar entrada já cadastra o item na hora).
class EstoqueManutencao(models.Model):
    efisco = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='E-Fisco',
    )

    descricao = models.TextField(
        verbose_name='Descrição',
    )

    medida = models.CharField(
        max_length=20,
        choices=UnidadesMedida.choices,
        default=UnidadesMedida.unidade,
        verbose_name='Unidade de Medida',
    )

    grupo = models.CharField(
        max_length=20,
        choices=GrupoManutencao.choices,
        default=GrupoManutencao.outros,
        verbose_name='Grupo',
    )

    mark = models.CharField(
        max_length=40,
        blank=True,
        verbose_name='Marca',
    )

    amount_shock = models.PositiveIntegerField(
        default=0,
        verbose_name='Quantidade',
    )

    locate = models.ForeignKey(
        'dempam.LocalizacaoDEMPAM',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='localizacao_manutencao',
        verbose_name='Localização',
    )

    validity = models.DateField(
        blank=True,
        null=True,
        verbose_name='Validade',
    )

    photo = models.ImageField(
        upload_to=path_photo_bem_manutencao,
        blank=True,
        null=True,
        verbose_name='Foto do Item',
    )

    form_input = models.CharField(
        max_length=30,
        blank=True,
        verbose_name='Forma de Entrada',
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data de Cadastro',
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última modificação',
    )

    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='estoque_manutencao_atualizado',
        verbose_name='Última edição por',
    )

    class Meta:
        verbose_name = 'Estoque de Manutenção'
        verbose_name_plural = 'Estoque de Manutenção'
        ordering = ['efisco']

    def __str__(self):
        return f'{self.efisco} — {self.descricao[:40]}'
