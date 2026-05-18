# Importações do Jungle     Welcome to the jungle, we got fun and games - Guns N' Roses
from django.db import models
from django.db.models import F
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

# Importações do código
from ..utils import *
from dempam.models import InfoUA
from .bensconsumo import Estoque

# ===============================
# MODELS DA DIMMS (BENS CONSUMO)
# ===============================

""" Solicitações """
# Solicitação de Materiais
class Solicitacao(models.Model):  
    request_code = models.CharField(
        max_length=30,
        unique=True,
        editable=False,
        verbose_name='Código da Solicitação'
    )
          
    ua_order = models.ForeignKey(
        InfoUA,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='solicitantesconsumo',
        verbose_name='Solicitante',
    )
    
    user_order = models.CharField(
        max_length=40,
        blank=True,
        null=True,
        verbose_name='Usuário Solicitante',
    )
      
    data_order = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data e Hora da Movimentação'
    )
    
    observation_order = models.TextField(
        blank=True,
        null=True,
        verbose_name='Observação'
    )
    
    documents_order = models.FileField(
        upload_to=path_solicitation,
        blank=True,
        null=True,
        verbose_name='Documento Anexado'
    )

    stock_deducted = models.BooleanField(
        default=False,
        verbose_name='Estoque já baixado',
    )
    
    situation = models.CharField(
        max_length=25,
        choices=StatusTramitacao,
        verbose_name='Situação',
    )
 
    user_responsible = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='usuario_sol_consumo',
        verbose_name='Usuário Responsável',
    )   

    class Meta():
        verbose_name='Solicitações'
        verbose_name_plural='09 - Solicitações'
        
    def save(self, *args, **kwargs):
        if not self.request_code:
            ano = timezone.now().year
            ultimo = Solicitacao.objects.filter(
                request_code__startswith=f'SBC-{ano}'
            ).count() + 1
 
            self.request_code = f'SBC-{ano}-{ultimo:04d}'

        super().save(*args, **kwargs)        
        
    def __str__(self):
       return str(self.request_code)  

# Itens solicitados
class SolicitacaoItens(models.Model):
    request_defendant = models.ForeignKey(
        Solicitacao,
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name='bens_solicitados',
        verbose_name='Bens Solicitados',
    )
    
    item_order = models.ForeignKey(
        Estoque,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='itens_solicitados',
        verbose_name='Item Solicitado',
    )
    
    amount_order = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='Quantidade',
    )

    def clean(self):
        super().clean()

        if not self.item_order or self.amount_order is None:
            return

        if self.amount_order <= 0:
            raise ValidationError({
                'amount_order': 'A quantidade solicitada deve ser maior que zero.'
            })

        if self.amount_order > self.item_order.amount_shock:
            raise ValidationError({
                'amount_order': (
                    f'Quantidade solicitada ({self.amount_order}) maior que o '
                    f'estoque atual ({self.item_order.amount_shock}).'
                )
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    class Meta():
        verbose_name='Bem Solicitado'
        verbose_name_plural='10 - Bens Solicitados'
    
    def __str__(self):
        return str(self.request_defendant) 

# Atualizações de cada solicitação
class Tramitacao(models.Model):
    request_update = models.ForeignKey(
        Solicitacao,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='tramitacao',
        verbose_name='Tramitação',
    )

    update = models.CharField(
        max_length=30,
        choices=StatusTramitacao,
        default=StatusTramitacao.atendimento,
        blank=True,
        null=True,
        verbose_name='Status',
    )    
    
    responsible_update = models.CharField(
        max_length=40, 
        blank=True,
        null=True,
        verbose_name='Responsável pela Atualização',
    )
    
    observation_update = models.TextField(
        blank=True,
        null=True,
        verbose_name='Observação'       
    )   
    
    documents_update = models.FileField(
        upload_to=path_solicitation_update,
        blank=True,
        null=True,
        verbose_name='Documento Anexado'
    )
    
    photo_update = models.ImageField(
        upload_to=path_solicitation_photo,
        blank=True,
        null=True,
        verbose_name='Foto do Item',
    )
    
    date_update = models.DateTimeField(
        blank=True,
        null=True,
        auto_now_add=True,
        verbose_name='Data e Hora da Atualização'
    )
    
    user_update = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='usuario_atualizacao',
        verbose_name='Usuário Responsável',
    )
    
    class Meta():
        verbose_name='Tramitação'
        verbose_name_plural='11 - Tramitação'
    
    def save(self, *args, **kwargs):
        with transaction.atomic():
            novo_registro = self.pk is None

            super().save(*args, **kwargs)

            if self.request_update_id and self.update:
                solicitacao = Solicitacao.objects.select_for_update().get(pk=self.request_update_id)

                # atualiza a situação da solicitação pela tramitação mais recente
                ultima = solicitacao.tramitacao.order_by("-date_update", "-id").first()
                if ultima and ultima.id == self.id:
                    solicitacao.situation = self.update
                    solicitacao.save(update_fields=["situation"])

                # baixa automática do estoque apenas uma vez
                if (
                    novo_registro
                    and self.update in (
                        StatusTramitacao.aguar_separada,
                        StatusTramitacao.separada,
                        StatusTramitacao.em_expedicao,
                        StatusTramitacao.recebida,
                    )
                    and not solicitacao.stock_deducted
                ):
                    itens = solicitacao.bens_solicitados.select_related("item_order").all()

                    for item in itens:
                        if not item.item_order:
                            continue

                        estoque = item.item_order

                        if item.amount_order is None:
                            continue

                        if estoque.amount_shock < item.amount_order:
                            raise ValidationError(
                                f'Estoque insuficiente para "{estoque}". '
                                f'Disponível: {estoque.amount_shock}, '
                                f'Solicitado: {item.amount_order}.'
                            )

                    for item in itens:
                        if not item.item_order or item.amount_order is None:
                            continue

                        Estoque.objects.filter(
                            pk=item.item_order.pk
                        ).update(
                            amount_shock=F("amount_shock") - item.amount_order
                        )

                    solicitacao.stock_deducted = True
                    solicitacao.save(update_fields=["stock_deducted"])

    def __str__(self):
        return str(self.request_update)
