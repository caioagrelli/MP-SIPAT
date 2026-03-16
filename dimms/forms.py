from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.core.exceptions import ValidationError
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
            'amount_order': forms.NumberInput(attrs={'min': 1}),
        }

    def clean(self):
        cleaned_data = super().clean()
        item = cleaned_data.get('item_order')
        quantidade = cleaned_data.get('amount_order')

        if not item or quantidade is None:
            return cleaned_data

        if quantidade <= 0:
            self.add_error('amount_order', 'A quantidade deve ser maior que zero.')
            return cleaned_data

        if quantidade > item.amount_shock:
            self.add_error(
                'amount_order',
                f'A quantidade solicitada ({quantidade}) é maior que o estoque atual ({item.amount_shock}).'
            )

        return cleaned_data


class SolicitacaoItemBaseFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()

        totais_por_item = {}

        for form in self.forms:
            if not hasattr(form, 'cleaned_data'):
                continue

            if form.cleaned_data.get('DELETE'):
                continue

            item = form.cleaned_data.get('item_order')
            quantidade = form.cleaned_data.get('amount_order')

            if not item or quantidade is None:
                continue

            if quantidade <= 0:
                raise ValidationError('A quantidade deve ser maior que zero.')

            if item.pk not in totais_por_item:
                totais_por_item[item.pk] = {
                    'item': item,
                    'total': 0,
                }

            totais_por_item[item.pk]['total'] += quantidade

        for dados in totais_por_item.values():
            item = dados['item']
            total = dados['total']

            if total > item.amount_shock:
                raise ValidationError(
                    f'O item "{item}" foi solicitado em quantidade total de {total}, '
                    f'mas o estoque atual é {item.amount_shock}.'
                )


SolicitacaoItemFormSet = inlineformset_factory(
    Solicitacao,
    SolicitacaoItens,
    form=SolicitacaoItemForm,
    formset=SolicitacaoItemBaseFormSet,
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