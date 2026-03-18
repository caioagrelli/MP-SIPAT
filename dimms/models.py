from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import date
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from localflavor.br.models import BRCNPJField
from django.core.validators import RegexValidator
from django.db.models import F
from .utils import *
from dempam.models import InfoUA, LocalizacaoDEMPAM

# Recursos Usados pelo Banco de Dados
class Complementos(): #Temporário
    validator_contato = RegexValidator(regex=r'^\+?\d{10,15}$',)

''' --- Informações Bens de Consumo DIMMS --- '''   
# Campo Usado para o cadastro de Bens de acordo com o EFISCO 
class BensConsumo(models.Model): 
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



""" Artefatos """
# Campo usado para o cadastro de fornecedores
class Supplier(models.Model): 
    supplier = models.CharField(
        max_length=40,
        verbose_name='Fornecedor'
    )

    cnpj_supplier = BRCNPJField(
        blank=True,
        null=True,
        verbose_name='CNPJ do Fornecedor',
    )
    
    contact_supplier = models.CharField(
    max_length=15,
    validators=[Complementos.validator_contato],
    blank=True,
    null=True,
    verbose_name='Contato do Fornecedor',
    )
    
    email_supplier = models.EmailField(
    blank=True,
    null=True,
    verbose_name='Email do Fornecedor'
    )
    
    class Meta():
        verbose_name='Fornecedor'
        verbose_name_plural='02 - Fonecedores'
        
    def __str__(self):
        return str(self.supplier)

class Artifacts(models.Model):
    artifacts_code = models.CharField(max_length=50, blank=True, unique=True, editable=False, verbose_name='Artefato')
    description = models.CharField(max_length=100, blank=True, verbose_name='Descrição')
    tr = models.FileField(upload_to=path_tr,blank=True,verbose_name='(TR) Termo de Referência')
    etp = models.FileField(upload_to=path_etp,blank=True,verbose_name='(ETP) Estudo Técnico Preeliminar')
    rgpp = models.FileField(upload_to=path_rgpp,blank=True,verbose_name='(RGPP) Registro de Preço')
    dode = models.FileField(upload_to=path_dode,blank=True,verbose_name='(DODE)Documento de Oficialização de Demanda')
    tapp = models.FileField(upload_to=path_tapp,blank=True,verbose_name='(TAPP) TERMO DE ANALISE PREELIMINAR DO PLANEJAMENTO DA CONTRATAÇÃO')
    risk_analysis = models.FileField(upload_to=path_risk_analysis,blank=True,verbose_name='Análise de Risco')
    state = models.CharField(max_length=40, choices=StatusArtifacts,blank=True,  verbose_name='Estado') 

    def save(self, *args, **kwargs): #pra ajeitar
        if not self.artifacts_code:
            ano = timezone.now().year
            ultimo = Artifacts.objects.filter(
                artifacts_code__startswith=f'ART-{ano}'
            ).count() + 1

            self.artifacts_code = f'ART-{ano}-{ultimo:02d}'

        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.artifacts_code)
    
    class Meta():
        verbose_name ='Artefato'
        verbose_name_plural ='Artefatos'  
    
class ItensArtifacts(models.Model):
    artifacts = models.ForeignKey(Artifacts, on_delete=models.PROTECT, verbose_name='Itens do Artefato')
    efisco = models.ForeignKey(BensConsumo, on_delete=models.PROTECT, blank=True,verbose_name='Efisco')
    details = models.TextField(blank=True, verbose_name='Detalhamento do Item')
    amount = models.PositiveIntegerField(blank=True, verbose_name='Quantidade')
    value_max = models.PositiveIntegerField(blank=True, verbose_name='Valor Máximo')
    
    class Meta():
        verbose_name ='Item Artefato'
        verbose_name_plural ='Itens Artefatos'  

class Proposal(models.Model):
    proposal_code = models.CharField(max_length=50, unique=True, blank=True, editable=False ,verbose_name='Proposta')
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, verbose_name='Fornecedor')
    artifacts_proposal = models.ForeignKey(Artifacts, on_delete=models.PROTECT, verbose_name='Artefato')
    state = models.CharField(max_length=30, choices=StatusProposal, blank=True, verbose_name='Estado') #pa arrumar

    def save(self, *args, **kwargs):
        if not self.proposal_code:
            ano = timezone.now().year

            ultima_proposta = Proposal.objects.filter(
                proposal_code__startswith=f'Proposta-{ano}-'
            ).order_by('-proposal_code').first()

            if ultima_proposta:
                ultimo_numero = int(ultima_proposta.proposal_code.split('-')[-1])
                proximo_numero = ultimo_numero + 1
            else:
                proximo_numero = 1

            self.proposal_code = f'Proposta-{ano}-{proximo_numero:04d}'

        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.proposal_code)
    
    class Meta():
        verbose_name ='Proposta'
        verbose_name_plural ='Propostas'  

