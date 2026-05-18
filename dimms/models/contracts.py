# Importações do Jungle     Welcome to the jungle, we got fun and games - Guns N' Roses
from django.db import models

# Importações do código
from ..utils import *
from .artifacts import Supplier

# ===============================
# MODELS DA DIMMS (BENS CONSUMO)
# ===============================



''' Contratos '''
# Contratos
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
