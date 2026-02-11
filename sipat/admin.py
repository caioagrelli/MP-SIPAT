from django.contrib import admin
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import InfoUA, BensPermanentes, BensConsumo, CircunscricaoPredio, MovimentacoesConsumo, MovimentacoesPermanentes, SetorDEMPAM, LocalizacaoDEMPAM


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


# --- Informações Bens de Consumo DIMMS ---   
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
        'local_armazenamento'
    )
    
    search_fields=(
        'efisco',
        'marca',
        'grupo_consumo',
        'local_armazenamento'
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
        
        ('Localização no DEMPAM', {
            'fields': (
                'local_armazenamento',
            )
        }),
        
        ('Descrição do Bem', {
            'fields': (
                'validade',
                'custo_unit',
            )
        }),
        
        ('Foto do Item', {
            'fields': (
                'imagem_consumo',
            )
        }),
            
        ('Quantidade', {
            'fields': (
                'medida',
                'quantidade',
            )
        }),
    )


# --- Histórico de Movimentações---
@admin.register(MovimentacoesConsumo)
class  MovimentacoesConsumoAdmin(admin.ModelAdmin):
    list_display=(
        'item',
        'quantidade',
        'usuario',
        'acao',
        'data_hora',
    )

    search_fields=(
        'item__efisco',
        'usuario__username',
        'data_hora',
    )
    
    list_filter=(
        'acao',
    )
    
    readonly_fields=(
        'usuario', 
        'data_hora'
    )
    
    fieldsets =(
        ('Solicitações', {
            'fields': (
                'item',
                'acao',
                'quantidade',
            )
        }),
        
        ('Documentos', {
            'fields': (
                'anexo',
            )
        }),
    )

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        if change:
            raise ValidationError('Não edite solicitações. Crie uma nova :) ')
        
        obj.usuario = request.user
        item = obj.item
        
        if obj.acao == 'SAIDA':
            if obj.quantidade > item.quantidade:
                raise ValidationError('Saldo insuficiente para essa retirada.')
            else:
                item.quantidade -= obj.quantidade
        elif obj.acao == 'ENTRADA':
            item.quantidade += obj.quantidade
        else:
            raise ValidationError('Ação Inválida')
            
        item.save()
        super().save_model(request, obj, form, change)

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