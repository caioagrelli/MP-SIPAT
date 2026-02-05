# Arquivo: itens/forms.py

from django import forms
from .models import Item, Bloco, Setor, Requisicao, ItemRequisitado
from django import forms



class UnifiedForm(forms.Form):
    """
    Formulário simplificado e unificado para cadastro.
    """
    # --- CONTROLE DE FLUXO ---
    TIPO_CADASTRO_CHOICES = [
        ('UNICO', 'Item Único'),
        ('LOTE', 'Lote'),
    ]
    tipo_cadastro = forms.ChoiceField(
        choices=TIPO_CADASTRO_CHOICES,
        widget=forms.RadioSelect,
        label="Tipo",
        initial='UNICO'
    )
    
    # --- CAMPOS QUE APARECEM SEMPRE (CATEGORIA) ---
    categoria = forms.ChoiceField(choices=Item.CATEGORIA_CHOICES, label="Categoria")

    # --- CAMPOS DE ITEM ÚNICO ---
    numero_identificacao = forms.IntegerField(label="Tombo / Nº de Identificação", required=False)
    foto_do_bem = forms.ImageField(label="Foto do Bem", required=False)

    # --- CAMPOS DE LOTE ---
    inicio = forms.IntegerField(label="Nº de Início (Tombo)", required=False)
    fim = forms.IntegerField(label="Nº de Fim (Tombo)", required=False)

    # --- CAMPOS DE DETALHES DO BEM (Comuns a todos) ---
    nome = forms.CharField(label="Nome / Descrição Curta", max_length=200)
    descricao = forms.CharField(widget=forms.Textarea, required=False, label="Descrição Detalhada")
    localizacao = forms.CharField(max_length=100, required=False, label="Localização")
    marca = forms.CharField(max_length=100, required=False, label="Marca")
    modelo = forms.CharField(max_length=100, required=False, label="Modelo")
    numero_de_serie = forms.CharField(max_length=100, required=False, label="Nº de Série")
    estado_de_conservacao = forms.CharField(max_length=100, required=False, label="Estado de Conservação")
    valor_unitario = forms.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        initial=0.00, 
        required=False, 
        label="Valor Unitário"
    )
    bloco = forms.ModelChoiceField(queryset=Bloco.objects.all(), required=False, label="Bloco")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, (forms.RadioSelect, forms.CheckboxInput, forms.FileInput)):
                field.widget.attrs.update({'class': 'form-control'})
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': 3})
                
class BlocoForm(forms.ModelForm):
        class Meta:
            model = Bloco
            # Defina os campos que o usuário deve preencher
            fields = ['nome', 'setor'] 
            widgets = {
                'nome': forms.TextInput(attrs={'class': 'form-control'}),
                'setor': forms.Select(attrs={'class': 'form-select'}),
            }
            labels = {
                'nome': 'Nome do Bloco/Pallet',
                'setor': 'Setor ao qual pertence',
            }

class MovimentacaoForm(forms.Form):
    quantidade = forms.IntegerField(min_value=1, label="Quantidade")
    observacao = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False)
    documento_pdf = forms.FileField(
        required=False, 
        label="Documento (PDF ou Foto)"
    )

class RequisicaoForm(forms.ModelForm):
    """
    Formulário para os dados gerais da Requisição (ex: observação).
    """
    class Meta:
        model = Requisicao
        # CORREÇÃO AQUI:
        # Removemos os campos que não existem mais e usamos o campo correto 'observacao_geral'
        fields = ['observacao_geral']
        widgets = {
            'observacao_geral': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

class ItemRequisitadoForm(forms.ModelForm):
    """
    Formulário para um único item dentro da requisição.
    """
    class Meta:
        model = ItemRequisitado # <-- E também sabe o que é 'ItemRequisitado'
        fields = ['item', 'quantidade']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['item'].widget.attrs.update({'class': 'form-control'})
        self.fields['quantidade'].widget.attrs.update({'class': 'form-control'})


class ImportarGoogleSheetsForm(forms.Form):
    url_planilha = forms.URLField(
        label="https://docs.google.com/spreadsheets/d/1CsljDQ1e6AC72Gg2mfqBIPxCuOxfYyDSsVTnoWNYjrk/edit?gid=0#gid=0", 
        help_text="Certifique-se de que a planilha foi compartilhada com o email da conta de serviço.",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )