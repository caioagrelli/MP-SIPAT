from django.contrib import admin
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import *


# --- Informações sobre as Uas ---
@admin.register(CircunscricaoPredio) # (colocar só para atualizar todos os locais)
class CircunscricaoPredioAdmin(admin.ModelAdmin):
        list_display=(
            'local',
        )
        
        search_fields=(
            'local',
        ) 

@admin.register(InfoUA)
class InfoUaAdmin(admin.ModelAdmin):
    list_display=(
        'ua',
        'circunscricao_predio',
        'responsavel_ua',
        'mat_resp_ua',
        'contato_ua',
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
        '',
    )


# --- Localização Interna no DEMPAM ---
@admin.register(SetorDEMPAM)
class SetorDEMPAMAdmin(admin.ModelAdmin):
    list_display=(
        'setor',
    )
    
    search_fields=(
        'setor',
    )
    
    fieldsets=(
        ('Setor', {
            'fields': (
                'setor',
            )
        }),
    )
    
@admin.register(LocalizacaoDEMPAM)
class LocalizacaoDEMPAMAdmin(admin.ModelAdmin):
    list_display=(
        'setor_sala',
        'prateleira_pallet',
        'tipo_localizacao',
    )
    
    search_fields=(
        'setor_sala',
        'prateleira_pallet',
    )
    
    list_filter=(
        'setor_sala',
    )
    
    fieldsets=(
        ('Setor/Sala', {
            'fields': (
                'setor_sala',
            )
        }),
        
        ('Prateleira/Pallet', {
            'fields': (
                'prateleira_pallet',
                'tipo_localizacao',
            )
        }),
    )