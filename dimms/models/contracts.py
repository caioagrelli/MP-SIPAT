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
        max_length=60,
        verbose_name='N° Contrato (MPPE)'
    )

    numero_contrato_oficial = models.CharField(
        max_length=30,
        blank=True,
        verbose_name='N° Contrato Oficial',
    )

    forma = models.CharField(
        max_length=10,
        blank=True,
        choices=[('ATA', 'ATA'), ('PARC', 'PARC'), ('CD', 'CD')],
        verbose_name='Forma',
    )

    numero_processo = models.CharField(
        max_length=60,
        blank=True,
        verbose_name='N° Processo Eletrônico',
    )

    numero_arp = models.CharField(
        max_length=60,
        blank=True,
        verbose_name='N° ARP PE Integrado',
    )

    categoria = models.CharField(
        max_length=60,
        blank=True,
        verbose_name='Categoria',
    )

    aditivo_prazo = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Aditivo de Prazo',
    )

    aditivo_preco = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Aditivo de Preço',
    )

    valor_contratado = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='Valor Contratado (R$)',
    )

    previsao_anual = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='Previsão Anual (R$)',
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

    numero_sc = models.CharField(
        max_length=30,
        blank=True,
        verbose_name='N° SC',
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
