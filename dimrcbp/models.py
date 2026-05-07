# Importações do Django
from localflavor.br.models import BRCNPJField
from django.core.validators import RegexValidator
from django.contrib.auth.models import User
from django.utils import timezone

# Importações do codigo
from .utils import *
from dempam.models import InfoUA

# Recursos Usados pelo Banco de Dados
class Complementos(): #Temporário
    validator_contato = RegexValidator(regex=r'^\+?\d{10,15}$',)




''' INFORMAÇÕES DA CLASSIFICAÇÃO DOS BENS PERMANENTES '''
# Grupos
class Groups(models.Model):
    group = models.CharField(
        max_length=30,
        unique=True,
        verbose_name='Nome do Grupo'
        )
    
    class Meta:
        verbose_name = 'Grupo'
        verbose_name_plural = '2 - Grupos'
        
    def __str__(self):
        return self.group

# Tipo do bem permanente, associado a um grupo específico
class Type(models.Model):
    gruop = models.ForeignKey(
        Groups,
        on_delete=models.PROTECT,
        verbose_name='Grupo'
        )
    
    type = models.CharField(
        max_length=30,
        unique=True,
        verbose_name='Nome do Tipo'
        )
    
    class Meta:
        verbose_name = 'Tipo'
        verbose_name_plural = '3 - Tipos'
        
    def __str__(self):
        return self.type

# Descrição detalhada do bem permanente, associada a um tipo específico
class Description(models.Model):
    description = models.TextField(
        verbose_name='Descrição'
        )
    
    subdescription = models.CharField(
        max_length=30,
        blank=True,
        verbose_name='Subdescrição'
        )
    
    type = models.ForeignKey(
        Type,
        on_delete=models.PROTECT,
        verbose_name='Tipo'
        )
    
    classification = models.CharField(
        max_length=30,
        blank=True,
        verbose_name='Classificação'
        )
    
    subclassification = models.CharField(
        max_length=30,
        blank=True,
        verbose_name='Subclassificação'
        )
    
    capacity = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='BTU/HP'
        )
    
    size = models.CharField(
        max_length=30,
        blank=True,
        verbose_name='Tamanho'
        )
    
    color = models.CharField(
        max_length=40,
        choices=Cores.choices,
        blank=True,
        verbose_name='Cor'
        )
    
    class Meta:
        verbose_name = 'Descrição'
        verbose_name_plural = '4 - Descrições'
        
    def __str__(self):
        return self.description[:60]



'''FORNECEDORES'''
# Fornecedores
class Supplier(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name='Nome do Fornecedor'
        )
    
    cnpj = models.CharField(
        max_length=22,
        unique=True,
        verbose_name='CNPJ do Fornecedor'
        )
    
    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name='Email do Fornecedor'
        )
    
    phone = models.CharField(
        max_length=16,
        validators=[Complementos.validator_contato],
        blank=True,
        null=True,
        verbose_name='Telefone do Fornecedor'
        )
    
    Responsible = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Responsável pelo Fornececimento'
        )
    
    class Meta:
        verbose_name = 'Fornecedor'
        verbose_name_plural = '4 - Fornecedores'
        
    def __str__(self):
        return f'{self.name} - CNPJ: {self.cnpj}'



