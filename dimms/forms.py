# Importações do Django
from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.core.exceptions import ValidationError

# Importações do código
from .models import Estoque, SolicitacaoItens, Solicitacao, Tramitacao, Artifacts, ItensArtifacts, BensConsumo, Proposal, ItensProposal, Supplier, Contrato, SaldoAtivo

# =================================
# FORMS DA DIMMS (BENS DE CONSUMO)
# =================================



''' Estoque '''
# Estoque 
class EstoqueForm(forms.ModelForm):
    class Meta:
        model = Estoque
        fields = [
            'item_shock',
            'description_manual',
            'mark',
            'amount_shock',
            'locate',
            'monthly_consumption',
            'essential',
            'validity',
            'photo',
            'form_input',
        ]
        widgets = {
            'item_shock': forms.Select(attrs={'class': 'form-control'}),
            'description_manual': forms.TextInput(attrs={'class': 'form-control'}),
            'mark': forms.TextInput(attrs={'class': 'form-control'}),
            'amount_shock': forms.NumberInput(attrs={'class': 'form-control'}),
            'locate': forms.Select(attrs={'class': 'form-control'}),
            'monthly_consumption': forms.NumberInput(attrs={'class': 'form-control'}),
            'essential': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'validity': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'form_input': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'item_shock': 'Bem no Estoque',
            'description_manual': 'Descrição Manual',
            'mark': 'Marca',
            'amount_shock': 'Quantidade',
            'locate': 'Localização',
            'monthly_consumption': 'Consumo Mensal',
            'essential': 'Essencial',
            'validity': 'Validade',
            'photo': 'Foto do Item',
            'form_input': 'Forma de Entrada',
        }

# Adicionar um item ao estoque já existente no estoque
class stock_up(forms.Form):
    item_estoque = forms.ModelChoiceField(
        queryset=Estoque.objects.select_related("item_shock").all().order_by("item_shock"),
        label="Item em Estoque",
        widget=forms.Select(attrs={"class": "form-control"})
    )

    quantidade_entrada = forms.IntegerField(
        label="Quantidade a adicionar",
        min_value=1,
        widget=forms.NumberInput(attrs={"class": "form-control", "min": 1})
    )

    form_input = forms.CharField(
        label="Forma de Entrada",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    method = forms.CharField(
        label="Método de Entrada",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    def clean_quantidade_entrada(self):
        quantidade = self.cleaned_data.get("quantidade_entrada")
        if quantidade is None or quantidade <= 0:
            raise forms.ValidationError("Informe uma quantidade maior que zero.")
        return quantidade


''' Solicitaçoes '''
# Criar nova solicitação
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

# Adicionar itens as solicitações
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

# Extenção de SolicitacaoForm (para adicionar no momento da criação)
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



''' Tramitações '''
# Atualizar a tramitação da solicitação (pode escolher)
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
    
# Atualizar a tramitação da solicitação a partir dela mesma (não pode escolher)
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



''' Artefatos '''
# Adicionat itens aos artefatos
class ItensArtifactsForm(forms.ModelForm):
    class Meta:
        model = ItensArtifacts
        fields = [
            'efisco',
            'details',
            'amount',
            'value_max',
        ]
        widgets = {
            'details': forms.Textarea(attrs={'rows': 4}),
        }

# Gerenciar documentos dos artefatos
class ArtifactDocumentsForm(forms.ModelForm):
    class Meta:
        model = Artifacts
        fields = [
            'tr',
            'etp',
            'rgpp',
            'dode',
            'tapp',
            'risk_analysis',
        ]
        
# Criar um novo artefato
class ArtifactsCreateForm(forms.ModelForm):
    class Meta:
        model = Artifacts
        fields = ['description', 'sei', 'tr', 'etp', 'rgpp', 'dode', 'tapp', 'risk_analysis', 'state']
        widgets = {
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Aquisição de materiais de limpeza',
            }),
            'sei': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número SEI do processo',
            }),
            'state': forms.Select(attrs={'class': 'form-select'}),
        }


