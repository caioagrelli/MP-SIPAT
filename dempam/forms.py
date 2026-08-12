# Importações do Django
from django import forms

# Importações do código
from .models import InfoUA, CircunscricaoPredio, SetorDEMPAM, LocalizacaoDEMPAM, Aviso, ConfiguracaoPainelTV
from .utils import TipoLocalizacao

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


''' Mural de Avisos '''
# Publicar um novo aviso no mural do DEMPAM
class AvisoForm(forms.ModelForm):
    class Meta:
        model = Aviso
        fields = ['titulo', 'mensagem', 'exibir_de', 'exibir_ate']
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título do aviso',
            }),
            'mensagem': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Mensagem do aviso',
            }),
            'exibir_de': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
            }),
            'exibir_ate': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        exibir_de = cleaned_data.get('exibir_de')
        exibir_ate = cleaned_data.get('exibir_ate')
        if exibir_de and exibir_ate and exibir_de >= exibir_ate:
            raise forms.ValidationError('A data final precisa ser depois da data inicial.')
        return cleaned_data


''' Painel de TV '''
class ConfiguracaoPainelTVForm(forms.ModelForm):
    class Meta:
        model = ConfiguracaoPainelTV
        fields = ['video_arquivo', 'video_url']
        widgets = {
            'video_arquivo': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'video/*',
            }),
            'video_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'Link do YouTube ou link direto de um vídeo (.mp4)',
            }),
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
        # Verifica se já existe outro setor com o mesmo nome (exclui a própria instância na edição)
        qs = SetorDEMPAM.objects.filter(setor=setor)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Este setor já está cadastrado.')
        return setor

# Adicionar uma nova localização
class LocalizacaoDEMPAMForm(forms.ModelForm):
    class Meta:
        model = LocalizacaoDEMPAM
        fields = ['setor_sala', 'tipo_localizacao', 'prateleira_pallet', 'corredor', 'estante', 'prateleira']
        widgets = {
            'corredor': forms.TextInput(attrs={'placeholder': 'Ex.: A'}),
            'estante': forms.TextInput(attrs={'placeholder': 'Ex.: 3'}),
            'prateleira': forms.TextInput(attrs={'placeholder': 'Ex.: 6'}),
            'prateleira_pallet': forms.TextInput(attrs={'placeholder': 'Identificação do pallet'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo_localizacao')

        if tipo == TipoLocalizacao.prateleira:
            faltando = [
                nome for campo, nome in [
                    ('corredor', 'Corredor'), ('estante', 'Estante'), ('prateleira', 'Prateleira'),
                ] if not cleaned_data.get(campo)
            ]
            if faltando:
                raise forms.ValidationError(
                    f'Para localizações do tipo Prateleira, informe: {", ".join(faltando)}.'
                )
        elif tipo == TipoLocalizacao.pallet:
            if not cleaned_data.get('prateleira_pallet'):
                raise forms.ValidationError('Informe a identificação do pallet.')

        return cleaned_data