'''BENS PERMANENTES'''
# Bens Permanentes
class BensPermanentes(models.Model):
    tombo = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Tombo'
        )
    
    description = models.ForeignKey(
        Description,
        on_delete=models.PROTECT,
        related_name='description_tombo',
        verbose_name='Descrição'
        )
    
    mark = models.CharField(
        max_length=60,
        verbose_name='Marca/Fabricante'
        )
    
    model = models.CharField(
        max_length=60,
        verbose_name='Modelo'
        )
    
    n_series = models.CharField(
        max_length=30,
        verbose_name='Número de Série'
        )
    
    acquisition_date = models.DateField(
        verbose_name='Data da Aquisição'
        )

    garantia_vencimento = models.DateField(
        blank=True,
        null=True,
        verbose_name='Vencimento da Garantia'
        )
    
    value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Valor Unitário'
        )
        
    photo = models.ImageField(
        upload_to=caminho_benspermanentes,
        blank=True,  
        null=True,
        verbose_name='Imagem do Bem'
        )  
    
    state = models.CharField(
        max_length=20,
        choices=EstadoConservacao.choices,
        blank=True,
        null=True,
        verbose_name='Estado de Conservação'
        )
    
    situacion = models.CharField(
        max_length=20,
        choices=SituacaoFisica.choices,
        blank=True,
        null=True,
        verbose_name='Situação Física'
        )
    
    entry_method = models.CharField(
        max_length=15,
        blank=True,
        default='Compra',
        verbose_name='Forma de Ingresso'
        )
    
    n_empenho = models.CharField(
        max_length=20,
        blank=True,
        default='S/Número',
        verbose_name='Número do Empenho'
        )
    
    n_process = models.CharField(
        max_length=20,
        blank=True,
        default='S/Número', 
        verbose_name='Número do Processo'
        )
    
    modality = models.CharField(
        max_length=25,
        blank=True,
        default='Pregão Eletrônico',
        verbose_name='Modalidade'
        )
    
    supllier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name='Fornecedor'
         )
    
    
    class Meta:
        verbose_name = 'Bem Permanente'
        verbose_name_plural = '1 - Bens Permanentes'
        
    def __str__(self):
        return f'Tombo: {self.tombo} - Descrição: {str(self.description)[:30]}'

# Histórico das UAs que o Bem Permanente passou
class HistoryUas(models.Model):
    tombo = models.OneToOneField(
        BensPermanentes,
        on_delete=models.PROTECT,
        related_name='history_tombo',
        verbose_name='Tombo'
        )


    # UA Atual
    current_ua = models.ForeignKey(
        InfoUA,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='history_current_ua',
        verbose_name='UA Atual'
        )

    current_year = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='Ano Entrada Ua Atual'
        )

    current_responsible = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Responsável da Ua Atual'
        )

    current_registration = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Matrícula do Responsável da Ua Atual'
        )


    # Ua Anterior
    last_ua = models.ForeignKey(
        InfoUA,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='history_last_ua',
        verbose_name='UA Anterior'
        )

    last_year = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='Ano Entrada Ua Anterior'
        )

    last_responsible = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Responsável da última Ua'
        )

    last_registration = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Matrícula do Responsável da Ua Anterior'
        )


    # Penúltima Ua
    penultimate_ua = models.ForeignKey(
        InfoUA,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='history_penultimate_ua',
        verbose_name='UA Penúltima'
        )

    penultimate_year = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='Ano Entrada Ua Penúltima'
    )

    penultimate_responsible = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Responsável da penúltima'
    )

    penultimate_registration = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Matrícula do Responsável da Ua penúltima'
    )


    # Antepenúltima Ua
    third_last_ua = models.ForeignKey(
        InfoUA,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='history_third_last_ua',
        verbose_name='UA Antepenúltima'
        )

    third_last_year = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='Ano Entrada Ua Antepenúltima'
    )


    class Meta:
        verbose_name = 'Histórico das Uas'
        verbose_name_plural = '5 - Histórico das Uas'

    def __str__(self):
        return str(self.tombo)

# Usuários Externos
class UseExternal(models.Model):
    tombo = models.ForeignKey(
        BensPermanentes,
        on_delete=models.PROTECT,
        verbose_name='Tombo'
        )
    
    responsible = models.CharField(
        max_length=50,
        verbose_name='Responsável pelo Uso Externo'
        )
    
    contact_responsible = models.CharField(
        max_length=16,
        validators=[Complementos.validator_contato],
        blank=True,
        verbose_name='Contato do Uso Externo'
        )
    
    registration_responsible = models.CharField(
        max_length=50,
        verbose_name='Registro do Responsável pelo Uso Externo'
        )
    
    email_responsible = models.EmailField(
        blank=True,
        verbose_name='Email do Uso Externo'
        )
    
    user = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Usuário do Uso Externo'
        )
    
    cpf_user = models.CharField(
        max_length=14,
        blank=True,
        verbose_name='CPF do Usuário do Uso Externo'
        )
    
    email_user = models.EmailField(
        blank=True,
        verbose_name='Email do Usuário do Uso Externo'
        )
    
    phone_user = models.CharField(
        max_length=16,
        validators=[Complementos.validator_contato],
        blank=True,
        verbose_name='Telefone do Usuário do Uso Externo'
        )
    
    date_renovation = models.DateField(
        verbose_name='Data de Renovação do Uso Externo'
        )
    class Meta:
        verbose_name = 'Uso Externo'
        verbose_name_plural = '6 - Usos Externos'

    def __str__(self):
        return self.description[:60]


