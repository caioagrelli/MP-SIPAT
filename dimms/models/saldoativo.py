# Importações do Jungle     Welcome to the jungle, we got fun and games - Guns N' Roses
from django.db import models
from django.conf import settings
from django.db import transaction
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

# Itens que realmente foram enviados
class BensEnviados(models.Model):
    item_enviado = models.OneToOneField(
        ItensSolicitados,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='itemenviado',
        verbose_name='Bens Enviados',
    )

    quantidade_enviada = models.PositiveIntegerField(
        verbose_name='Quantidade Enviada',
        blank=True,
        null=True,
    )

    data_envio = models.DateTimeField(
        auto_now_add=True,
        blank=True,
        null=True,
        verbose_name='Data/Hora do Envio'
    )

    def clean(self):
        super().clean()

        # não enviar mais do que foi enviado
        if self.item_enviado_id and self.quantidade_enviada:
            if self.quantidade_enviada > (self.item_enviado.quantidade or 0):
                raise ValidationError('Quantidade enviada maior que a quantidade solicitada.')

            # não enviar mais do que o saldo atual permite
            bem = self.item_enviado.bem
            if bem and self.quantidade_enviada > (bem.saldo_disponivel or 0):
                raise ValidationError('Quantidade enviada maior que o saldo disponível.')

    def save(self, *args, **kwargs):
        self.full_clean()
        with transaction.atomic():
            super().save(*args, **kwargs)
            bem = self.item_enviado.bem
            if bem:
                bem.saldo_disponivel = (bem.saldo_disponivel or 0) - self.quantidade_enviada
                bem.save(update_fields=['saldo_disponivel'])

    class Meta:
        verbose_name = 'Item Enviado'
        verbose_name_plural = '07 - Bens Enviados'

    def __str__(self):
        return f'Envio de {self.quantidade_enviada} - {self.item_enviado}'
   