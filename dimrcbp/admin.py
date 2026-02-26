from django.contrib import admin
from django.core.exceptions import ValidationError
from .models import *

# --- Informações Bens Permanentes DIMRCBP --
@admin.register(BensPermanentes)
class BensPermanentesAdmin(admin.ModelAdmin):
    list_display =(
        'tombamento_legado',
        'descricao_manual',
        'modelo',
        'data_aquisicao',
        'ua_atual',
        'valor_unitario',
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
                'ua_atual',
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
        
        ('Foto do Bem', {
        'fields': (
            'imagem_permanente',
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

@admin.register(MovimentacoesPermanentes)
class MovimentacoesPermanentesAdmin(admin.ModelAdmin):
    list_display=(
        'tombo',
        'acao',
        'origem',
        'destino',
        'nome_resp_uso_ext',
        'usuario',
        'data_hora',
    )

    ordering = (
                '-id',
                )
   
    search_fields=(
        'tombo',
        'usuario_username',
        'data_hora',
    )
    
    
    list_filter=(
        'acao',
    )
    
    
    readonly_fields=(
        'usuario',
        'data_hora',
    )
    
    
    fieldsets=(
        ('SEI da Movimentação', {
            'fields': (
                'sei',
            )
        }),
        
        ('Movimentação', {
            'fields': (
                'tombo',
                'acao',
                'destino'
            )
        }),
        
        ('Documentos', {
            'fields': (
                'anexo',
            )
        }),
        
        ('Informações Uso Externo', {
            'fields': (
                'nome_resp_uso_ext',
                'matricula_resp_uso_ext',
                'contato_resp_uso_ext',
            )
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if change:
            raise ValidationError('Não Edite Movimentações, crie uma nova :) ')
        
        obj.usuario = request.user
        bem = obj.tombo        
        obj.origem = bem.ua_atual

        if obj.destino ==  obj.origem:
            raise ValidationError('O Destino não pode ser igual à Origem :(')
        
        bem.ua_atual = obj.destino
        bem.save()
        
        return super().save_model(request, obj, form, change)       


