from django.contrib import admin
from .models import InfoUA, BensPermanentes, BensConsumo, Locais

@admin.register(Locais)
class LocaisAdmin(admin.ModelAdmin):
        list_display=(
            'local',
        )
        
        search_fields=(
            'local',
        )
    
    
        

@admin.register(InfoUA)
class InfoUaAdmin(admin.ModelAdmin):
    list_display=(
        'circunscricao_predio',
        'ua',
        'contato_ua',
        'responsavel_ua',
        'mat_resp_ua',
        'email_ua',
    )

    search_fields=(
        'circunscricao_predio',
        'ua',
        'contato_ua',
        'responsavel_ua',
        'mat_resp_ua',
        'email_ua',
    )

    list_filter=(
        'circunscricao_predio',
    )
    
    autocomplete_fields=(
        'circunscricao_predio',
    )

    fieldsets=(
        ('Local', {
            'fields': (
                'circunscricao_predio',
            )
        }),
        
        ('Informações da UA', {
            'fields': (
                'ua', 
                'contato_ua',
                'email_ua',
            )
        }),
        
        ('Informações do Responsável', {
            'fields': (
                'responsavel_ua',
                'mat_resp_ua',
            )
                
        }),
    )

@admin.register(BensPermanentes)
class BensPermanentesAdmin(admin.ModelAdmin):
    list_display = (
        'tombamento_legado',
        'marca_fabricante',
        'modelo',
        'nota_fiscal',
        'cpf_fornecedor',
        'data_aquisicao',
        'valor_unitario',
        'qtde',
        'ua_atual',
        'valor_atual_do_bem',
    )
    
    search_fields=(
        'tombamento_legado',
        'ua_atual',
        'nome_resp_uso_ext',
        'marca_fabricante',
        'modelo',
        'numero_do_processo',
        'numero_do_empenho',
        'numero_de_serie',
    )

    list_filter=(
        'ua_atual',        
    )
    
    autocomplete_fields=(
        'ua_atual',
    )
    
    fieldsets=(
        ('Informações do Bem', {
            'fields': (
                'tombamento_legado',
                'numero_de_serie',
                'modelo',
                'qtde',
                'matricula_responsavel',

            )
        }),
        
        ('Detalhamento do Bem', {
            'fields': (
                'descricao_manual',
                'classe',
                'subclasse',
                'subclasse_2',
                'subclasse_3',
            )
        }),
        
        ('Informações do Fornecedor', {
            'fields': (
                'marca_fabricante',
                'cpf_fornecedor',
                'cnpj_fornecedor',
            )
        }),

        ('Informações da Compra', {
            'fields': (
                'numero_do_processo',
                'numero_do_empenho',
                'nota_fiscal',
                'valor_unitario',
                'data_aquisicao',
                'venc_garantia',
            )
        }),

        ('Informações do Responsável de Uso Externo', {
            'fields': (
                'nome_resp_uso_ext',
                'matricula_resp_uso_ext',
                'contato_resp_uso_ext',
            )
        }),
    )

@admin.register(BensConsumo)
class BensConsumoAdmin(admin.ModelAdmin):
    list_display=(
        'efisco',
        'marca',
        'validade',
        'custo_unit',
        'medida',
        'quantidade',
        'grupo_consumo',
    )
    
    search_fields=(
        'efisco',
        'marca',
        'grupo_consumo',
    )
    
    list_filter=(
        'grupo_consumo',
    )
    
    fieldsets=(
        ('Informações Do Bem', {
            'fields': (
                'efisco',
                'marca',
                'grupo_consumo',
            )
        }),
        
        ('Descrição do Bem', {
            'fields': (
                'validade',
                'custo_unit',
            )
        }),
            
        ('Quantidade', {
            'fields': (
                'medida',
                'quantidade',
            )
        }),
    )