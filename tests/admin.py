from django.contrib import admin
from .models import Item, Bloco, Setor
from .models import *

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
        'circunscricao_predio'
    )

    fieldsets=(
        ('Local', {
            'fiels': (
                'circunscricao_predio',
            )
        })
        
        ('Informações da UA', {
            'fields': (
                'ua', 
                'contato_ua',
                'email_ua',
            )
        })
        
        ('Informações do Responsável', {
            'fields': (
                'responsavel_ua',
                'mat_resp_ua',
            )
                
        })
    )


class BensPermanentesAdmin(admin.ModelAdmin):
    list_display = (
        'tombamento_legado',
        'numero_de_serie',
        'descricao_manual',
        'marca_fabricante',
        'modelo',
        'forma_de_ingresso',
        'nota_fiscal',
        'cpf_fornecedor',
        'cnpj_fornecedor',
        'data_aquisicao',
        'numero_do_processo',
        'numero_do_empenho',
        'valor_unitario',
        'qtde',
        'ua_atual',
        'valor_atual_do_bem',
        'classe',
        'subclasse',
        'subclasse_2',
        'subclasse_3',
        'venc_garantia',
        'nome_resp_uso_ext',
        'matricula_uso_ext'
        'contato_resp_uso_ext',
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
    
    fieldsets=(
        ('Informações do Bem', {
            'fields': (
                'tombamento_legado',
                'numero_de_serie',
                'modelo',
                'qtde'
            )
        })
        
        ('Detalhamento do Bem', {
            'fields': (
                'descricao_manual',
                'classe',
                'subclasse',
                'subclasse_2',
                'subclasse_3',
            )
        })
        
        ('Informações do Fornecedor', {
            'fields': (
                'marca_fabricante',
                'cpf_fornecedor',
                'cnpj_fornecedor',
            )
        })

        ('Informações da Compra', {
            'fields': (
                'numero_do_processo',
                'numero_do_empenho',
                'nota_fiscal',
                'valor_unitario',
                'data_aquisicao',
                'venc_garantia',
            )
        })

        ('Informações do Responsável de Uso Externo', {
            'fields': (
                'nome_resp_uso_ext',
                'matricula_resp_uso_ext'
                'contato_resp_uso_ext',
            )
        })
    )


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
                'grupo_consumo'
            )
        })
        
        ('Descrição do Bem', {
            'fields': (
                'validade',
                'custo_unit'
            )
        })
            
        ('Quantidade', {
            'fields': (
                'medida',
                'quantidade',
            )
        })
    )