# Importações do Django
from django.contrib import admin
from django.core.exceptions import ValidationError

# importações código (Todo o models de uma vez)
from .models import *

# =================================
# ADMIN DA DIMMS (BENS DE CONSUMO)
# =================================



''' Informações dos Bens de Consumo''' 
@admin.register(BensConsumo)
class BensConsumoAdmin(admin.ModelAdmin):
    list_display=(
        'efisco',
        'descricao_efisco',
        'medida',
        'grupo_consumo',
        'preco_medio',
    )
    
    search_fields=(
        'efisco',
        'descricao_efisco'
        'grupo_consumo',
    )
    
    list_filter=(
        'grupo_consumo',
    )
    
    fieldsets=(
        ('Informações Do Bem', {
            'fields': (
                'efisco',
                'grupo_consumo',
            )
        }),
                                    
        ('Unidade de Medida', {
            'fields': (
                'medida',
            )
        }),
        
        ('Descrição', {
            'fields': (
                'descricao_efisco',                
            )
        }),
    )



''' Admin dos Artefatos '''
# Itens dos Artefatos (Tabela nos Artefatos)
class ItensArtifactsInline(admin.TabularInline):
    model = ItensArtifacts
    extra = 1
    autocomplete_fields = ['efisco']

# Fornecedores
@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'supplier',
        'cnpj_supplier',
        'contact_supplier',
        'email_supplier',
    )
    search_fields = (
        'supplier',
        'cnpj_supplier',
        'contact_supplier',
        'email_supplier',
    )
    ordering = ('supplier',)

# Artefatos 
@admin.register(Artifacts)
class ArtifactsAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'artifacts_code',
        'description',
        'state',
        'updated_at',
        'updated_by',
    )
    search_fields = (
        'artifacts_code',
        'description',
        'sei',
        'state',
    )
    list_filter = (
        'state',
        'updated_at',
    )
    readonly_fields = (
        'artifacts_code',
        'updated_at',
        'updated_by',
    )
    inlines = [ItensArtifactsInline]

# Itens dos Artefatos (Geral)
@admin.register(ItensArtifacts)
class ItensArtifactsAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'artifacts',
        'efisco',
        'amount',
        'value_max',
    )
    search_fields = (
        'artifacts__artifacts_code',
        'efisco__item_shock',
        'details',
    )
    list_filter = (
        'artifacts',
    )
    autocomplete_fields = (
        'artifacts',
        'efisco',
    )


''' Propostas '''
# Itens das Propostas
class ItensProposalInline(admin.TabularInline):
    model = ItensProposal
    extra = 1
    autocomplete_fields = ['item']
    fields = (
        'item',
        'details_proposal',
        'amount',
        'value',
        'state',
        'reason',
    )


@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'proposal_code',
        'supplier',
        'artifacts_proposal',
        'state',
    )
    search_fields = (
        'proposal_code',
        'supplier__supplier',
        'artifacts_proposal__artifacts_code',
        'state',
    )
    list_filter = (
        'state',
        'supplier',
        'artifacts_proposal',
    )
    readonly_fields = (
        'proposal_code',
    )
    autocomplete_fields = (
        'supplier',
        'artifacts_proposal',
    )
    inlines = [ItensProposalInline]


@admin.register(ItensProposal)
class ItensProposalAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'proposal_item',
        'item',
        'amount',
        'value',
        'state',
        'total_value',
    )
    search_fields = (
        'proposal_item__proposal_code',
        'item__efisco__item_shock',
        'details_proposal',
    )
    list_filter = (
        'state',
        'proposal_item',
    )
    autocomplete_fields = (
        'proposal_item',
        'item',
    )

    @admin.display(description='Valor Total')
    def total_value(self, obj):
        return obj.total_value


''' Saldo Ativo '''     # Desativado Temporariamente
# Contratos
'''@admin.register(Contrato)
class ContratoAdmin(admin.ModelAdmin):
    list_display=(
        'contrato',
        'supplier',
        'homologacao',
        'cs',
        'cod_liquidacao',
        'inicio_vigencia',
        'final_vigencia',
    )
 
    search_fields=(
        'contrato',
        'supplier__supplier',
        'homologacao',
        'cs',
        'cod_liquidacao',        
    )

    list_select_related =(
        'supplier',
        )

    autocomplete_fields =(
        'supplier',
        )
    
    ordering =(
        '-id',
        )

    fieldsets=(
        ('Fornecedor', {
            'fields': (
                'fornecedor',
            )
        }),
        
        ('Informações do Contrato', {
            'fields': (
                'contrato',
                'homologacao',
                'cs',
                'cod_liquidacao',     
            )
        }),
        
        ('Datas do Contrato', {
            'fields': (
                'inicio_vigencia',
                'final_vigencia',
            )
        })
    )
'''

