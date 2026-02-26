from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from localflavor.br.models import BRCNPJField
from django.core.validators import RegexValidator
from .utils import *
from dempam.models import InfoUA, LocalizacaoDEMPAM

# Recursos Usados pelo Banco de Dados
class Complementos(): #Temporário
    validator_contato = RegexValidator(regex=r'^\+?\d{10,15}$',)

''' --- Informações Bens de Consumo DIMMS --- '''   
# Campo Usado para o cadastro de Bens de acordo com o EFISCO 
class BensConsumo(models.Model): 
    id = models.AutoField(primary_key=True)
    
    efisco = models.CharField(
        max_length=20,
        default='Não Consta',
        blank=True,
        verbose_name='E-Fisco',
    )
    

    descricao_efisco= models.TextField(
        blank=True,
        null=True,
        verbose_name='Descrição Efisco'
    )    
    
    
    medida = models.CharField(
        max_length=20,
        choices=UnidadesMedida.choices,
        blank=True,
        null=True,
        verbose_name='Unidade de Medida',
    )

    
    grupo_consumo = models.CharField(
        choices=GrupoConsumo.choices,
        blank=True,
        null=True,
        verbose_name='Grupo',
    )
    
    
    class Meta():
        verbose_name='Bem de Consumo'
        verbose_name_plural='01 - Bens de Consumo'
        
    def __str__(self):
        return self.efisco

# Campo usado para o cadastro de fornecedores
class Fornecedor(models.Model): #PRONTO
    id = models.AutoField(primary_key=True)
    
    fornecedor = models.CharField(
        max_length=40,
        verbose_name='Fornecedor'
    )


    cnpj_fornecedor = BRCNPJField(
        blank=True,
        null=True,
        verbose_name='CNPJ do Fornecedor',
    )
    
    
    contato_fornecedor = models.CharField(
    max_length=15,
    validators=[Complementos.validator_contato],
    blank=True,
    null=True,
    verbose_name='Contato do Fornecedor',
    )
    
    
    email_fornecedor = models.EmailField(
    blank=True,
    null=True,
    verbose_name='Email do Fornecedor'
    )

    
    class Meta():
        verbose_name='Fornecedor'
        verbose_name_plural='02 - Fonecedores'
        
    def __str__(self):
        return str(self.fornecedor)

# Campo Usado para formulário de cadastro de compra Individual
class CompraIndividual(models.Model): #PRONTO
    efisco = models.ForeignKey(
        BensConsumo,
        on_delete=models.PROTECT,
        related_name='compras_individuais',
        blank=True,
        null=True,
        verbose_name='Efisco'
    )
    
    
    bem = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Bem',
    )
    
    
    quantidade = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='Quantidade'
    )
    
    
    valor = models.PositiveIntegerField(
        verbose_name='Valor'
    )
    
    
    nf = models.FileField(
        upload_to=caminho_nf_compraindividual,
        blank=True,
        null=True,
        verbose_name='Nota Fiscal'
    )
    
    
    data_compra = models.DateField(
        blank=True,
        null=True,
        verbose_name='Data da Compra'
    
    )
    
    
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='usuario_compraindividual',
        verbose_name='Usuário Responsável',
    )
    
# Campo usado para criação de Contratos
class Contrato(models.Model): #PRONTO
    id = models.AutoField(primary_key=True)

    fornecedor = models.ForeignKey(
        Fornecedor,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    
    
    contrato = models.CharField(
        max_length=30,
        verbose_name='N° Contrato'
    )
    
    
    inicio_vigencia = models.DateField(
        blank=True,
        null=True,
        verbose_name='Início da Vigência',
    )
    
    
    final_vigencia = models.DateField(
        blank=True,
        null=True,
        verbose_name='Final da Vigência',
    )
    
    
    homologacao = models.DateField(
        blank=True,
        null=True,
        verbose_name='Homologação',
    )
    
    
    cs = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='N° CS',
    )
    
    
    cod_liquidacao = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='Código de Licitação',
    )


    class Meta():
        verbose_name='Contrato'
        verbose_name_plural='03 - Contratos'
        
    def __str__(self):
        return str(self.contrato)

# Campo usado para cadastro de Itens (Baseado em um Contrato)
class SaldoAtivo(models.Model): #PRONTO
    id = models.AutoField(primary_key=True)
    
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

# Campo usado para solicitações de Itens com base em um Contrato
class SolicitacoesSaldoAtivo(models.Model):
    id = models.AutoField(primary_key=True)
    
    codigo = models.CharField(
        max_length=30,
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

# Campo usado para Inserir os itens solicitados
class ItensSolicitados(models.Model):
    id = models.AutoField(primary_key=True)
    
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
        verbose_name = 'Item Solicitado'
        verbose_name_plural = '06 - Itens Solicitados'
        constraints = [
            models.UniqueConstraint(
                fields=['solicitacao', 'bem'],
                name='uniq_item_por_solicitacao'
            )
        ]

# Campo usado para Inserir os Bens que foram enviados a partir da solicitação 
class BensEnviados(models.Model):
    id = models.AutoField(primary_key=True)

    item_enviado = models.OneToOneField(
        ItensSolicitados,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='itemenviado',
        verbose_name='Itens Enviados',
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
        verbose_name_plural = '07 - Itens Enviados'

    def __str__(self):
        return f'Envio de {self.quantidade_enviada} - {self.item_enviado}'

class BensConsumoEstoque(models.Model): 
    id = models.AutoField(primary_key=True)
    
    solicitacao = models.ForeignKey(
        ItensSolicitados,
        on_delete=models.PROTECT,
        related_name='estoquesolicitacao',
        verbose_name='Estoque da Solicitação',
    )
      
        
    quantidade = models.PositiveIntegerField(
        verbose_name='Quantidade',
    )
    
    
    local_armazenamento = models.ForeignKey(
        LocalizacaoDEMPAM,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='localizacao_consumo',
        verbose_name='Localização',
        )

    
    class Meta():
        verbose_name='Bem de Consumo'
        verbose_name_plural='Bens de Consumo'
        
    def __str__(self):
        return self.efisco

class SolicitacoesConsumo(models.Model):  
    id = models.AutoField(primary_key=True)
        
    item = models.ForeignKey(
        BensConsumo,
        on_delete=models.PROTECT,
        related_name='itens_movimentados',
        verbose_name='Item Movimentado',
    )


    solicitante = models.ForeignKey(
        InfoUA,
        on_delete=models.PROTECT,
        related_name='solicitantesconsumo',
        verbose_name='Solicitante',
    )
    
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='usuario_sol_consumo',
        verbose_name='Usuário Responsável',
    )
    
    quantidade = models.PositiveIntegerField(
        verbose_name='Quantidade',
    )
    
    
    data_hora = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data e Hora da Movimentação'
    )
    
    
    observacao = models.TextField(
        blank=True,
        null=True,
        verbose_name='Observação'
    )
    
    
    anexo = models.FileField(
        upload_to=caminho_movimentacao_consumo,
        blank=True,
        null=True,
        verbose_name='Documento Anexado'
    )
    
    class Meta():
        verbose_name='Movimentação (Consumo)'
        verbose_name_plural='Movimentações (Consumo)'
        
    def __str__(self):
       return str(self.id)  

class Tramitacao(models.Model):
    ...

