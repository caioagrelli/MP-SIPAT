# Importações do Jungle     Welcome to the jungle, we got fun and games - Guns N' Roses
from django.db import models
from django.conf import settings
from django.utils import timezone

# Importações do código
from ..utils import *
from dempam.models import InfoUA
from .bensconsumo import BensConsumo

# ===============================
# MODELS DA DIMMS (BENS CONSUMO)
# ===============================


# =============================================================
# CATÁLOGO DE BENS DE CONSUMO (separado do estoque)
# =============================================================

class CatalogoConsumo(models.Model):
    efisco = models.ForeignKey(
        BensConsumo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='catalogo_consumo',
        verbose_name='E-Fisco',
    )

    description = models.CharField(
        max_length=200,
        verbose_name='Descrição',
    )

    mark = models.CharField(
        max_length=80,
        blank=True,
        verbose_name='Marca',
    )

    detalhes = models.TextField(
        blank=True,
        verbose_name='Detalhes',
    )

    medida = models.CharField(
        max_length=20,
        choices=UnidadesMedida.choices,
        default=UnidadesMedida.unidade,
        verbose_name='Unidade de Medida',
    )

    grupo_consumo = models.CharField(
        max_length=50,
        choices=GrupoConsumo.choices,
        default=GrupoConsumo.papeis_expediente,
        verbose_name='Grupo',
    )

    photo = models.ImageField(
        upload_to=path_photo_catalogo_consumo,
        blank=True,
        null=True,
        verbose_name='Foto',
    )

    ativo = models.BooleanField(
        default=True,
        verbose_name='Ativo no catálogo',
    )

    class Meta:
        verbose_name = 'Catálogo Consumo'
        verbose_name_plural = 'Catálogo de Consumo'
        ordering = ['grupo_consumo', 'description']

    def __str__(self):
        return self.description


class SolicitacaoCatalogoConsumo(models.Model):
    codigo = models.CharField(
        max_length=30,
        unique=True,
        blank=True,
        editable=False,
        verbose_name='Código',
    )

    solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='solicitacoes_catalogo_consumo',
        verbose_name='Solicitante',
    )

    ua_destino = models.ForeignKey(
        InfoUA,
        on_delete=models.PROTECT,
        related_name='solicitacoes_catalogo_consumo',
        verbose_name='UA Destino',
    )

    status = models.CharField(
        max_length=20,
        choices=StatusSolicitacaoCatalogoConsumo.choices,
        default=StatusSolicitacaoCatalogoConsumo.pendente,
        verbose_name='Status',
    )

    data = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data',
    )

    observacao = models.TextField(
        blank=True,
        verbose_name='Observação',
    )

    obs_decisao = models.TextField(
        blank=True,
        verbose_name='Observação da Decisão',
    )

    decidido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='decisoes_catalogo_consumo',
        verbose_name='Decidido por',
    )

    data_decisao = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Data da Decisão',
    )

    class Meta:
        verbose_name = 'Solicitação Catálogo Consumo'
        verbose_name_plural = 'Solicitações Catálogo Consumo'
        ordering = ['-data']

    def save(self, *args, **kwargs):
        if not self.codigo:
            ano = timezone.now().year
            ultimo = SolicitacaoCatalogoConsumo.objects.filter(
                codigo__startswith=f'SCC-{ano}'
            ).count() + 1
            self.codigo = f'SCC-{ano}-{ultimo:04d}'
        super().save(*args, **kwargs)

    @property
    def total_itens(self):
        return self.itens.count()

    def __str__(self):
        return self.codigo


class ItemSolicitacaoCatalogoConsumo(models.Model):
    solicitacao = models.ForeignKey(
        SolicitacaoCatalogoConsumo,
        on_delete=models.CASCADE,
        related_name='itens',
        verbose_name='Solicitação',
    )

    catalogo = models.ForeignKey(
        CatalogoConsumo,
        on_delete=models.PROTECT,
        related_name='itens_solicitados',
        verbose_name='Item do Catálogo',
    )

    quantidade = models.PositiveIntegerField(
        default=1,
        verbose_name='Quantidade',
    )

    observacao = models.TextField(
        blank=True,
        verbose_name='Observação',
    )

    class Meta:
        verbose_name = 'Item Solicitação Catálogo Consumo'
        verbose_name_plural = 'Itens Solicitação Catálogo Consumo'

    def __str__(self):
        return f'{self.catalogo} ({self.quantidade}x)'