# Saldo ativo
@admin.register(SaldoAtivo)
class SaldoAtivoAdmin(admin.ModelAdmin):
    list_display=(
        'contrato_saldo',
        'efisco',
        'descricao_manual',
        'marca',
        'saldo_disponivel',
        'cota',
    )
    
    search_fields=(
        'contrato_saldo__contrato',
        'efisco__efisco',
        'descricao_manual',
    )
    
    fieldsets=(
        ('Informações do Contrato', {
            'fields': (
                'contrato_saldo',
                'cota',
            )
        }),
        
        ('Informações do Bem', {
            'fields': (
                'efisco',                
                'quantidade_contrato',
                'marca',
                'descricao_manual',
            )
        }),
    )

# Aditivos de contrato
@admin.register(AditivoContrato)
class AditivoContratoAdmin(admin.ModelAdmin):
    list_display = ('numero', 'contrato', 'numero_empenho', 'valor_total', 'criado_por', 'criado_em')
    search_fields = ('numero', 'contrato__contrato', 'numero_empenho')

@admin.register(ItemAditivoContrato)
class ItemAditivoContratoAdmin(admin.ModelAdmin):
    list_display = ('aditivo', 'efisco', 'quantidade_acrescida', 'item_novo')
    search_fields = ('aditivo__numero', 'efisco__efisco')

# Solicitações do saldo ativo
@admin.register(SolicitacoesSaldoAtivo)
class SolicitacoesSaldoAtivoAdmin(admin.ModelAdmin):
    list_display=(
        'codigo',
        'status',
        'contrato',
    )
    
    search_fields=(
        'codigo',
        'status',
        'contrato',
    )

    fieldsets=(
        ('Contrato', {
            'fields': (
                'contrato',
            )
        }),
        
        ('Andamento', {
            'fields': (
                'status',
            )
        }),
    )

# Itens solicitados por cada solcitação 
@admin.register(ItensSolicitados)
class ItensSolicitadosAdmin(admin.ModelAdmin):
    list_display=(
        'solicitacao',
        'bem',
        'quantidade'
    )
    
    search_fields=(
        'solicitacao',
        'bem',
    )
    
    fieldsets=(
        ('Dados do envio', {
            'fields': (
                'solicitacao',
            )
        }),
        
        ('Dados do Bem', {
            'fields': (
                'bem',
                'quantidade',
            )
        }),
    )

# Bens que realmente foram enviados 
@admin.register(BensEnviados)
class BensEnviadosAdmin(admin.ModelAdmin):
    list_display=(
        'item_enviado',
        'quantidade_enviada',
    )
    
    search_fields=(
        'item_enviado',
    )
    
    fieldsets = (        
        ('Informações do Bem Enviado', {
            'fields': (
                'item_enviado',
                'quantidade_enviada',
            )
        }),
    )

 
''' Estoque '''
#estoque principal
@admin.register(Estoque)
class EstoqueAdmin(admin.ModelAdmin):
    list_display=(
        'item_shock',
        'description_manual',
        'mark',
        'amount_shock',
        'locate',
    )
    
    search_fields=(
        'item_shock'
        'description_manual',
        'mark',
        'locate',
    )
    
    fieldsets=(
        ('Informações do Bem', {
            'fields': (
                'item_shock',
                'amount_shock',
                'description_manual',
                'mark',
                'validity',
                'essential', 
                'monthly_consumption',
            )
        }),
        
        ('Local de Armazenamento', {
            'fields': (
                'locate',
            )
        }),
        
        ('Fotos do Bem', {
            'fields': (
                'photo',
            )
        }), 
        )


''' Tramitações do estoque  '''
# Solicitação
@admin.register(Solicitacao)
class SolicitacaoAdmin(admin.ModelAdmin):
    list_display=(
        'request_code',
        'ua_order',
        'data_order',
        'situation',
    )

    search_fields=(
        'request_code',
        'user_order',
        'situation',
    )

    # 'situation' só pode mudar via Tramitação (dimms/models/solicitacoes.py) —
    # editar direto aqui pula a baixa automática de estoque.
    readonly_fields=(
        'situation',
    )

    fieldsets=(
        ('Informações da Requisição', {
            'fields': (
                'ua_order',
                'user_order',
                'situation',
            )
        }),
        
        ('Observação', {
            'fields': (
                'observation_order',
            )
        }),
        
        ('Documento Anexado', {
            'fields': (
                'documents_order',
            )
        }),

    )

