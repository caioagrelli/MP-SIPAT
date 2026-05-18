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