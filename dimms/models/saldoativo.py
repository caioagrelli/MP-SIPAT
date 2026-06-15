# Importações do Jungle     Welcome to the jungle, we got fun and games - Guns N' Roses
from django.db import models
from django.conf import settings
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from django.core.exceptions import ValidationError

# Importações do código
from ..utils import *
from .bensconsumo import BensConsumo
from .contracts import Contrato

# ===============================
# MODELS DA DIMMS (BENS CONSUMO)
# ===============================


""" Saldo Ativo """
# Itens do saldo ativo (Baseado em um Contrato)
class SaldoAtivo(models.Model): #PRONTO
    contrato_saldo = models.ForeignKey(
        Contrato,
        on_delete=models.PROTECT,
        related_name='Contrato',
        verbose_name='Contrato' 
    )
    
    
    efisco = models.ForeignKey(
        BensConsumo,
        on_delete=models.PROTECT,
        related_name='saldos_ativos',
        verbose_name='Efisco'
    )
   
    
    marca = models.CharField(
        max_length=60,
        blank=True,
        null=True,
        verbose_name='Marca',
    )    
    

    descricao_manual= models.CharField(
        max_length=60, 
        blank=True,
        null=True,
        verbose_name='Descrição Manual'
    )
    
    
    quantidade_contrato = models.PositiveIntegerField(
        verbose_name='Quantidade Contrato',
    )
    
    
    saldo_disponivel = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='Saldo Disponível',
    )

    
    cota = models.CharField(
        max_length=15,
        choices=Cota,
        blank=True,
        null=True,
        verbose_name='Cota'
    )
    
    def save(self, *args, **kwargs):
        if self.pk is None:
            self.saldo_disponivel = self.quantidade_contrato
        super().save(*args, **kwargs)
    
    class Meta():
        verbose_name='Saldo Ativo'
        verbose_name_plural='04 - Saldo Ativo'
        unique_together = ('contrato_saldo', 'efisco')
        
    def __str__(self):
        return f'{self.contrato_saldo} | {self.efisco}'

# solicitações de Itens do saldo ativo
class SolicitacoesSaldoAtivo(models.Model):
    codigo = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        unique=True,
        editable=False,
        verbose_name='Código da Solicitação'
    )
    
    
    status = models.CharField(
        max_length=20,
        choices=Status,
        default=Status.rascunho,
        verbose_name='Status',
    )
    
    
    contrato = models.ForeignKey(
        Contrato,
        on_delete=models.PROTECT,
        related_name='contrato_soli_saldoativo',
        verbose_name='Contrato',
    )
    
    
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='usuario_solic_saldoativo',
        verbose_name='Usuário Responsável',
    )
    
    
    data_hora = models.DateTimeField(
        blank=True,
        null=True,
        auto_now_add=True,
        verbose_name='Data e Hora da Movimentação'
    )
    
    

    class Meta():
        verbose_name='Solicitação Saldo Ativo'
        verbose_name_plural='05 - Solicitações Saldo Ativo'
        
        
    def save(self, *args, **kwargs):
        if not self.codigo:
            ano = timezone.now().year
            ultimo = SolicitacoesSaldoAtivo.objects.filter(
                codigo__startswith=f'SSA-{ano}'
            ).count() + 1

            self.codigo = f'SSA-{ano}-{ultimo:04d}'

        super().save(*args, **kwargs)

    def __str__(self):
        return self.codigo

# Itens que foram solicitados
class ItensSolicitados(models.Model):
    solicitacao = models.ForeignKey(
        SolicitacoesSaldoAtivo,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='bensenviados_saldoativo',
        verbose_name='Solicitação',
    )
    
    
    bem = models.ForeignKey(
        SaldoAtivo,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='itens_enviados',
        verbose_name='Item do Contrato (Saldo Ativo)',
    )
    
    
    quantidade = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='Quantidade Solicitada',
    )

    def clean(self):
        super().clean()

        # Verifica se o item pertence ao contrato da solicitação
        if self.solicitacao_id and self.bem_id:
            if self.bem.contrato_saldo_id != self.solicitacao.contrato_id:
                raise ValidationError(
                    'Esse item não pertence ao contrato desta solicitação.'
                )

        # Verifica se tem saldo suficiente
        if self.bem_id and self.quantidade:
            if self.quantidade > (self.bem.saldo_disponivel or 0):
                raise ValidationError(
                    'Quantidade solicitada maior que o saldo disponível.'
                )

    class Meta:
        verbose_name = 'Bens Solicitado'
        verbose_name_plural = '06 - Bens Solicitados'
        constraints = [
            models.UniqueConstraint(
                fields=['solicitacao', 'bem'],
                name='uniq_item_por_solicitacao'
            )
        ]

# Remessas enviadas pelo fornecedor (pode ser parcial, pode ter várias por item)
class BensEnviados(models.Model):
    item_enviado = models.ForeignKey(
        ItensSolicitados,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='remessas',
        verbose_name='Item Solicitado',
    )

    quantidade_enviada = models.PositiveIntegerField(
        verbose_name='Quantidade Enviada pelo Fornecedor',
        blank=True,
        null=True,
    )

    recebida = models.BooleanField(
        default=False,
        verbose_name='Recebida',
    )

    data_envio = models.DateTimeField(
        auto_now_add=True,
        blank=True,
        null=True,
        verbose_name='Data/Hora do Registro da Remessa'
    )

    data_recebimento = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Data/Hora do Recebimento',
    )

    observacao = models.CharField(
        max_length=300,
        blank=True,
        verbose_name='Observação',
    )

    def clean(self):
        super().clean()

        if not self.item_enviado_id or not self.quantidade_enviada:
            return

        # Total já enviado por remessas anteriores (excluindo a atual)
        total_ja_enviado = BensEnviados.objects.filter(
            item_enviado=self.item_enviado
        ).exclude(pk=self.pk).aggregate(t=Sum('quantidade_enviada'))['t'] or 0

        if total_ja_enviado + self.quantidade_enviada > (self.item_enviado.quantidade or 0):
            raise ValidationError(
                f'Total de remessas ({total_ja_enviado + self.quantidade_enviada}) '
                f'excede a quantidade solicitada ({self.item_enviado.quantidade}).'
            )

        bem = self.item_enviado.bem
        if bem and self.quantidade_enviada > (bem.saldo_disponivel or 0):
            raise ValidationError('Quantidade enviada maior que o saldo disponível no contrato.')

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        self.full_clean()
        with transaction.atomic():
            super().save(*args, **kwargs)
            # Desconta do saldo do contrato ao registrar a remessa
            if is_new:
                bem = self.item_enviado.bem
                if bem:
                    bem.saldo_disponivel = (bem.saldo_disponivel or 0) - self.quantidade_enviada
                    bem.save(update_fields=['saldo_disponivel'])

    @property
    def quantidade_recebida(self):
        return self.quantidade_enviada if self.recebida else 0

    class Meta:
        verbose_name = 'Remessa'
        verbose_name_plural = '07 - Remessas'

    def __str__(self):
        status = 'Recebida' if self.recebida else 'Pendente'
        return f'Remessa {status} — {self.quantidade_enviada} un. — {self.item_enviado}'
   