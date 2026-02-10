from django.db import models
from django.conf import settings
from .utils import caminho_benspermanentes, caminho_bensconsumo, caminho_movimentacao_consumo
from .choices import AcaoConsumo, AcaoPermanente, TipoLocalizacao, UnidadesMedida, EstadoConservacao, SituacaoFisica, GrupoConsumo
from django.contrib.auth.models import User
from localflavor.br.models import BRCPFField, BRCNPJField
from django.core.validators import RegexValidator

# Recursos Usados pelo Banco de Dados
class Complementos(): #Temporário
    validator_contato = RegexValidator(regex=r'^\+?\d{10,15}$',)


# --- Informações sobre as Uas ---
class Locais(models.Model):
    id = models.AutoField(primary_key=True)
    
    
    local = models.CharField(
        max_length=80,
        verbose_name='Local',
    )
    
    class Meta:
        verbose_name = 'Local'
        verbose_name_plural = 'Locais'

    def __str__(self):
        return self.local

class InfoUA(models.Model): 
    id = models.AutoField(primary_key=True)
    
    
    circunscricao_predio = models.ForeignKey(
        Locais,
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
class Setor(models.Model):
    id = models.AutoField(primary_key=True)
    
    setor = models.CharField(
        max_length=30,
        verbose_name='Setor/Sala'
    )
    
    class Meta():
        verbose_name='Setor/Sala DEMPAM'
        verbose_name_plural='Setores/Salas'
        
    def __str__(self):
       return str(self.setor)  

class Localizacao(models.Model):
    id = models.AutoField(primary_key=True)

    setor_sala = models.ForeignKey(
        Setor,
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
        choices=TipoLocalizacao.choices,
        blank=True,
        null=True,
    )
    
    class Meta():
        verbose_name='Localização Interna DEMPAM'
        verbose_name_plural='Localizações Internas DEMPAM'
        
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
    
    
    cpf_fornecedor = BRCPFField(
        null=True,
        blank=True,
        verbose_name='CPF do Fornecedor',
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


# --- Informações Bens de Consumo DIMMS ---   
class BensConsumo(models.Model):
    id = models.AutoField(primary_key=True)
    
    efisco = models.CharField(
        max_length=20,
        default='Não Consta',
        blank=True,
        verbose_name='E-Fisco',
    )


    marca = models.CharField(
        max_length=30,
        default='S/Marca',
        blank=True,
        verbose_name='Marca',
    )
    
    
    validade = models.DateField(
        blank=True,
        null=True,
        verbose_name='Validade'
    )
    
    
    custo_unit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='Custo Unitário',
    )
   
    
    medida = models.CharField(
        max_length=20,
        choices=UnidadesMedida.choices,
        blank=True,
        null=True,
        verbose_name='Unidade de Medida',
    )

    
    quantidade = models.IntegerField(
        blank=True,
        null=True,
        default=0
    )
    
    
    grupo_consumo = models.CharField(
        choices=GrupoConsumo.choices,
        blank=True,
        null=True,
        verbose_name='Grupo',
    )
    
    
    local = models.ForeignKey(
        Localizacao,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='localizacao_consumo',
        verbose_name='Localização',
        
    )
    
    
    imagem_consumo = models.ImageField(
        upload_to=caminho_bensconsumo,
        blank=True,
        null=True,
        verbose_name='Imagem do Item'
    )
    
    class Meta():
        verbose_name='Bem de Consumo'
        verbose_name_plural='Bens de Consumo'
        
    def __str__(self):
        return self.efisco


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
        verbose_name='Movimentação Permanente'
        verbose_name_plural='Movimentações de Bens Permanentes'
        
    def __str__(self):
       return str(self.id)            
   
class MovimentacoesConsumo(models.Model): 
    
    id = models.AutoField(primary_key=True)
        
    item = models.ForeignKey(
        BensConsumo,
        on_delete=models.PROTECT,
        related_name='itens_movimentados',
        verbose_name='Item Movimentado',
    )
    
    
    acao = models.CharField(
        max_length=10,
        choices=AcaoConsumo.choices,
        verbose_name='Ação'
    )
    
    
    quantidade = models.PositiveIntegerField(
        verbose_name='Quantidade',
    )
    
    
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='usuario_mov_consumo',
        verbose_name='Usuário Responsável',
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
        verbose_name='Movimentação Consumo'
        verbose_name_plural='Movimentações de Bens Consumo'
        
    def __str__(self):
       return str(self.id)  
   
   
