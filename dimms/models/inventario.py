# Importações do Django
from django.db import models
from django.conf import settings
from django.utils import timezone

# Importações do código
from .bensconsumo import Estoque
from dempam.models import LocalizacaoDEMPAM
from ..utils import DecisaoAjusteEstoque

# ===============================
# MODELS DO INVENTÁRIO MENSAL (DIMMS)
# ===============================


''' Janela mensal de conferência de estoque — um período por mês/ano '''
class PeriodoInventarioConsumo(models.Model):
    mes = models.PositiveSmallIntegerField(verbose_name='Mês')
    ano = models.PositiveSmallIntegerField(verbose_name='Ano')

    aberto = models.BooleanField(default=True, verbose_name='Aberto')

    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='periodos_inventario_criados',
        verbose_name='Criado por',
    )
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    encerrado_em = models.DateTimeField(blank=True, null=True, verbose_name='Encerrado em')

    class Meta():
        verbose_name = 'Período de Inventário'
        verbose_name_plural = '12 - Períodos de Inventário (Consumo)'
        unique_together = ('mes', 'ano')
        ordering = ['-ano', '-mes']

    def __str__(self):
        return f'{self.mes:02d}/{self.ano}'

    @classmethod
    def periodo_atual(cls):
        agora = timezone.localtime(timezone.now())
        periodo, _ = cls.objects.get_or_create(mes=agora.month, ano=agora.year)
        return periodo

    @property
    def total_itens(self):
        return Estoque.objects.count()

    @property
    def total_conferidos(self):
        return self.conferencias.count()

    @property
    def total_pendentes(self):
        return max(self.total_itens - self.total_conferidos, 0)

    @property
    def percentual_concluido(self):
        total = self.total_itens
        if not total:
            return 0
        return round((self.total_conferidos / total) * 100)


''' Registro de conferência de um item de estoque dentro de um período de inventário '''
class ConferenciaEstoque(models.Model):
    periodo = models.ForeignKey(
        PeriodoInventarioConsumo,
        on_delete=models.CASCADE,
        related_name='conferencias',
        verbose_name='Período',
    )
    item = models.ForeignKey(
        Estoque,
        on_delete=models.CASCADE,
        related_name='conferencias_inventario',
        verbose_name='Item',
    )

    quantidade_anterior = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Quantidade Anterior')
    quantidade_conferida = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Quantidade Conferida')

    localizacao_anterior = models.ForeignKey(
        LocalizacaoDEMPAM,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='+',
        verbose_name='Localização Anterior',
    )
    localizacao_conferida = models.ForeignKey(
        LocalizacaoDEMPAM,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='+',
        verbose_name='Localização Conferida',
    )

    observacao = models.CharField(max_length=200, blank=True, verbose_name='Observação')

    conferido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='conferencias_estoque',
        verbose_name='Conferido por',
    )
    conferido_em = models.DateTimeField(auto_now_add=True, verbose_name='Conferido em')

    decisao_ajuste = models.CharField(
        max_length=15,
        choices=DecisaoAjusteEstoque.choices,
        default=DecisaoAjusteEstoque.pendente,
        verbose_name='Decisão do Ajuste',
    )
    decidido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='ajustes_estoque_decididos',
        verbose_name='Decidido por',
    )
    decidido_em = models.DateTimeField(blank=True, null=True, verbose_name='Decidido em')

    class Meta():
        verbose_name = 'Conferência de Estoque'
        verbose_name_plural = '13 - Conferências de Estoque'
        unique_together = ('periodo', 'item')
        ordering = ['-conferido_em']

    def __str__(self):
        return f'{self.item} — {self.periodo}'

    @property
    def houve_ajuste_quantidade(self):
        return self.quantidade_anterior != self.quantidade_conferida

    @property
    def houve_ajuste_localizacao(self):
        return self.localizacao_anterior_id != self.localizacao_conferida_id

    @property
    def houve_divergencia(self):
        return self.houve_ajuste_quantidade or self.houve_ajuste_localizacao
