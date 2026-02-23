from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from localflavor.br.models import BRCNPJField
from django.core.validators import RegexValidator
from .utils import *
from .choices import *


# Recursos Usados pelo Banco de Dados
class Complementos(): #Temporário
    validator_contato = RegexValidator(regex=r'^\+?\d{10,15}$',)


# --- Informações sobre as Uas ---
class CircunscricaoPredio(models.Model):
    id = models.AutoField(primary_key=True)
    
    
    local = models.CharField(
        max_length=80,
        verbose_name='Local',
    )
    
    class Meta:
        verbose_name = 'Circunscrição/Prédio'
        verbose_name_plural = 'Circunscrições/Prédios'

    def __str__(self):
        return self.local

class InfoUA(models.Model): 
    id = models.AutoField(primary_key=True)
    
    
    circunscricao_predio = models.ForeignKey(
        CircunscricaoPredio,
        on_delete=models.PROTECT, 
        related_name='circunscricoes_predios',
        verbose_name='Circunscricao/Prédio',
    )
     
     
    ua = models.CharField(
        max_length=100,
        verbose_name='UA',
    )


    contato_ua = models.CharField(
        max_length=15,
        validators=[Complementos.validator_contato],
        blank=True,
        null=True,
        verbose_name='Contato da UA',
    )
    
    
    responsavel_ua = models.CharField(
        max_length=60, 
        default='Não Consta',
        blank=True,
        verbose_name='Responsável da UA',
    )
    
    
    mat_resp_ua = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='Matrícula do Responsável da UA',
    )
    
    
    email_ua = models.EmailField(
        blank=True,
        null=True,
        verbose_name='Email da UA'
    )

    class Meta():
        verbose_name='UA'
        verbose_name_plural='UAs'

    def __str__(self):
        return self.ua


# --- Localização Interna no DEMPAM ---
class SetorDEMPAM(models.Model):
    id = models.AutoField(primary_key=True)
    
    setor = models.CharField(
        max_length=30,
        verbose_name='Setor/Sala'
    )
    
    class Meta():
        verbose_name='Setor/Sala DEMPAM'
        verbose_name_plural='Setores/Salas DEMPAM'
        
    def __str__(self):
       return str(self.setor)  

class LocalizacaoDEMPAM(models.Model):
    id = models.AutoField(primary_key=True)

    setor_sala = models.ForeignKey(
        SetorDEMPAM,
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name='localizacao_interna',
        verbose_name='Setor/Sala',
    )


    prateleira_pallet = models.CharField(
        max_length=30,
        blank=True, 
        null=True,
        verbose_name='Prateleira/Pallet'
    )
    
    
    tipo_localizacao = models.CharField(
        max_length=30,
        choices=TipoLocalizacao.choices,
        blank=True,
        null=True,
    )
    
    class Meta():
        verbose_name='Localização DEMPAM'
        verbose_name_plural='Localizações DEMPAM'
        
    def __str__(self):
       return str(self.prateleira_pallet) 


