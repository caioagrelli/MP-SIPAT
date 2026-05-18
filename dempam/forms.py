# Importações do Django
from django import forms

# Importações do código 
from .models import InfoUA, CircunscricaoPredio, SetorDEMPAM, LocalizacaoDEMPAM

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
            "sede",
            "gestor",
        ]
        widgets = {
            "circunscricao_predio": forms.Select(attrs={"class": "form-control"}),
            "ua": forms.TextInput(attrs={"class": "form-control"}),
            "contato_ua": forms.TextInput(attrs={"class": "form-control"}),
            "responsavel_ua": forms.TextInput(attrs={"class": "form-control"}),
            "mat_resp_ua": forms.NumberInput(attrs={"class": "form-control"}),
            "email_ua": forms.EmailInput(attrs={"class": "form-control"}),
            "sede": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "gestor": forms.Select(attrs={"class": "form-control"}),
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


''' Setores e Salas '''
# Adicionar um novo setor
class SetorDEMPAMForm(forms.ModelForm):
    class Meta:
        model = SetorDEMPAM
        fields = ['setor']

    # Validação personalizada para evitar setores duplicados
    def clean_setor(self):
        setor = self.cleaned_data.get('setor')
        # Verifica se já existe um setor com o mesmo nome
        if SetorDEMPAM.objects.filter(setor=setor).exists():
            raise forms.ValidationError('Este setor já está cadastrado.')
        return setor

# Adicionar uma nova localização
class LocalizacaoDEMPAMForm(forms.ModelForm):
    class Meta:
        model = LocalizacaoDEMPAM
        fields = ['setor_sala', 'prateleira_pallet', 'tipo_localizacao']