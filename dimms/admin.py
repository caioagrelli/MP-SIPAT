from django.contrib import admin
from django.core.exceptions import ValidationError
from .models import *

# --- Informações Bens de Consumo DIMMS ---   
@admin.register(BensConsumo)
class BensConsumoAdmin(admin.ModelAdmin):
    list_display=(
        'efisco',
        'descricao_efisco',
        'medida',
        'grupo_consumo',
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

@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display=(
        'fornecedor',
        'cnpj_fornecedor',
        'contato_fornecedor',
        'email_fornecedor',
    )
    
    search_fields=(
        'fornecedor',
        'cnpj_fornecedor',
    )

    fieldsets=(
        ('Fornecedor', {
            'fields': (
                'fornecedor',
            )
        }),

        ('Dados do Fornecedor', {
            'fields': (
                'cnpj_fornecedor',
                'contato_fornecedor',
                'email_fornecedor',
            )
        }),
    )

@admin.register(Contrato)
class ContratoAdmin(admin.ModelAdmin):
    list_display=(
        'contrato',
        'fornecedor',
        'homologacao',
        'cs',
        'cod_liquidacao',
        'inicio_vigencia',
        'final_vigencia',
    )
 
    search_fields=(
        'contrato',
        'fornecedor__fornecedor',
        'homologacao',
        'cs',
        'cod_liquidacao',        
    )

    list_select_related =(
        'fornecedor',
        )

    autocomplete_fields =(
        'fornecedor',
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
    
@admin.register(Solicitacao)
class SolicitacaoAdmin(admin.ModelAdmin):
    list_display=(
        'request',
        'user_order',
        'data_order',
        'situation',
    )

    search_fields=(
        'request',
        'user_order',
        'situation',
    )
    
    fieldsets=(
        ('Informações da Requisição', {
            'fields': (
                'user_order',
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

@admin.register(SolicitacaoItens)
class SolicitacaoItensAdmin(admin.ModelAdmin):
    list_display=(
        'request_defendant',
        'item_order',
        'amont_order',
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
                'amont_order',
            )
        }),
    )
    class SolicitacaoAdmin(admin.ModelAdmin):
        def save_model(self, request, obj, form, change):
            if not obj.user_responsible_id:
                obj.user_responsible = request.user
            super().save_model(request, obj, form, change)

@admin.register(Tramitacao)
class TramitacaoAdmin(admin.ModelAdmin):
    list_display=(
        'request_update',
        'update',
        'date_update',
        'user_update',
    )
    
    search_fields=(
        'request_update',
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
                'observation_update',
            )
        }),
        
        ('Documentos Anexados', {
            'fields': (
                'documents_update',
            )
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.user_update_id:
            obj.user_update = request.user
        super().save_model(request, obj, form, change)