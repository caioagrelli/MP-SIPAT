# Importações do Jungle     Welcome to the jungle, we got fun and games - Guns N' Roses
from django.db import models
from django.conf import settings
from django.utils import timezone

# Importações de validação
from localflavor.br.models import BRCNPJField, BRCPFField

# Importações do código
from ..utils import *
from .bensconsumo import BensConsumo, Complementos

# ===============================
# MODELS DA DIMMS (BENS CONSUMO)
# ===============================


""" Artefatos """
# Fornecedores
class Supplier(models.Model): 
    supplier = models.CharField(
        max_length=40,
        verbose_name='Fornecedor'
    )

    cnpj_supplier = BRCNPJField(
        blank=True,
        verbose_name='CNPJ do Fornecedor',
    )
    
    name_responsible = models.CharField(
        max_length=90,
        verbose_name='Nome do Responsável'
        )
    
    cpf_responsible = BRCPFField(
        blank=True,
        verbose_name='Cpf do Responsável'
        )
    
    contact_supplier = models.CharField(
    max_length=15,
    validators=[Complementos.validator_contato],
    blank=True,
    verbose_name='Contato do Fornecedor',
    )
    
    email_supplier = models.EmailField(
    blank=True,
    verbose_name='Email do Fornecedor'
    )
    
    class Meta():
        verbose_name='Fornecedor'
        verbose_name_plural='02 - Fonecedores'
        
    def __str__(self):
        return str(self.supplier)

# Artefatos
class Artifacts(models.Model):
    artifacts_code = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        verbose_name='Artefato'
        )

    description = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Descrição'
        )

    sei = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='SEI'
        )

    tr = models.FileField(
        upload_to=path_tr,
        blank=True,
        verbose_name='(TR) Termo de Referência'
        )

    etp = models.FileField(
        upload_to=path_etp,
        blank=True,
        verbose_name='(ETP) Estudo Técnico Preeliminar'
        )

    rgpp = models.FileField(
        upload_to=path_rgpp,
        blank=True,
        verbose_name='(RGPP) Registro de Preço'
        )

    dode = models.FileField(
        upload_to=path_dode,
        blank=True,
        verbose_name='(DODE)Documento de Oficialização de Demanda'
        )

    tapp = models.FileField(
        upload_to=path_tapp,
        blank=True,
        verbose_name='(TAPP) TERMO DE ANALISE PREELIMINAR DO PLANEJAMENTO DA CONTRATAÇÃO'
        )

    risk_analysis = models.FileField(
        upload_to=path_risk_analysis,
        blank=True,
        verbose_name='Análise de Risco'
        )

    state = models.CharField(
        max_length=40,
        choices=StatusArtifacts,
        blank=True,
        verbose_name='Estado'
        )

    updated_at = models.DateTimeField(
        auto_now=True,
        blank=True,
        verbose_name='Última modificação'
        )

    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='artifacts_updated',
        verbose_name='Última edição por'
        )

    def save(self, *args, **kwargs): #pra ajeitar
        if not self.artifacts_code:
            ano = timezone.now().year
            ultimo = Artifacts.objects.filter(
                artifacts_code__startswith=f'ART-{ano}'
            ).count() + 1

            self.artifacts_code = f'ART-{ano}-{ultimo:02d}'

        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.artifacts_code)
    
    class Meta():
        verbose_name ='Artefato'
        verbose_name_plural ='12 - Artefatos'  

# Itens dos Artefatos
class ItensArtifacts(models.Model):
    artifacts = models.ForeignKey(
        Artifacts,
        on_delete=models.PROTECT,
        verbose_name='Itens do Artefato'
        )
    
    efisco = models.ForeignKey(
        BensConsumo,
        on_delete=models.PROTECT,
        verbose_name='Efisco'
        )
    
    details = models.TextField(
        blank=True,
        verbose_name='Detalhamento do Item'
        )
    
    amount = models.PositiveIntegerField(
        blank=True,
        verbose_name='Quantidade'
        )
    
    value_max = models.PositiveIntegerField(
        blank=True,
        verbose_name='Valor Máximo'
        )

    def __str__(self):
        return str(self.efisco)
    
    class Meta():
        verbose_name ='Item Artefato'
        verbose_name_plural ='13 - Itens Artefatos'  

