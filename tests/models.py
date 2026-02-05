from django.db import models
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import User
from localflavor.br.models import BRCPFField, BRCNPJField

# --- Informações sobre as Uas ---
class Local(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=80)
    
    def __str__(self):
        return self.name

class InfoUA(models.Model):
    id = models.AutoField(primary_key=True)
    circunscricao_predio = models.ForeignKey(Local, on_delete=models.PROTECT, related_name=' Circunscrição/Prédio') 
    ua = models.CharField(max_length=100)
    contato_ua = models.CharField(max_length=16, blank=True, null=True)
    responsavel_ua = models.CharField(max_length=60, blank=True, null=True)
    mat_resp_ua = models.IntegerField(max_length=16, blank=True, null=True)
    email_ua = models.EmailField(blank=True, null=True)

    def __str__(self):
        return self.ua

# --- Informações Bens Permanentes DIMRCBP ---
class Bens(models.Model):
    id = models.AutoField(primary_key=True)
    efisco = models.IntegerField(max_length=20, blank=True, null=True)
    #descricao = models()
    #forma_de_controle = models()
    #tipo_de_bem = models()
    #imobilizado = models()
    marca_fabricante = models.CharField(max_length=30, blank=True, null=True)
    modelo = models.CharField(max_length=60, blank=True, null=True)
    numero_de_serie = models.CharField(max_length=30, blank=True, null=True)
    #situacao_juridica = models()
    #situacao_fisica = models()
    #estado_de_conservacao = models()
    #forma_de_ingresso = models()
    nota_fiscal = models.IntegerField(max_length=20, blank=True, null=True)
    #tipo_do_documento = models()
    codigo_unidade = models.IntegerField(max_length=10, blank=True, null=True)
    cpf_fonecedor = BRCPFField(null=True, blank=True)
    cnpj_fonecedor = BRCNPJField(null=True, blank=True)
    data_aquisicao = models.DateField(blank=True, null=True)
    data_de_entrega = models.DateField(blank=True, null=True)
    #modalidade = models()
    numero_do_processo = models.IntegerField(max_length=20, blank=True, null=True)
    codigo_natureza_de_despesa = models.CharField(max_length=20, blank=True, null=True)
    #moeda = models()
    numero_da_af = models.IntegerField(max_length=20, blank=True, null=True)
    numero_do_empenho = models.IntegerField(max_length=20, blank=True, null=True)
    garantia_em_dias = models.DateField(blank=True, null=True)
    valor_unitario = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    qtde = models.IntegerField()
    observacao = models.CharField(max_length=80, blank=True, null=True)
    conta_contabil = models()
    tombamento_legado = models()
    # unidade_gestora = models()
    # matricula_responsavel = models()
    # nome_responsavel = models()
    # valor_atual_do_bem = models()
    descricao_manual = models.CharField(max_length=30, blank=True, null=True)
    classe = models.CharField(max_length=30, blank=True, null=True)
    subclasse = models.CharField(max_length=30, blank=True, null=True)
    subclasse_2 = models.CharField(max_length=30, blank=True, null=True)
    subclasse_3 = models.CharField(max_length=30, blank=True, null=True)
    venc_garantia = models.DateField(blank=True, null=True)
    
    ua_atual = models.ForeignKey(InfoUA, on_delete=models.PROTECT, related_name='UA Atual')
    nome_resp_uso_ext = models.CharField(blank=True, null=True)
    contato_responsavel_uso_ext = models()
    
    def __str__(self):
        return self.tombamento_legado