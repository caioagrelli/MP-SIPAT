from django import forms
from .models import BensPermanentes, Description, Supplier, HistoryUas
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
    current_responsible = forms.CharField(
        max_length=50,
        required=False,
        label='Responsável',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome completo'}),
    )
    current_registration = forms.CharField(
        max_length=50,
        required=False,
        label='Matrícula do Responsável',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 123456'}),
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
