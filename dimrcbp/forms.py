from django.utils import timezone

from django import forms
from .models import BensPermanentes, Description, Supplier, HistoryUas, Inventario, UseExternal
from .utils import SituacaoInventario
from dempam.models import InfoUA, LocalizacaoDEMPAM
from dempam.utils import TipoSetor


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

    # Cadastro em série — cria um bem para cada número de tombo no intervalo
    modo_serie = forms.BooleanField(required=False, widget=forms.HiddenInput())
    tombo_inicio = forms.IntegerField(
        required=False,
        label='Tombo Inicial',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 1000'}),
    )
    tombo_fim = forms.IntegerField(
        required=False,
        label='Tombo Final',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 1200'}),
    )

    MAX_SERIE = 500

    class Meta:
        model = BensPermanentes
        fields = [
            'tombo', 'description', 'mark', 'model', 'n_series',
            'acquisition_date', 'garantia_vencimento', 'value', 'entry_method',
            'n_empenho', 'n_process', 'modality', 'supllier',
            'state', 'situacion', 'photo', 'locate',
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
            'locate':               forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'locate': 'Localização (Pallet/Prateleira)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['locate'].queryset = (
            LocalizacaoDEMPAM.objects
            .filter(setor_sala__tipo=TipoSetor.dimrcbp)
            .select_related('setor_sala')
            .order_by('setor_sala__setor', 'prateleira_pallet')
        )
        self.fields['locate'].required = False
        self.fields['tombo'].required = False

    def clean(self):
        cleaned = super().clean()
        modo_serie = cleaned.get('modo_serie')
        tombo = cleaned.get('tombo')
        inicio = cleaned.get('tombo_inicio')
        fim = cleaned.get('tombo_fim')

        if modo_serie:
            if inicio is None or fim is None:
                raise forms.ValidationError('Informe o tombo inicial e o tombo final da série.')
            if inicio > fim:
                inicio, fim = fim, inicio
            qtd = fim - inicio + 1
            if qtd > self.MAX_SERIE:
                raise forms.ValidationError(
                    f'A série tem {qtd} tombos — o limite por cadastro é {self.MAX_SERIE}.'
                )
            existentes = list(
                BensPermanentes.objects
                .filter(tombo__in=[str(n) for n in range(inicio, fim + 1)])
                .values_list('tombo', flat=True)
            )
            if len(existentes) == qtd:
                raise forms.ValidationError(
                    f'Todos os {qtd} tombos da série ({inicio} a {fim}) já existem no cadastro.'
                )
            cleaned['tombo_inicio'] = inicio
            cleaned['tombo_fim'] = fim
            cleaned['tombos_existentes'] = existentes
        elif not tombo:
            self.add_error('tombo', 'Informe o tombo.')

        return cleaned


class UseExternalForm(forms.ModelForm):
    class Meta:
        model = UseExternal
        fields = [
            'responsible', 'cpf_responsible', 'contact_responsible', 'registration_responsible', 'email_responsible',
            'user', 'cpf_user', 'email_user', 'phone_user',
            'date_renovation',
        ]
        widgets = {
            'responsible':              forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do responsável pelo uso externo'}),
            'cpf_responsible':          forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000.000.000-00'}),
            'contact_responsible':      forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(00) 00000-0000'}),
            'registration_responsible': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Matrícula do responsável'}),
            'email_responsible':        forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@exemplo.com'}),
            'user':                     forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome de quem vai usar o bem (se diferente do responsável)'}),
            'cpf_user':                 forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000.000.000-00'}),
            'email_user':               forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@exemplo.com'}),
            'phone_user':               forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(00) 00000-0000'}),
            'date_renovation':          forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
        labels = {
            'responsible':              'Nome Completo',
            'cpf_responsible':          'CPF do Responsável',
            'contact_responsible':      'Contato do Responsável',
            'registration_responsible': 'Matrícula do Responsável',
            'email_responsible':        'Email do Responsável',
            'user':                     'Nome de Quem Vai Usar',
            'cpf_user':                 'CPF do Usuário',
            'email_user':               'Email do Usuário',
            'phone_user':               'Telefone do Usuário',
            'date_renovation':          'Data de Renovação',
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

    def clean(self):
        cleaned = super().clean()
        situation = cleaned.get('situation')
        photo = cleaned.get('photo')
        tem_foto_existente = bool(self.instance.pk and self.instance.photo)

        if situation != SituacaoInventario.nao_localizado and not photo and not tem_foto_existente:
            self.add_error('photo', 'Envie uma foto do bem, ou marque a situação como "Não Localizado".')

        return cleaned


class AbrirInventarioForm(forms.Form):
    descricao = forms.CharField(
        label='Descrição',
        max_length=100,
        initial=f'Inventário {timezone.now().year}',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: Inventário 2026',
        }),
    )
    inicio = forms.DateField(
        label='Início',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    fim = forms.DateField(
        label='Fim',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )

    def clean(self):
        cleaned = super().clean()
        inicio, fim = cleaned.get('inicio'), cleaned.get('fim')
        if inicio and fim and fim < inicio:
            raise forms.ValidationError('A data de fim não pode ser anterior à data de início.')
        return cleaned
