# Importações do Jungle     Welcome to the jungle, we got fun and games - Guns N' Roses
from decimal import Decimal

from django.db import models
from django.conf import settings
from django.db import transaction
from django.db.models import Sum
from django.core.validators import MinValueValidator
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
    
    
    quantidade_contrato = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Quantidade Contrato',
    )


    saldo_disponivel = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
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

    numero_item = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='N° Item no Contrato',
    )

    preco_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        blank=True,
        null=True,
        verbose_name='Preço Unitário (R$)',
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

    numero_sei = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='N° SEI',
    )

    numero_empenho = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='N° Empenho',
    )

    numero_nota_fiscal = models.CharField(
        max_length=60,
        blank=True,
        verbose_name='N° Nota Fiscal',
    )

    nota_fiscal = models.FileField(
        upload_to=path_nota_fiscal_solicitacao,
        blank=True,
        null=True,
        verbose_name='Nota Fiscal (PDF)',
    )

    empenho = models.FileField(
        upload_to=path_empenho_solicitacao,
        blank=True,
        null=True,
        verbose_name='Empenho (PDF)',
    )

    termo_recebimento_definitivo = models.FileField(
        upload_to=path_termo_recebimento_solicitacao,
        blank=True,
        null=True,
        verbose_name='Termo de Recebimento Definitivo (PDF)',
    )

    class Meta():
        verbose_name='Solicitação Saldo Ativo'
        verbose_name_plural='05 - Solicitações Saldo Ativo'
        
        
    def save(self, *args, **kwargs):
        if not self.codigo:
            from django.db.models import Max
            import re
            ano = timezone.now().year
            prefixo = f'SSA-{ano}-'
            existentes = SolicitacoesSaldoAtivo.objects.filter(
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
    
    
    quantidade = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
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

        # Verifica se tem saldo suficiente (só valida em criação)
        if self.pk is None and self.bem_id and self.quantidade:
            if self.quantidade > (self.bem.saldo_disponivel or 0):
                raise ValidationError(
                    f'Quantidade solicitada ({self.quantidade}) maior que o saldo disponível ({self.bem.saldo_disponivel or 0}).'
                )

        # Quantidade fracionada só é permitida para itens medidos em metro
        if self.bem_id and self.quantidade is not None:
            try:
                validar_quantidade_por_unidade(self.quantidade, self.bem.efisco.medida)
            except ValueError as e:
                raise ValidationError({'quantidade': str(e)})

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        self.full_clean()
        with transaction.atomic():
            super().save(*args, **kwargs)
            # Desconta do saldo ativo no momento da solicitação
            if is_new and self.bem_id and self.quantidade:
                bem = self.bem
                bem.saldo_disponivel = max(0, (bem.saldo_disponivel or 0) - self.quantidade)
                bem.save(update_fields=['saldo_disponivel'])

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

    quantidade_enviada = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
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

    comprovante = models.FileField(
        upload_to=path_comprovante_remessa,
        blank=True,
        null=True,
        verbose_name='Comprovante de Recebimento',
        help_text='Nota fiscal, termo de recebimento ou outro documento (PDF, imagem)',
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

        # Nenhuma validação de saldo aqui — o saldo é descontado ao solicitar o item,
        # não ao registrar remessa.

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        # Detecta se recebida está sendo confirmada agora (False → True)
        recebimento_confirmado = False
        if not is_new:
            anterior = BensEnviados.objects.filter(pk=self.pk).values('recebida').first()
            if anterior and not anterior['recebida'] and self.recebida:
                recebimento_confirmado = True

        self.full_clean()
        with transaction.atomic():
            super().save(*args, **kwargs)

            # Aumenta o estoque físico quando o recebimento é confirmado
            if recebimento_confirmado:
                self._atualizar_estoque()

    def _atualizar_estoque(self):
        """Aumenta o estoque físico quando o recebimento da remessa é confirmado."""
        from .bensconsumo import Estoque

        bem = self.item_enviado.bem
        if not bem or not self.quantidade_enviada:
            return

        estoques = Estoque.objects.filter(item_shock=bem.efisco)
        if estoques.count() == 1:
            estoque = estoques.first()
            estoque.amount_shock += self.quantidade_enviada
            estoque.save(update_fields=['amount_shock', 'updated_at'])
        # Se houver mais de um local, não atualiza automaticamente —
        # o gestor deve distribuir manualmente via estoque.

    @property
    def quantidade_recebida(self):
        return self.quantidade_enviada if self.recebida else 0

    class Meta:
        verbose_name = 'Remessa'
        verbose_name_plural = '07 - Remessas'

    def __str__(self):
        status = 'Recebida' if self.recebida else 'Pendente'
        return f'Remessa {status} — {self.quantidade_enviada} un. — {self.item_enviado}'


""" Aditivos de Contrato """
# Aditivo — acréscimo de quantidade em itens já existentes no contrato e/ou itens novos
class AditivoContrato(models.Model):
    contrato = models.ForeignKey(
        Contrato,
        on_delete=models.PROTECT,
        related_name='aditivos',
        verbose_name='Contrato',
    )

    numero = models.CharField(
        max_length=30,
        unique=True,
        editable=False,
        verbose_name='Número do Aditivo',
    )

    numero_empenho = models.CharField(
        max_length=60,
        blank=True,
        verbose_name='N° Empenho',
    )

    documento = models.FileField(
        upload_to=path_documento_aditivo,
        blank=True,
        null=True,
        verbose_name='Documento',
    )

    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='aditivos_criados',
        verbose_name='Criado por',
    )

    criado_em = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')

    def save(self, *args, **kwargs):
        if not self.numero:
            salvar_com_codigo_sequencial(self, 'numero', 'ADT', super().save, *args, **kwargs)
        else:
            super().save(*args, **kwargs)

    class Meta():
        verbose_name = 'Aditivo de Contrato'
        verbose_name_plural = '14 - Aditivos de Contrato'
        ordering = ['-criado_em']

    def __str__(self):
        return f'{self.numero} — {self.contrato}'

    @property
    def valor_total(self):
        return sum((item.valor_total for item in self.itens.all()), Decimal('0'))


# Item de um aditivo — pode ser acréscimo em item já existente ou item novo no contrato
class ItemAditivoContrato(models.Model):
    aditivo = models.ForeignKey(
        AditivoContrato,
        on_delete=models.CASCADE,
        related_name='itens',
        verbose_name='Aditivo',
    )

    efisco = models.ForeignKey(
        BensConsumo,
        on_delete=models.PROTECT,
        related_name='itens_aditivo',
        verbose_name='Efisco',
    )

    quantidade_acrescida = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name='Quantidade Acrescida',
    )

    preco_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        validators=[MinValueValidator(0.01)],
        verbose_name='Preço Unitário (R$)',
    )

    item_novo = models.BooleanField(
        default=False,
        verbose_name='Item novo no contrato',
    )

    class Meta():
        verbose_name = 'Item de Aditivo'
        verbose_name_plural = '15 - Itens de Aditivo'

    def __str__(self):
        return f'{self.efisco} (+{self.quantidade_acrescida})'

    @property
    def valor_total(self):
        return self.quantidade_acrescida * self.preco_unitario
   