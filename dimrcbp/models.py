# Importações do Django
from localflavor.br.models import BRCNPJField
from django.core.validators import RegexValidator
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

# Importações do codigo
from .utils import *
from dempam.models import InfoUA, LocalizacaoDEMPAM

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
        blank=True,
        null=True,
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

    locate = models.ForeignKey(
        LocalizacaoDEMPAM,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='bens_permanentes',
        verbose_name='Localização (Pallet/Prateleira)',
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

    cpf_responsible = models.CharField(
        max_length=14,
        blank=True,
        verbose_name='CPF do Responsável pelo Uso Externo'
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
        return f'Tombo {self.tombo_id} — {self.responsible}'


'''ATRIBUIÇÃO DE BENS'''
# Atribuição de Bens a Usuários
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


def sincronizar_atribuicao(bem, ua):
    """Desativa atribuições ativas do bem e cria uma nova para o gestor da UA (se houver)."""
    AtribuicaoBem.objects.filter(bem=bem, ativo=True).update(ativo=False)
    gestor = getattr(ua, 'gestor', None) if ua else None
    if gestor:
        AtribuicaoBem.objects.create(bem=bem, user=gestor, ativo=True)


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

    @classmethod
    def get_periodo_ativo(cls):
        hoje = timezone.now().date()
        return cls.objects.filter(inicio__lte=hoje, fim__gte=hoje).first()

# Registro do bem em um período de inventário — um bem só pode ser registrado uma vez por inventário
class Inventario(models.Model):
    n_inventario = models.ForeignKey(
        PeriodoInventario,
        on_delete=models.PROTECT,
        related_name='n_inventarios',
        verbose_name='Período de Inventário',
    )

    bem = models.ForeignKey(
        BensPermanentes,
        on_delete=models.PROTECT,
        related_name='inventarios',
        verbose_name='Bem',
    )

    photo = models.ImageField(
        upload_to=caminho_inventario,
        blank=True,
        null=True,
        verbose_name='Foto do Inventário',
    )

    observation = models.TextField(
        blank=True,
        verbose_name='Observação do Inventário',
    )

    situation = models.CharField(
        max_length=20,
        choices=SituacaoInventario.choices,
        verbose_name='Situação no Inventário',
    )

    registrado_por = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='registros_inventario',
        verbose_name='Registrado por',
    )

    data_registro = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data do Registro',
    )

    class Meta:
        verbose_name        = 'Registro de Inventário'
        verbose_name_plural = '10 - Registros de Inventário'
        ordering            = ['-n_inventario__inicio', 'bem__tombo']
        constraints = [
            models.UniqueConstraint(
                fields=['n_inventario', 'bem'],
                name='unique_bem_por_inventario',
            )
        ]

    def __str__(self):
        return f'{self.n_inventario} — Tombo {self.bem.tombo}'

    

'''SOLICITAÇÕES DO CATÁLOGO (CARRINHO)'''

class SolicitacaoCatalogo(models.Model):
    codigo = models.CharField(
        max_length=30, unique=True, editable=False, verbose_name='Código',
    )
    
    solicitante = models.ForeignKey(
        User, on_delete=models.PROTECT,
        related_name='solicitacoes_catalogo', verbose_name='Solicitante',
    )
    
    ua_destino = models.ForeignKey(
        InfoUA, on_delete=models.PROTECT,
        related_name='solicitacoes_catalogo', verbose_name='UA Destino',
    )
    
    status = models.CharField(
        max_length=15,
        choices=StatusSolicitacaoCatalogo.choices,
        default=StatusSolicitacaoCatalogo.pendente,
        verbose_name='Status',
    )
    
    data = models.DateTimeField(auto_now_add=True, verbose_name='Data')
    
    observacao = models.TextField(blank=True, verbose_name='Observação')
    
    obs_decisao = models.TextField(blank=True, verbose_name='Obs. Decisão')
    
    decidido_por = models.ForeignKey(
        User, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='decisoes_catalogo', verbose_name='Decidido por',
    )
    
    data_decisao = models.DateTimeField(null=True, blank=True, verbose_name='Data Decisão')

    class Meta:
        verbose_name        = 'Solicitação Catálogo'
        verbose_name_plural = '13 - Solicitações Catálogo'
        ordering            = ['-data']

    def save(self, *args, **kwargs):
        if not self.codigo:
            salvar_com_codigo_sequencial(self, 'codigo', 'STC', super().save, *args, **kwargs)
        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return self.codigo

    @property
    def total_itens(self):
        return self.itens.count()

    @property
    def atendida(self):
        return self.itens.filter(bem_atribuido__isnull=False).count() == self.itens.count()