# --- Informações Bens Permanentes DIMRCBP ---
class BensPermanentes(models.Model):
    id = models.AutoField(
        primary_key=True
    )
        
    
    descricao = models.CharField(
        max_length=100,
        blank=True,
        default='Não Consta',
        editable=False,
        verbose_name='Descrição',
    )
 
    
    forma_de_controle = models.CharField(
        max_length=15,
        editable=False,
        default='Individual',
        verbose_name='Forma de Controle'
    )
    
    
    tipo_de_bem = models.CharField(
        max_length=15,
        editable=False,
        default='Móvel',
        verbose_name='Tipo do Bem',
    )
    
    
    imobilizado = models.BooleanField(
        editable=False,
        default=True,
        verbose_name='Imobilizado',
    )
    
    
    marca_fabricante = models.CharField(
        max_length=60,
        default='Sem Marca',
        blank=True,
        verbose_name='Marca/Fabricante',
    )
    
    
    modelo = models.CharField(
        max_length=60,
        default='S/Modelo',
        blank=True,
        verbose_name='Modelo',
    )
    
    
    numero_de_serie = models.CharField(
        max_length=30,
        default='S/Número',
        blank=True,
        verbose_name='Número de Série',
    )
    
    
    situacao_juridica = models.CharField(
        max_length=15,
        editable=False,
        default='Regular',
        verbose_name='Situação Jurídica'
    )
    
    situacao_fisica = models.CharField(
        max_length=20,
        choices=SituacaoFisica.choices,
        blank=True,
        null=True,
        verbose_name='Situação Física',
    )
 
    #temporariamente    
    estado_de_conservacao = models.CharField(
        max_length=20,
        choices=EstadoConservacao.choices,
        blank=True,
        null=True,
        verbose_name='Estado de Conservação',
    )
 
    
    forma_de_ingresso = models.CharField(
        max_length=15,
        blank=True,
        editable=False,
        default='Compra',
        verbose_name='Forma de Ingresso',
    )
    
    
    nota_fiscal = models.CharField(
        max_length=20,
        blank=True,
        default='S/Nota Fiscal',
        verbose_name='Nota Fiscal'
    )
    
    
    tipo_do_documento = models.CharField(
        max_length=20,
        blank=True,
        editable=False,
        default='Nota Fiscal',
        verbose_name='Tipo do Documento',
    )
    
    
    codigo_unidade = models.CharField(
        max_length=10,
        default='320101',
        blank=True,
        editable=False,
        verbose_name='Código da Unidade',
    )

    
    cnpj_fornecedor = BRCNPJField(
        blank=True,
        null=True,
        verbose_name='CNPJ do Fornecedor',
    )
    
    
    data_aquisicao = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data da aquisição',
    )
       
    
    modalidade = models.CharField(
        max_length=25,
        blank=True,
        default='Pregão Eletrônico',
        editable=False,
        verbose_name='Modalidade',
    )
    
    
    numero_do_processo = models.CharField(
        max_length=20,
        blank=True, 
        default='S/Número',
        verbose_name='Número do Processo',
    )
    
    
    codigo_natureza_de_despesa = models.CharField(
        max_length=20,
        blank=True,
        default='S/Número',
        verbose_name='Código Natureza de Despesa',
        
    )
    
    
    moeda = models.CharField(
        max_length=5,
        default='REAL',
        editable=False,
        verbose_name='Moeda',
    )
     
     
    numero_da_af = models.CharField(
        max_length=20,
        blank=True,
        default='S/Número',
        verbose_name='Número da AF',
        
    )
    
    
    numero_do_empenho = models.CharField(
        max_length=20,
        blank=True,
        default='S/Número',
        verbose_name='Número do Empenho',
    )
    
    
    garantia_em_dias = models.DateField(
        blank=True,
        null=True,
        verbose_name='Vencimento Garantia',
    )
    
    
    valor_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        blank=True,
        null=True,
        verbose_name='Valor Unitário',
    )
    
    
    qtde = models.IntegerField(
        blank=True,
        verbose_name='Quantidade',
    )
    
    
    observacao = models.TextField(
        max_length=80,
        blank=True,
        default='',
        verbose_name='Observação',
    )
    
    
    conta_contabil = models.CharField(
        max_length=20,
        default='Ativo Móveis',
        blank=True,
        verbose_name='Conta Contábil',        
    )
    
    
    tombamento_legado = models.IntegerField(
        unique=True,
        blank=True,
        null=True,
        verbose_name='Tombo',
    )
    
    
    unidade_gestora = models.ForeignKey(
        InfoUA,
        on_delete=models.PROTECT,
        related_name='unidades_gestora_dos_bens',
        blank=True,
        null=True,
        verbose_name='Unidade Gestora',
    )
    
    
    valor_atual_do_bem = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        editable=False,
        blank=True,
        verbose_name='Valor Atual do Bem',
    )
    
    
    descricao_manual = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        verbose_name='Descrição Manual'
    )
    
    
    classe = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        verbose_name='Classe',
    )
    
    
    subclasse = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        verbose_name='Subclasse',
    )
    
    
    subclasse_2 = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        verbose_name='Subclasse 2',
    )
    
    
    subclasse_3 = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        verbose_name='Subclasse 3',
    )
    
    
    venc_garantia = models.DateField(
        blank=True,
        null=True,
        verbose_name='Vencimento da Garantia'
        )
    
    
    ua_atual = models.ForeignKey(
        InfoUA,
        on_delete=models.PROTECT,
        related_name='uas_com_bens_cadastrados',
        blank=True,
        null=True,
        verbose_name='UA Atual'
    )
    
    
    imagem_permanente = models.ImageField(
        upload_to=caminho_benspermanentes,
        blank=True,
        null=True,
        verbose_name='Imagem do Bem'
    )

