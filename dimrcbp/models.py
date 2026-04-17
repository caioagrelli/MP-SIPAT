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

class BensPermanentes(models.Model):
    tombo = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Tombo'
        )
    
    description = models.TextField(
        verbose_name='Descrição'
        )
    
    mark = models.CharField(
        max_length=60,
        verbose_name='Marca/Fabricante'
        )
    
    model = models.CharField(
        max_length=60,
        verbose_name='Modelo'
        )
    
    n_series = models.CharField(
        max_length=30,
        verbose_name='Número de Série'
        )
    
    acquisition_date = models.DateField(
        verbose_name='Data da Aquisição'
        )
    
    value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Valor Unitário'
        )
        
    photo = models.ImageField(
        upload_to=caminho_benspermanentes,
        blank=True,  
        null=True,
        verbose_name='Imagem do Bem'
        )  
    
    state = models.CharField(
        max_length=20,
        choices=EstadoConservacao.choices,
        blank=True,
        null=True,
        verbose_name='Estado de Conservação'
        )
    
    situacion = models.CharField(
        max_length=20,
        choices=SituacaoFisica.choices,
        blank=True,
        null=True,
        verbose_name='Situação Física'
        )
    
    entry_method = models.CharField(
        max_length=15,
        blank=True,
        default='Compra',
        verbose_name='Forma de Ingresso'
        )
    
    n_empenho = models.CharField(
        max_length=20,
        blank=True,
        default='S/Número',
        verbose_name='Número do Empenho'
        )
    
    n_process = models.CharField(
        max_length=20,
        blank=True,
        default='S/Número', 
        verbose_name='Número do Processo'
        )
    
    modality = models.CharField(
        max_length=25,
        blank=True,
        default='Pregão Eletrônico',
        verbose_name='Modalidade'
        )
    
    supllier = BRCNPJField(
        blank=True,
        null=True,
        verbose_name='Fornecedor'
        )
    
    
    class Meta:
        verbose_name = 'Bem Permanente'
        verbose_name_plural = 'Bens Permanentes'
        
    def __str__(self):
        return f'Tombo: {self.tombo} - Descrição: {self.description[:30]}'
    

class HistoryUas(models.Model):
    tombo = models.CharField(
        max_length=20,  
        unique=True,
        verbose_name='Tombo'
        )
    
    ua_current = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='UA Atual'
        )
    
    ua_last = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='UA Anterior'
        )

    ua_penultimate = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='UA Penúltima'
        )
    
    ua_third_last = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='UA Antepenúltima'
        )

    class Meta:
        verbose_name = 'Histórico das Uas'
        verbose_name_plural = 'Histórico das Uas'
        
        def __str__(self):
            return str(self.tombo)

class Description(models.Model):
    description = models.TextField(
        verbose_name='Descrição'
        )
    
    group = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        verbose_name='Grupo'
        )
    
    type = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        verbose_name='Tipo'
        )
    
    classification = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        verbose_name='Classificação'
        )
    
    subclassification = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        verbose_name='Subclassificação'
        )
    
    btu_hp = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        verbose_name='BTU/HP'
        )
    
    size = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        verbose_name='Tamanho'
        )
    
    color = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        verbose_name='Cor'
        )
    
    class Meta:
        verbose_name = 'Descrição'
        verbose_name_plural = 'Descrições'
        
    def __str__(self):
        return self.description[:60]


class Supplier(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name='Nome do Fornecedor'
        )
    
    cnpj = BRCNPJField(
        unique=True,
        verbose_name='CNPJ do Fornecedor'
        )
    
    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name='Email do Fornecedor'
        )
    
    phone = models.CharField(
        max_length=16,
        validators=[Complementos.validator_contato],
        blank=True,
        null=True,
        verbose_name='Telefone do Fornecedor'
        )
    
    Responsible = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Responsável pelo Fornecedor'
        )
    
    class Meta:
        verbose_name = 'Fornecedor'
        verbose_name_plural = 'Fornecedores'
        
    def __str__(self):
        return f'{self.name} - CNPJ: {self.cnpj}'

    
class UseExternal(models.Model):
    tombo = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Tombo'
        )
    
    responsible = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Responsável pelo Uso Externo'
        )
    
    contact_responsible = models.CharField(
        max_length=16,
        validators=[Complementos.validator_contato],
        blank=True,
        null=True,
        verbose_name='Contato do Uso Externo'
        )
    
    registration_responsible = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Registro do Responsável pelo Uso Externo'
        )
    
    email_responsible = models.EmailField(
        blank=True,
        null=True,
        verbose_name='Email do Uso Externo'
        )
    
    user = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Usuário do Uso Externo'
        )
    
    cpf_user = models.CharField(
        max_length=14,
        blank=True,
        null=True,
        verbose_name='CPF do Usuário do Uso Externo'
        )
    
    email_user = models.EmailField(
        blank=True,
        null=True,
        verbose_name='Email do Usuário do Uso Externo'
        )
    
    phone_user = models.CharField(
        max_length=16,
        validators=[Complementos.validator_contato],
        blank=True,
        null=True,
        verbose_name='Telefone do Usuário do Uso Externo'
        )
    
    date_renovation = models.DateField(
        blank=True,
        null=True,
        verbose_name='Data de Renovação do Uso Externo'
        )
    class Meta:
        verbose_name = 'Uso Externo'
        verbose_name_plural = 'Usos Externos'
        
    def __str__(self):
        return self.description[:60]