class ItensProposal(models.Model):
    proposal_item = models.ForeignKey(Proposal, on_delete=models.PROTECT, verbose_name='Proposta')
    efisco = models.ForeignKey(BensConsumo, on_delete=models.PROTECT, verbose_name='Efisco')
    details_proposal = models.TextField(verbose_name='Detalhes da Proposta')
    amount = models.PositiveIntegerField(verbose_name='Quantidade')
    value = models.PositiveIntegerField(verbose_name='Valor')
    state = models.CharField(max_length=50, choices=StatusProposal ,blank=True, verbose_name='Status')
    reason = models.TextField(blank=True, verbose_name='Motivo da Reprovação')
    
    class Meta():
        verbose_name ='Item Proposta'
        verbose_name_plural ='Itens Propostas'  

# Campo usado para criação de Contratos
class Contrato(models.Model): #PRONTO
    supplier_contract = models.ForeignKey(
        Supplier,
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

    status = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Status do Contrato',
    )
    class Meta():
        verbose_name='Contrato'
        verbose_name_plural='03 - Contratos'
        
    def __str__(self):
        return str(self.contrato)



""" Saldo Ativo """
# Campo usado para cadastro de Itens (Baseado em um Contrato)
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

# Campo usado para solicitações de Itens com base em um Contrato
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

# Campo usado para Inserir os itens solicitados
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

# Campo usado para Inserir os Bens que foram enviados a partir da solicitação 
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



""" Estoque """
# Campo usado para armazenar os Itens em Estoque
class Estoque(models.Model): 
    item_shock = models.ForeignKey(
        BensConsumo,
        on_delete=models.PROTECT,
        related_name='bem_estoque',
        verbose_name='Bem no Estoque',
    )
    
    description_manual = models.CharField(
        max_length=90,
        verbose_name='Descrição Manual',
    )
    
    mark = models.CharField(
        max_length=40,
        verbose_name='Marca',
    )
        
    amount_shock = models.PositiveIntegerField(
        verbose_name='Quantidade',
    )
    
    locate = models.ForeignKey(
        LocalizacaoDEMPAM,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='localizacao_consumo',
        verbose_name='Localização',
        )
    
    monthly_consumption = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='Consumo Mensal',
    )
    
    essential = models.BooleanField(
        default=False,
        blank=True,
        null=True,
        verbose_name='Essencial',
    )
    
    validity = models.DateField(
        blank=True,
        null=True,
        verbose_name='Validade',
    )
    
    photo = models.ImageField(
        upload_to=caminho_bensconsumo,
        blank=True,
        null=True,      
        verbose_name='Foto do Item',
    )
    
    @property
    def duration(self):
        if self.amount_shock is not None and self.monthly_consumption not in (None, 0):
            return calcular_duracao(
                self.amount_shock,
                self.monthly_consumption
            )
        return None

    @property
    def low_stock(self):
        duracao = self.duration

        if not duracao:
            return False
        duracao = str(duracao).strip().lower()

        if "dia" in duracao:
            return True

        if "mes" in duracao:
            numero = (
                duracao
                .replace("meses", "")
                .replace("mês", "")
                .replace("mes", "")
                .strip()
            )

            try:
                return float(numero) < 3
            except ValueError:
                return False

        return False
        
    @property
    def alerta_vencimento(self):
        if not self.validity:
            return False

        dias_restantes = (self.validity - date.today()).days

        return dias_restantes <= 30

    class Meta():
        verbose_name='Bem Estoque'
        verbose_name_plural='08 - Bens Estoque'
        
    def __str__(self):
        return str(self.item_shock)



""" Parte de Solicitações """
# Campo usado para criar uma Solicitação de Materiais
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
        upload_to=caminho_movimentacao_consumo,
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

# Campo usado para adicionar os itens solicitados
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

# Campo usado para atualizar o status da entrega do material
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
        upload_to=caminho_consum_update,
        blank=True,
        null=True,
        verbose_name='Documento Anexado'
    )
    
    photo_update = models.ImageField(
        upload_to=caminho_consum_update,
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