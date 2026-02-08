from django.db import models
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import User
from localflavor.br.models import BRCPFField, BRCNPJField
from django.core.validators import RegexValidator

# Recursos Usados pelo Banco de Dados
class Complementos():
    validator_contato = RegexValidator(regex=r'^\+?\d{10,15}$',)

# --- Informações sobre as Uas ---
class Locais(models.Model):
    id = models.AutoField(primary_key=True)
    
    
    local = models.CharField(
        max_length=80,
        verbose_name='Local',
    )
    
    
    def __str__(self):
        return self.name

class InfoUA(models.Model):
    
    id = models.AutoField(primary_key=True)
    
    
    circunscricao_predio = models.ForeignKey(
        Locais,
        on_delete=models.PROTECT, 
        related_name=' circunscrição_predio',
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
        blank=True, 
        null=True,
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


    def __str__(self):
        return self.ua


# --- Informações Bens Permanentes DIMRCBP ---
class BensPermanentes(models.Model):
    
    
    id = models.AutoField(
        primary_key=True
    )
        
    
    descricao = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        editable=False,
        verbose_name='Descrição',
    )
 
    
    forma_de_controle = models.CharField(
        max_length=15,
        default='Individual',
        verbose_name='Forma de Controle'
    )
    
    
    tipo_de_bem = models.CharField(
        max_length=15,
        default='Móvel',
        verbose_name='Tipo do Bem',
    )
    
    
    imobilizado = models.CharField(
        max_length=15,
        default='Sim',
        verbose_name='Imobilizado',
    )
    
    
    marca_fabricante = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        verbose_name='Marca/Fabricante',
    )
    
    
    modelo = models.CharField(
        max_length=60,
        blank=True,
        null=True,
        verbose_name='Modelo',
    )
    
    
    numero_de_serie = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        verbose_name='Número de Série',
    )
    
    
    situacao_juridica = models.CharField(
        max_length=15,
        default='Regular',
        verbose_name='Situação Jurídica'
    )
    
    #temporariamente
    situacao_fisica = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Situação Física',
    )
 
    #temporariamente    
    estado_de_conservacao = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Estado de Conservação',
    )
 
    
    forma_de_ingresso = models.CharField(
        max_length=15,
        default='Compra',
        verbose_name='Forma de Ingresso',
    )
    
    
    nota_fiscal = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='Nota Fiscal'
    )
    
    
    tipo_do_documento = models.CharField(
        max_length=20,
        default='Nota Fiscal',
        verbose_name='Tipo do Documento',
    )
    
    
    codigo_unidade = models.CharField(
        max_length=10,
        default='320101',
        editable=False,
        verbose_name='Código da Unidade',
    )
    
    
    cpf_fornecedor = BRCPFField(
        null=True,
        blank=True,
        verbose_name='CPF do Fornecedor',
    )

    
    cnpj_fornecedor = BRCNPJField(
        null=True,
        blank=True,
        verbose_name='CNPJ do Fornecedor',
    )
    
    
    data_aquisicao = models.DateField(
        blank=True,
        verbose_name='Data da aquisição',
        null=True,
    )
       
    
    modalidade = models.CharField(
        max_length=25,
        default='Pregão Eletrônico',
        verbose_name='Modalidade',
    )
    
    
    numero_do_processo = models.IntegerField(
        blank=True, 
        null=True,
        verbose_name='Número do Processo',
    )
    
    
    codigo_natureza_de_despesa = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Código Natureza de Despesa'
        
    )
    
    
    moeda = models.CharField(
        max_length=5,
        default='REAL',
        editable=False,
        verbose_name='Moeda',
    )
     
     
    numero_da_af = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='Número da AF',
        
    )
    
    
    numero_do_empenho = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='Número do Empenho',
    )
    
    
    garantia_em_dias = models.DateField(
        blank=True,
        null=True,
        verbose_name='Garantia em Dias',
    )
    
    
    valor_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        null=True,
        blank=True,
        verbose_name='Valor Unitário',
    )
    
    
    qtde = models.IntegerField(
        verbose_name='Quantidade',
    )
    
    
    observacao = models.CharField(
        max_length=80,
        blank=True,
        null=True,
        verbose_name='Observação',
    )
    
    
    conta_contabil = models.CharField(
        max_length=20,
        default='Ativo Móveis',
        blank=True,
        null=True,
        verbose_name='Conta Contábil',
        
        
    )
    
    
    tombamento_legado = models.IntegerField(
        unique=True,
        blank=True,
        null=True,
        verbose_name='Tombamento Legado',
    )
    
    
    unidade_gestora = models.ForeignKey(
        InfoUA,
        on_delete=models.PROTECT,
        related_name='unidade_gestora',
        blank=True,
        null=True,
        verbose_name='Unidade Gestora',
    )
    
    
    matricula_responsavel = models.IntegerField(
        verbose_name='Matrícula Responsável',
    )
    
    
    nome_responsavel = models.CharField(
    verbose_name='Nome Responsável',
    )
    
    
    valor_atual_do_bem = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        editable=False,
        null=True,
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
        related_name='ua_atual',
        blank=True,
        null=True,
        verbose_name='UA Atual'
    )


    nome_resp_uso_ext = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Nome Responsável Uso Externo',
    )
    

    matricula_resp_uso_ext = models.IntegerField(
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
    
        
    def __str__(self):
        return self.tombamento_legado

# --- Informações Bens de Consumo ---

class GrupoConsumo(models.Model):
    id = models.AutoField(primary_key=True)
    
    grupo = models.CharField(
        max_length=60,
    )    


    def __str__(self):
        return self.grupo
   
class BensConsumo(models.Model):
    id = models.AutoField(primary_key=True)
    
    efisco = models.IntegerField(
    verbose_name='E-Fisco',
    )


    marca = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        verbose_name='Marca',
    )
    
    
    validade = models.DateField(
        blank=True,
        null=True,
        verbose_name='Validade'
    )
    
    
    custo_unit = models.FloatField(
        blank=True,
        null=True,
        verbose_name='Custo Unitário',
    )
   
    
    medida = models.CharField(
        max_length=20,
        verbose_name='Unidade de Medida',
    )

    
    quantidade = models.IntegerField(
        blank=True,
        null=True,
        default=0
    )
    
    
    grupo_consumo = models.ForeignKey(
        GrupoConsumo,
        on_delete=models.PROTECT,
        related_name='GrupoConsumo',
        verbose_name='Grupo',
    )
    
