# Importações do Django
from django import forms

# Importações do código 
from .models import InfoUA, CircunscricaoPredio

# ================================================================
# FORMS DO DEMPAM (DIVISÃO MINISTERIAL DE PATRIMÔNIO E MATERIAL)
# ================================================================



''' Unidades Administrativas '''
# Adiconar uma nova Ua
class InfoUAForm(forms.ModelForm):
    class Meta:
        model = InfoUA
        fields = [
            "circunscricao_predio",
            "ua",
            "contato_ua",
            "responsavel_ua",
            "mat_resp_ua",
            "email_ua",
        ]
        widgets = {
            "circunscricao_predio": forms.Select(attrs={"class": "form-control"}),
            "ua": forms.TextInput(attrs={"class": "form-control"}),
            "contato_ua": forms.TextInput(attrs={"class": "form-control"}),
            "responsavel_ua": forms.TextInput(attrs={"class": "form-control"}),
            "mat_resp_ua": forms.NumberInput(attrs={"class": "form-control"}),
            "email_ua": forms.EmailInput(attrs={"class": "form-control"}),
        }


''' Locais (Prédios e Circunscrições) '''
# Adicionar um novo local
class CircunscricaoPredioForm(forms.ModelForm):
    class Meta:
        model = CircunscricaoPredio
        fields = ["local", "meso", "micro"]

        widgets = {
            "local": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Informe o local (prédio ou circunscrição)"
            }),
            "meso": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Mesorregião (opcional)"
            }),
            "micro": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Microrregião (opcional)"
            }),
        }

        labels = {
            "local": "Local",
            "meso": "Mesorregião",
            "micro": "Microrregião",
        }

        help_texts = {
            "local": "Nome do prédio ou circunscrição.",
        }