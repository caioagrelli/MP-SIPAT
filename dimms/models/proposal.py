# Importações do Jungle     Welcome to the jungle, we got fun and games - Guns N' Roses
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

# Importações do código
from ..utils import *
from .artifacts import Supplier, Artifacts, ItensArtifacts

# ===============================
# MODELS DA DIMMS (BENS CONSUMO)
# ===============================


''' Propostas '''
# Propostas
class Proposal(models.Model):
    proposal_code = models.CharField(
        max_length=50,
        unique=True,
        blank=True, editable=False ,verbose_name='Proposta')
    
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        verbose_name='Fornecedor',
        )
    
    artifacts_proposal = models.ForeignKey(
        Artifacts,
        on_delete=models.PROTECT,
        verbose_name='Artefato'
        )
    
    state = models.CharField(
        max_length=30,
        choices=StatusProposal,
        blank=True,
        verbose_name='Estado'
        ) #pa arrumar

    def save(self, *args, **kwargs):
        if not self.proposal_code:
            ano = timezone.now().year

            ultima_proposta = Proposal.objects.filter(
                proposal_code__startswith=f'Proposta-{ano}-'
            ).order_by('-proposal_code').first()

            if ultima_proposta:
                ultimo_numero = int(ultima_proposta.proposal_code.split('-')[-1])
                proximo_numero = ultimo_numero + 1
            else:
                proximo_numero = 1

            self.proposal_code = f'Proposta-{ano}-{proximo_numero:04d}'

        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.proposal_code)
    
    class Meta():
        verbose_name ='Proposta'
        verbose_name_plural ='14 - Propostas'  

# Itens das Propostas
class ItensProposal(models.Model):
    proposal_item = models.ForeignKey(
        Proposal,
        on_delete=models.PROTECT,
        verbose_name='Proposta'
        )
    
    item = models.ForeignKey(
        ItensArtifacts,
        on_delete=models.PROTECT,
        verbose_name='Item'
        )
    
    details_proposal = models.TextField(
        blank=True,
        verbose_name='Detalhes da Proposta'
        )
    
    amount = models.PositiveIntegerField(
        blank=True,
        verbose_name='Quantidade'
        )
    
    value = models.PositiveIntegerField(
        blank=True,
        verbose_name='Valor'
        )
    
    state = models.CharField(
        max_length=50,
        choices=StatusProposal,
        blank=True,
        verbose_name='Status'
        )
    
    reason = models.TextField(
        blank=True,
        verbose_name='Motivo da Reprovação'
        )
    
    @property
    def total_value(self):
        return self.amount * self.value

    def clean(self):
        super().clean()

        if self.proposal_item and self.item:
            if self.item.artifacts_id != self.proposal_item.artifacts_proposal_id:
                raise ValidationError({
                    'item': 'Este item não pertence ao artefato vinculado à proposta selecionada.'
                })

        if self.state == 'RECUSADO' and not (self.reason or '').strip():
            raise ValidationError({
                'reason': 'Informe o motivo da reprovação para itens recusados.'
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        
    class Meta():
        verbose_name ='Item Proposta'
        verbose_name_plural ='15 - Itens Propostas'  

# Notas/ Observações (Desabilitada)
'''class Notes(models.Model):
    note_proposal = models.ForeignKey(
        Proposal,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notes',
        verbose_name='Proposta',
    )

    note_artifacts = models.ForeignKey(
        Artifacts,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notes',
        verbose_name='Artefato')

    note = models.TextField(
        verbose_name='Nota',
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última modificação',
    )

    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='artifacts_updated',
        verbose_name='Última edição por',
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em',
    )

    class Meta:
        verbose_name = 'Nota'
        verbose_name_plural = 'Notas'
        ordering = ['-updated_at']

    def clean(self):
        super().clean()

        if not self.note_artifacts and not self.note_proposal:
            raise ValidationError(
                'A nota precisa estar vinculada a um artefato ou a uma proposta.'
            )

        if self.note_artifacts and self.note_proposal:
            raise ValidationError(
                'A nota não pode estar vinculada a artefato e proposta ao mesmo tempo.'
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.note_artifacts:
            return f'Nota do artefato {self.note_artifacts}'
        if self.note_proposal:
            return f'Nota da proposta {self.note_proposal}'
        return 'Nota sem vínculo'
'''