# Informações Uso Externo
    nome_resp_uso_ext = models.CharField(
        max_length=50,
        default='Não Consta',
        blank=True,
        verbose_name='Nome Responsável Uso Externo',
    )
    

    matricula_resp_uso_ext = models.CharField(
        max_length=25,
        default='Não Consta',
        blank=True,
        null=True,
        verbose_name='Matrícula Responsável Uso Externo',
    )


    contato_resp_uso_ext = models.CharField(
        max_length=16,
        validators=[Complementos.validator_contato],
        blank=True,
        null=True,
        verbose_name='Contato Responsável Uso Externo',
    )
    

    class Meta():
        verbose_name='Bem Permanente'
        verbose_name_plural='Bens Permanentes'
        
    def __str__(self):
        return str(self.tombamento_legado)


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
        verbose_name_plural='Bens de Consumo'
        
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
        verbose_name_plural='Fonecedores'
        
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
        verbose_name_plural='Contratos'
        
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
        verbose_name_plural='Saldo Ativo'
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
        default='Rascunho',
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
        verbose_name_plural='Solicitação Saldo Ativo'
        
        
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
class BensEnviados(models.Model):
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
        constraints = [
            models.UniqueConstraint(
                fields=['solicitacao', 'bem'],
                name='uniq_item_por_solicitacao'
            )
        ]

class BensConsumoEstoque(models.Model): 
    id = models.AutoField(primary_key=True)
    
    solicitacao = models.ForeignKey(
        BensEnviados,
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


# --- Histórico de Movimentações---
class MovimentacoesPermanentes(models.Model):
    id = models.AutoField(primary_key=True)
    
    sei = models.CharField(
        max_length=25,
        blank=True,
        null=True,
        verbose_name='SEI',
    )
    
    
    tombo = models.ForeignKey(
        BensPermanentes,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='tombos_movimentados',
        verbose_name='Tombo',
    )
    
    
    acao = models.CharField(
        choices=AcaoPermanente.choices,
        default=AcaoPermanente.tranferencia,
        verbose_name='Ação',
    )


    origem = models.ForeignKey(
        InfoUA,
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name='origens_uas',
        verbose_name='Origem',
    )


    destino = models.ForeignKey(
        InfoUA,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='destinos_uas',
        verbose_name='Destino',
    )
    
    
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='usuario_mov_permanentes',
        verbose_name='Usuário Responsável',
    )
    
    
    data_hora = models.DateTimeField(
        blank=True,
        null=True,
        auto_now_add=True,
        verbose_name='Data e Hora da Movimentação'
    )

    
    anexo = models.FileField(
        upload_to=caminho_movimentacao_consumo,
        blank=True,
        null=True,
        verbose_name='Documento Anexado'
    )
    
    
    nome_resp_uso_ext = models.CharField(
        max_length=50,
        default='Não Consta',
        blank=True,
        verbose_name='Nome Responsável Uso Externo',
    )


    matricula_resp_uso_ext = models.CharField(
        max_length=25,
        default='Não Consta',
        blank=True,
        null=True,
        verbose_name='Matrícula Responsável Uso Externo',
    )


    contato_resp_uso_ext = models.CharField(
        max_length=25,
        validators=[Complementos.validator_contato],
        blank=True,
        null=True,
        verbose_name='Contato Responsável Uso Externo',
    )

    
    class Meta():
        verbose_name='Movimentação (Permanente)'
        verbose_name_plural='Movimentações (Permanentes)'
        
    def __str__(self):
       return str(self.id)            
   
