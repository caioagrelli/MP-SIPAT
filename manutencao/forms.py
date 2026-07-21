from django import forms

from .models import EstoqueManutencao


class EstoqueManutencaoForm(forms.ModelForm):
    class Meta:
        model = EstoqueManutencao
        fields = [
            'efisco', 'descricao', 'medida', 'grupo', 'mark',
            'amount_shock', 'locate', 'validity', 'photo', 'form_input',
        ]
        widgets = {
            'efisco': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Código E-Fisco'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'medida': forms.Select(attrs={'class': 'form-select'}),
            'grupo': forms.Select(attrs={'class': 'form-select'}),
            'mark': forms.TextInput(attrs={'class': 'form-control'}),
            'amount_shock': forms.NumberInput(attrs={'class': 'form-control'}),
            'locate': forms.Select(attrs={'class': 'form-control'}),
            'validity': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'form_input': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'efisco': 'E-Fisco',
            'descricao': 'Descrição',
            'medida': 'Unidade de Medida',
            'grupo': 'Grupo',
            'mark': 'Marca',
            'amount_shock': 'Quantidade a Adicionar',
            'locate': 'Localização',
            'validity': 'Validade',
            'photo': 'Foto do Item',
            'form_input': 'Forma de Entrada',
        }
