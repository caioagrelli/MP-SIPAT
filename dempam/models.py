from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from localflavor.br.models import BRCNPJField
from django.core.validators import RegexValidator
from .utils import *


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
        verbose_name_plural = '01 - Circunscrições/Prédios'

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
        verbose_name_plural='02 - UAs'

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
        verbose_name_plural='03 - Setores/Salas DEMPAM'
        
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
        verbose_name_plural='04 - Localizações DEMPAM'
        
    def __str__(self):
       return str(self.prateleira_pallet) 