'''ATRIBUIÇÃO DE BENS A USUÁRIOS'''

class AtribuicaoBem(models.Model):
    bem   = models.ForeignKey(
        BensPermanentes,
        on_delete=models.PROTECT,
        related_name='atribuicoes',
        verbose_name='Bem Permanente',
    )
    user  = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='bens_atribuidos',
        verbose_name='Usuário',
    )
    desde = models.DateField(
        auto_now_add=True,
        verbose_name='Atribuído desde',
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name='Atribuição ativa',
    )

    class Meta:
        verbose_name        = 'Atribuição de Bem'
        verbose_name_plural = '7 - Atribuições de Bens'

    def __str__(self):
        nome = self.user.get_full_name() or self.user.username
        return f'{nome} → Tombo {self.bem.tombo}'


'''HISTÓRICO DE MUDANÇAS'''

class HistoricoMudanca(models.Model):
    bem = models.ForeignKey(
        BensPermanentes,
        on_delete=models.PROTECT,
        related_name='historico_mudancas',
        verbose_name='Bem',
    )
    alterado_por = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='mudancas_realizadas',
        verbose_name='Alterado por',
    )
    data = models.DateTimeField(auto_now_add=True, verbose_name='Data da Alteração')
    justificativa = models.TextField(blank=True, verbose_name='Justificativa')
    # JSON: {"campo": {"label": "Rótulo", "de": "valor antigo", "para": "novo valor"}}
    campos = models.JSONField(verbose_name='Campos Alterados')

    class Meta:
        verbose_name        = 'Histórico de Mudança'
        verbose_name_plural = '9 - Histórico de Mudanças'
        ordering            = ['-data']

    def __str__(self):
        return f'#{self.pk} — Tombo {self.bem.tombo} em {self.data:%d/%m/%Y %H:%M}'


'''PERÍODO DE INVENTÁRIO'''

class PeriodoInventario(models.Model):
    descricao = models.CharField(
        max_length=100,
        verbose_name='Descrição',
    )
    inicio = models.DateField(
        verbose_name='Início',
    )
    fim = models.DateField(
        verbose_name='Fim',
    )

    class Meta:
        verbose_name        = 'Período de Inventário'
        verbose_name_plural = '8 - Períodos de Inventário'
        ordering            = ['-inicio']

    def __str__(self):
        return f'{self.descricao} ({self.inicio} — {self.fim})'

    @classmethod
    def em_andamento(cls):
        hoje = timezone.now().date()
        return cls.objects.filter(inicio__lte=hoje, fim__gte=hoje).exists()
    

class Catalogo(models.Model):
    efisco = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Código Efisco'
    )

    description = models.ForeignKey(
        Description,
        on_delete=models.PROTECT,
        related_name='catalogo_description',
        verbose_name='Descrição'
    )

    descricao = models.TextField(
        blank=True,
        verbose_name='Descrição Livre'
    )

    photo = models.ImageField(
        upload_to=caminho_catalogo,
        blank=True,
        null=True,
        verbose_name='Imagem do Catálogo'
    )

    value = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='Valor Unitário de Referência'
    )

    class Meta:
        verbose_name = 'Catálogo'
        verbose_name_plural = '10 - Catálogos'
        ordering = ['description__type__gruop', 'description']

    def __str__(self):
        return str(self.description)[:60]