class ItemSolicitacaoCatalogo(models.Model):
    solicitacao = models.ForeignKey(
        SolicitacaoCatalogo, on_delete=models.CASCADE,
        related_name='itens', verbose_name='Solicitação',
    )

    catalogo = models.ForeignKey(
        'Catalogo', on_delete=models.PROTECT,
        related_name='itens_solicitados', verbose_name='Item do Catálogo',
    )

    observacao = models.TextField(blank=True, verbose_name='Observação do Item')

    bem_atribuido = models.ForeignKey(
        BensPermanentes, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='atribuicoes_catalogo', verbose_name='Bem Atribuído',
    )

    class Meta:
        verbose_name        = 'Item Solicitação Catálogo'
        verbose_name_plural = '14 - Itens Solicitação Catálogo'

    def __str__(self):
        return f'{self.solicitacao} → {self.catalogo}'


'''TRANSFERÊNCIA BEM PERMANENTE'''

class SolicitacaoTransferencia(models.Model):
    codigo = models.CharField(
        max_length=30,
        unique=True,
        editable=False,
        verbose_name='Código',
    )

    bem = models.ForeignKey(
        BensPermanentes,
        on_delete=models.PROTECT,
        related_name='solicitacoes_transferencia',
        verbose_name='Bem',
    )

    ua_destino = models.ForeignKey(
        InfoUA,
        on_delete=models.PROTECT,
        related_name='solicitacoes_recebimento',
        verbose_name='UA Destino',
    )

    solicitante = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='solicitacoes_transferencia',
        verbose_name='Solicitante',
    )

    data = models.DateTimeField(auto_now_add=True, verbose_name='Data da Solicitação')

    motivo = models.TextField(verbose_name='Motivo / Justificativa')

    status = models.CharField(
        max_length=15,
        choices=StatusSolicitacaoTransferencia.choices,
        default=StatusSolicitacaoTransferencia.pendente,
        verbose_name='Status',
    )

    obs_decisao = models.TextField(blank=True, verbose_name='Observação da Decisão')

    decidido_por = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='decisoes_transferencia',
        verbose_name='Decidido por',
    )

    data_decisao = models.DateTimeField(null=True, blank=True, verbose_name='Data da Decisão')

    class Meta:
        verbose_name        = 'Solicitação de Transferência'
        verbose_name_plural = '11 - Solicitações de Transferência'
        ordering            = ['-data']

    def save(self, *args, **kwargs):
        if not self.codigo:
            salvar_com_codigo_sequencial(self, 'codigo', 'STF', super().save, *args, **kwargs)
        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return self.codigo

class MovimentacaoBem(models.Model):
    codigo = models.CharField(
        max_length=30,
        unique=True,
        editable=False,
        verbose_name='Código',
    )

    bem = models.ForeignKey(
        BensPermanentes,
        on_delete=models.PROTECT,
        related_name='movimentacoes',
        verbose_name='Bem',
    )

    ua_origem = models.ForeignKey(
        InfoUA,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='saidas_movimentacao',
        verbose_name='UA Origem',
    )

    ua_destino = models.ForeignKey(
        InfoUA,
        on_delete=models.PROTECT,
        related_name='entradas_movimentacao',
        verbose_name='UA Destino',
    )

    responsavel = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='movimentacoes_realizadas',
        verbose_name='Responsável',
    )

    data = models.DateTimeField(auto_now_add=True, verbose_name='Data da Movimentação')

    motivo = models.TextField(blank=True, verbose_name='Motivo')

    solicitacao = models.OneToOneField(
        SolicitacaoTransferencia,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='movimentacao',
        verbose_name='Solicitação Origem',
    )

    class Meta:
        verbose_name        = 'Movimentação de Bem'
        verbose_name_plural = '12 - Movimentações de Bens'
        ordering            = ['-data']

    def save(self, *args, **kwargs):
        if not self.codigo:
            salvar_com_codigo_sequencial(self, 'codigo', 'TRF', super().save, *args, **kwargs)
        else:
            super().save(*args, **kwargs)

        # Atualiza o histórico de UAs do bem
        try:
            hist = self.bem.history_tombo
            hist.penultimate_ua   = hist.last_ua
            hist.penultimate_year = hist.last_year
            hist.last_ua          = hist.current_ua
            hist.last_year        = hist.current_year
            hist.current_ua       = self.ua_destino
            hist.current_year     = timezone.now().year
            hist.save()
        except HistoryUas.DoesNotExist:
            HistoryUas.objects.create(
                tombo=self.bem,
                current_ua=self.ua_destino,
                current_year=timezone.now().year,
            )

        sincronizar_atribuicao(self.bem, self.ua_destino)

        HistoricoMudanca.objects.create(
            bem=self.bem,
            alterado_por=self.responsavel,
            justificativa=self.motivo or f'Transferência {self.codigo}',
            campos={'ua_destino': str(self.ua_destino)},
        )

    def __str__(self):
        return self.codigo

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