# Itens de cada Solicitação
@admin.register(SolicitacaoItens)
class SolicitacaoItensAdmin(admin.ModelAdmin):
    list_display=(
        'request_defendant',
        'item_order',
        'amount_order',
    )
    
    search_fields=(
        'request_defendant',
        'item_order',
    )
    
    fieldsets=(
        ('Requisição', {
            'fields': (
                'request_defendant',
            )
        }),
        
        ('Dados Item', {
            'fields': (
                'item_order',
                'amount_order',
            )
        }),
    )
    class SolicitacaoAdmin(admin.ModelAdmin):
        def save_model(self, request, obj, form, change):
            if not obj.user_responsible_id:
                obj.user_responsible = request.user
            super().save_model(request, obj, form, change)

# Atualizações em cada solicitação
@admin.register(Tramitacao)
class TramitacaoAdmin(admin.ModelAdmin):
    list_display=(
        'request_update',
        'update',
        'date_update',
        'responsible_update',
        'user_update',
    )
    
    search_fields=(
        'request_update',
        'responsible_update',
        'update',
        'user_update',
    )
    
    fieldsets=(
        ('Requisição', {
            'fields': (
                'request_update',
            )
        }),
        
        ('Dados da Requisição', {
            'fields': (
                'update',
                'responsible_update',
                'observation_update',
            )
        }),
        
        ('Documentos Anexados', {
            'fields': (
                'documents_update',
            )
        }),
        
        ('Foto da Atualização', {
            'fields': (
                'photo_update',
            )
        })
        )
    
    def save_model(self, request, obj, form, change):
        if not obj.user_update_id:
            obj.user_update = request.user
        super().save_model(request, obj, form, change)

@admin.register(CatalogoConsumo)
class CatalogoConsumoAdmin(admin.ModelAdmin):
    list_display  = ('description', 'marca_ou_dash', 'grupo_consumo', 'medida', 'ativo')
    list_filter   = ('grupo_consumo', 'ativo')
    search_fields = ('description', 'mark')
    list_editable = ('ativo',)

    def marca_ou_dash(self, obj):
        return obj.mark or '—'
    marca_ou_dash.short_description = 'Marca'


@admin.register(SolicitacaoCatalogoConsumo)
class SolicitacaoCatalogoConsumoAdmin(admin.ModelAdmin):
    list_display  = ('codigo', 'solicitante', 'ua_destino', 'data', 'status')
    list_filter   = ('status',)
    search_fields = ('codigo', 'solicitante__username', 'solicitante__first_name')
    readonly_fields = ('codigo', 'data', 'data_decisao')


@admin.register(ItemSolicitacaoCatalogoConsumo)
class ItemSolicitacaoCatalogoConsumoAdmin(admin.ModelAdmin):
    list_display  = ('solicitacao', 'catalogo', 'quantidade')
    search_fields = ('solicitacao__codigo', 'catalogo__description')


''' Acompanhamentos SEI '''
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display  = ('name', 'color', 'created_by', 'created_at')
    search_fields = ('name',)
    ordering = ('name',)


class SeiUpdateInline(admin.TabularInline):
    model = SeiUpdate
    extra = 1
    fields = ('text', 'date', 'user')


@admin.register(Sei)
class SeiAdmin(admin.ModelAdmin):
    list_display  = ('sei_number', 'subject', 'description', 'status', 'user', 'created_at', 'updated_at')
    list_filter   = ('status', 'subject')
    search_fields = ('sei_number', 'description', 'subject__name')
    autocomplete_fields = ('subject',)
    readonly_fields = ('created_at', 'updated_at')
    inlines = [SeiUpdateInline]


@admin.register(SeiUpdate)
class SeiUpdateAdmin(admin.ModelAdmin):
    list_display  = ('sei', 'date', 'user', 'created_at')
    list_filter   = ('date',)
    search_fields = ('sei__sei_number', 'text')
    autocomplete_fields = ('sei',)


''' Inventário mensal de estoque '''
@admin.register(PeriodoInventarioConsumo)
class PeriodoInventarioConsumoAdmin(admin.ModelAdmin):
    list_display  = ('__str__', 'aberto', 'total_conferidos', 'total_itens', 'criado_por')
    list_filter   = ('aberto', 'ano')


@admin.register(ConferenciaEstoque)
class ConferenciaEstoqueAdmin(admin.ModelAdmin):
    list_display  = ('item', 'periodo', 'quantidade_conferida', 'localizacao_conferida', 'conferido_por', 'conferido_em')
    list_filter   = ('periodo',)
    search_fields = ('item__item_shock__efisco', 'item__description_manual')
    autocomplete_fields = ('item',)