''' Fornecedores '''
class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['supplier', 'cnpj_supplier', 'name_responsible', 'cpf_responsible', 'contact_supplier', 'email_supplier']
        widgets = {
            'supplier':          forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do fornecedor'}),
            'cnpj_supplier':     forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00.000.000/0000-00'}),
            'name_responsible':  forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome completo'}),
            'cpf_responsible':   forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000.000.000-00'}),
            'contact_supplier':  forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(81) 99999-9999'}),
            'email_supplier':    forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@fornecedor.com'}),
        }
        labels = {
            'supplier':         'Nome do Fornecedor',
            'cnpj_supplier':    'CNPJ',
            'name_responsible': 'Nome do Responsável',
            'cpf_responsible':  'CPF do Responsável',
            'contact_supplier': 'Telefone de Contato',
            'email_supplier':   'E-mail',
        }


''' Propostas '''
# Criar nova proposta
class ProposalForm(forms.ModelForm):
    class Meta:
        model = Proposal
        fields = ['supplier', 'state']
        widgets = {
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'state': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'supplier': 'Fornecedor',
            'state': 'Status',
        }

# Adicionar item à proposta
class ItensProposalForm(forms.ModelForm):
    class Meta:
        model = ItensProposal
        fields = ['item', 'details_proposal', 'amount', 'value']
        widgets = {
            'item': forms.Select(attrs={'class': 'form-select'}),
            'details_proposal': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'value': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }
        labels = {
            'item': 'Item do Artefato',
            'details_proposal': 'Detalhes da Proposta',
            'amount': 'Quantidade Ofertada',
            'value': 'Valor Unitário (R$)',
        }

    def __init__(self, *args, artifact=None, **kwargs):
        super().__init__(*args, **kwargs)
        if artifact:
            self.fields['item'].queryset = ItensArtifacts.objects.filter(
                artifacts=artifact
            ).select_related('efisco')


''' Contratos '''
# Criar contrato
class ContratoForm(forms.ModelForm):
    class Meta:
        model = Contrato
        fields = [
            'supplier_contract', 'contrato', 'inicio_vigencia',
            'final_vigencia', 'homologacao', 'cs', 'cod_liquidacao', 'status',
        ]
        widgets = {
            'supplier_contract': forms.Select(attrs={'class': 'form-select'}),
            'contrato': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'N° do contrato'}),
            'inicio_vigencia': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'final_vigencia': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'homologacao': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'cs': forms.NumberInput(attrs={'class': 'form-control'}),
            'cod_liquidacao': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Ativo'}),
        }
        labels = {
            'supplier_contract': 'Fornecedor',
            'contrato': 'N° do Contrato',
            'inicio_vigencia': 'Início da Vigência',
            'final_vigencia': 'Final da Vigência',
            'homologacao': 'Data de Homologação',
            'cs': 'N° CS',
            'cod_liquidacao': 'Código de Licitação',
            'status': 'Status',
        }


''' Saldo Ativo '''
# Adicionar item ao saldo ativo de um contrato
class SaldoAtivoItemForm(forms.ModelForm):
    class Meta:
        model = SaldoAtivo
        fields = ['efisco', 'marca', 'descricao_manual', 'quantidade_contrato', 'cota']
        widgets = {
            'efisco': forms.Select(attrs={'class': 'form-select'}),
            'marca': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Marca X'}),
            'descricao_manual': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Descrição complementar'}),
            'quantidade_contrato': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'cota': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'efisco': 'E-Fisco (Bem de Consumo)',
            'marca': 'Marca',
            'descricao_manual': 'Descrição Manual',
            'quantidade_contrato': 'Quantidade do Contrato',
            'cota': 'Tipo de Cota',
        }


''' Bens de Consumo '''
# Cadastrar Bem de Consumo
class BensConsumoForm(forms.ModelForm):
    class Meta:
        model = BensConsumo
        fields = ['efisco', 'descricao_efisco', 'medida', 'grupo_consumo']
        widgets = {
            'efisco': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Digite o código E-Fisco'
            }),
            'descricao_efisco': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Digite a descrição do bem de consumo',
                'rows': 4
            }),
            'medida': forms.Select(attrs={
                'class': 'form-select'
            }),
            'grupo_consumo': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
        labels = {
            'efisco': 'E-Fisco',
            'descricao_efisco': 'Descrição Efisco',
            'medida': 'Unidade de Medida',
            'grupo_consumo': 'Grupo',
        } 