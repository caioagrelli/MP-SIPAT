from django.contrib import admin
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
    list_display = (
        'codigo',
        'sigla',
        'ua',
        'nivel',
        'parent',
        'circunscricao_predio',
        'responsavel_ua',
    )

    search_fields = (
        'ua',
        'sigla',
        'codigo',
        'responsavel_ua',
        'email_ua',
    )

    list_filter = (
        'nivel',
        'circunscricao_predio',
    )

    autocomplete_fields = (
        'circunscricao_predio',
        'parent',
    )

    fieldsets = (
        ('Hierarquia', {
            'fields': (
                'codigo',
                'sigla',
                'nivel',
                'parent',
            )
        }),

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
                'gestor',
            )
        }),
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
    
@admin.register(Aviso)
class AvisoAdmin(admin.ModelAdmin):
    list_display = (
        'titulo',
        'autor',
        'data_publicacao',
        'ativo',
    )

    list_filter = (
        'ativo',
    )

    search_fields = (
        'titulo',
        'mensagem',
    )


@admin.register(ConfiguracaoPainelTV)
class ConfiguracaoPainelTVAdmin(admin.ModelAdmin):
    list_display = (
        'video_url',
        'atualizado_por',
        'atualizado_em',
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