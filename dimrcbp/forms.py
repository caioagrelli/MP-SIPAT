from django.utils import timezone

from django import forms
from .models import BensPermanentes, Description, Supplier, HistoryUas, Inventario
from dempam.models import InfoUA


class CadastroBemForm(forms.ModelForm):
    # Campos de HistoryUas embutidos no mesmo form
    current_ua = forms.ModelChoiceField(
        queryset=InfoUA.objects.select_related('circunscricao_predio').order_by('ua'),
        required=False,
        label='UA Atual',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    current_year = forms.IntegerField(
        required=False,
        label='Ano de Entrada na UA',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 2024'}),
    )
    class Meta:
        model = BensPermanentes
        fields = [
            'tombo', 'description', 'mark', 'model', 'n_series',
            'acquisition_date', 'garantia_vencimento', 'value', 'entry_method',
            'n_empenho', 'n_process', 'modality', 'supllier',
            'state', 'situacion', 'photo',
        ]
        widgets = {
            'tombo':                forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 12345'}),
            'description':          forms.Select(attrs={'class': 'form-select'}),
            'mark':                 forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Dell, Intelbras…'}),
            'model':                forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Latitude 5540'}),
            'n_series':             forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de série'}),
            'acquisition_date':     forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'garantia_vencimento':  forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'value':                forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0,00'}),
            'entry_method':         forms.TextInput(attrs={'class': 'form-control'}),
            'n_empenho':            forms.TextInput(attrs={'class': 'form-control'}),
            'n_process':            forms.TextInput(attrs={'class': 'form-control'}),
            'modality':             forms.TextInput(attrs={'class': 'form-control'}),
            'supllier':             forms.Select(attrs={'class': 'form-select'}),
            'state':                forms.Select(attrs={'class': 'form-select'}),
            'situacion':            forms.Select(attrs={'class': 'form-select'}),
            'photo':                forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class InventarioForm(forms.ModelForm):
    class Meta:
        model = Inventario
        fields = ['situation', 'observation', 'photo']
        widgets = {
            'situation':   forms.Select(attrs={'class': 'form-select'}),
            'observation': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observações sobre o estado do bem…'}),
            'photo':       forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'situation':   'Situação no Inventário',
            'observation': 'Observação',
            'photo':       'Foto do Bem (inventário)',
        }


class AbrirInventarioForm(forms.Form):
    ano = forms.IntegerField(
        label='Ano',
        min_value=2000,
        max_value=2099,
        initial=timezone.now().year,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: 2025',
            'style': 'width:120px;',
        }),
    )
