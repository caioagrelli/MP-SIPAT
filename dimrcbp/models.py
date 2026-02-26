from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from localflavor.br.models import BRCNPJField
from django.core.validators import RegexValidator
from .utils import *
from dempam.models import InfoUA

# Recursos Usados pelo Banco de Dados
class Complementos(): #Temporário
    validator_contato = RegexValidator(regex=r'^\+?\d{10,15}$',)

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
        verbose_name_plural='01 - Bens Permanentes'
        
    def __str__(self):
        return str(self.tombamento_legado)

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
        upload_to=caminho_benspermanentes,
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
        verbose_name_plural='02 - Movimentações (Permanentes)'
        
    def __str__(self):
       return str(self.id)            
   
