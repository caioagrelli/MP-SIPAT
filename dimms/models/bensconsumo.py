# Importações do Jungle     Welcome to the jungle, we got fun and games - Guns N' Roses
from django.db import models
from django.conf import settings
from datetime import date

# Importações de validação
from django.core.validators import RegexValidator

# Importações do código
from ..utils import *
from dempam.models import LocalizacaoDEMPAM


class Complementos():
    validator_contato = RegexValidator(regex=r'^\+?\d{10,15}$',)

# ===============================
# MODELS DA DIMMS (BENS CONSUMO)
# ===============================


'''  Informações Bens de Consumo DIMMS  '''   
# Bens de acordo com o EFISCO
class BensConsumo(models.Model): 
    efisco = models.CharField(
        max_length=20,
        default='Não Consta',
        unique=True,
        verbose_name='E-Fisco',
    )
    

    descricao_efisco= models.TextField(
        verbose_name='Descrição Efisco'
    )    
    
    
    medida = models.CharField(
        max_length=20,
        choices=UnidadesMedida.choices,
        default=UnidadesMedida.unidade,
        verbose_name='Unidade de Medida',
    )

    
    grupo_consumo = models.CharField(
        max_length=50,
        choices=GrupoConsumo.choices,
        default=GrupoConsumo.alimento,
        verbose_name='Grupo',
    )

    almoxarifado = models.CharField(
        max_length=20,
        choices=TipoAlmoxarifado.choices,
        default=TipoAlmoxarifado.geral,
        verbose_name='Almoxarifado',
    )

    class Meta():
        verbose_name='Bem de Consumo'
        verbose_name_plural='01 - Bens de Consumo'
        
    def __str__(self):
        return self.efisco



""" Estoque """
# Itens em Estoque
class Estoque(models.Model): 
    item_shock = models.ForeignKey(BensConsumo,
        on_delete=models.PROTECT,
        related_name='bem_estoque',
        verbose_name='Bem no Estoque',)
    
    description_manual = models.CharField(max_length=90,verbose_name='Descrição Manual',)
    
    mark = models.CharField(max_length=40,verbose_name='Marca',)
        
    amount_shock = models.PositiveIntegerField(verbose_name='Quantidade',)
    
    locate = models.ForeignKey(
        LocalizacaoDEMPAM,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='localizacao_consumo',
        verbose_name='Localização',)
    
    monthly_consumption = models.PositiveIntegerField(blank=True,null=True,verbose_name='Consumo Mensal',)
    
    essential = models.BooleanField(default=False,blank=True, verbose_name='Essencial',)
    
    validity = models.DateField(blank=True,null=True,verbose_name='Validade',)
    
    photo = models.ImageField(upload_to=path_photo_bens,blank=True,null=True, verbose_name='Foto do Item',)
    
    form_input = models.CharField(max_length=30, blank=True, verbose_name='Forma de Entrada')

    created_at = models.DateTimeField(auto_now_add=True, blank=True ,verbose_name="Data de Cadastro")  
    
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name='Última modificação')
    
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_updated',
        verbose_name='Última edição por')

    method = models.CharField(max_length=60, blank=True, verbose_name='Método de Entrada' )
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


