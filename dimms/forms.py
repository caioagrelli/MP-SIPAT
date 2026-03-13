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

class TramitacaoCreateForm(forms.ModelForm):
    class Meta:
        model = Tramitacao
        fields = [
            'request_update',
            'update',
            'responsible_update',
            'observation_update',
            'documents_update',
            'photo_update',
        ]
        widgets = {
            'request_update': forms.Select(attrs={'class': 'form-select'}),
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['request_update'].queryset = Solicitacao.objects.order_by('-id')
        self.fields['request_update'].empty_label = 'Selecione uma solicitação'

    def clean(self):
        cleaned_data = super().clean()
        solicitacao = cleaned_data.get('request_update')
        status = cleaned_data.get('update')

        if not solicitacao:
            self.add_error('request_update', 'Selecione a solicitação.')
        if not status:
            self.add_error('update', 'Selecione o status.')

        return cleaned_data
    
    
class SolicitacaoStatusUpdateForm(forms.ModelForm):
    observacao_tramitacao = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Digite uma observação sobre a atualização...'
        }),
        label='Observação da Atualização'
    )

    documents_update = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
        label='Documento Anexado'
    )

    photo_update = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
        label='Foto do Item'
    )

    class Meta:
        model = Solicitacao
        fields = ['situation']
        widgets = {
            'situation': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'situation': 'Novo Status',
        }