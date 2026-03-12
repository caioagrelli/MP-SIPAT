from django import forms
from django.forms import inlineformset_factory
from .models import Solicitacao, SolicitacaoItens, Tramitacao


class SolicitacaoForm(forms.ModelForm):
    class Meta:
        model = Solicitacao
        fields = [
            'ua_order',
            'user_order',
            'observation_order',
            'documents_order',
            'situation',
        ]
        widgets = {
            'observation_order': forms.Textarea(attrs={'rows': 4}),
        }


class SolicitacaoItemForm(forms.ModelForm):
    class Meta:
        model = SolicitacaoItens
        fields = ['item_order', 'amount_order']
        widgets = {
            'amount_order': forms.NumberInput(attrs={
                'min': 1
            }),
        }


SolicitacaoItemFormSet = inlineformset_factory(
    Solicitacao,
    SolicitacaoItens,
    form=SolicitacaoItemForm,
    extra=1,
    can_delete=True
)

class TramitacaoForm(forms.ModelForm):
    class Meta:
        model = Tramitacao
        fields = [
            'update',
            'responsible_update',
            'observation_update',
            'documents_update',
            'photo_update',
        ]
        widgets = {
            'update': forms.Select(attrs={'class': 'form-select'}),
            'responsible_update': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do responsável'
            }),
            'observation_update': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Digite uma observação...'
            }),
            'documents_update': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'photo_update': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }