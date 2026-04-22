from django.contrib import admin
from .models import *


''' CLASSIFICAÇÃO DOS BENS PERMANENTES '''

@admin.register(Groups)
class GroupsAdmin(admin.ModelAdmin):
    list_display = (
        'group',
    )

    search_fields = (
        'group',
    )

    fieldsets = (
        ('Grupo', {
            'fields': (
                'group',
            )
        }),
    )


@admin.register(Type)
class TypeAdmin(admin.ModelAdmin):
    list_display = (
        'type',
        'gruop',
    )

    search_fields = (
        'type',
    )

    list_filter = (
        'gruop',
    )

    autocomplete_fields = (
        'gruop',
    )

    fieldsets = (
        ('Classificação', {
            'fields': (
                'gruop',
                'type',
            )
        }),
    )


@admin.register(Description)
class DescriptionAdmin(admin.ModelAdmin):
    list_display = (
        'description',
        'type',
        'classification',
        'subclassification',
        'color',
        'size',
        'btu_hp',
    )

    search_fields = (
        'description',
        'classification',
        'subclassification',
    )

    list_filter = (
        'type',
        'color',
    )

    autocomplete_fields = (
        'type',
    )

    fieldsets = (
        ('Descrição', {
            'fields': (
                'type',
                'description',
            )
        }),

        ('Classificação', {
            'fields': (
                'classification',
                'subclassification',
            )
        }),

        ('Características', {
            'fields': (
                'color',
                'size',
                'btu_hp',
            )
        }),
    )


''' FORNECEDORES '''

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'cnpj',
        'email',
        'phone',
        'Responsible',
    )

    search_fields = (
        'name',
        'cnpj',
        'email',
        'Responsible',
    )

    fieldsets = (
        ('Fornecedor', {
            'fields': (
                'name',
                'cnpj',
            )
        }),

        ('Contato', {
            'fields': (
                'email',
                'phone',
                'Responsible',
            )
        }),
    )


''' BENS PERMANENTES '''

@admin.register(BensPermanentes)
class BensPermanentesAdmin(admin.ModelAdmin):
    list_display = (
        'tombo',
        'description',
        'mark',
        'model',
        'state',
        'situacion',
        'acquisition_date',
        'value',
    )

    search_fields = (
        'tombo',
        'description__description',
        'mark',
        'model',
        'n_series',
        'n_empenho',
        'n_process',
    )

    list_filter = (
        'state',
        'situacion',
        'entry_method',
        'modality',
    )

    fieldsets = (
        ('Identificação', {
            'fields': (
                'tombo',
                'description',
                'mark',
                'model',
                'n_series',
                'photo',
            )
        }),

        ('Estado', {
            'fields': (
                'state',
                'situacion',
            )
        }),

        ('Aquisição', {
            'fields': (
                'acquisition_date',
                'value',
                'entry_method',
                'modality',
                'n_empenho',
                'n_process',
                'supllier',
            )
        }),
    )


@admin.register(HistoryUas)
class HistoryUasAdmin(admin.ModelAdmin):
    list_display = (
        'tombo',
        'current_ua',
        'current_year',
        'current_responsible',
    )

    search_fields = (
        'current_responsible',
        'current_registration',
        'last_responsible',
        'last_registration',
    )

    list_filter = (
        'current_ua',
        'last_ua',
    )

    autocomplete_fields = (
        'tombo',
        'current_ua',
        'last_ua',
        'penultimate_ua',
        'third_last_ua',
    )

    fieldsets = (
        ('Bem Permanente', {
            'fields': (
                'tombo',
            )
        }),

        ('UA Atual', {
            'fields': (
                'current_ua',
                'current_year',
                'current_responsible',
                'current_registration',
            )
        }),

        ('UA Anterior', {
            'fields': (
                'last_ua',
                'last_year',
                'last_responsible',
                'last_registration',
            )
        }),

        ('UA Penúltima', {
            'fields': (
                'penultimate_ua',
                'penultimate_year',
                'penultimate_responsible',
                'penultimate_registration',
            )
        }),

        ('UA Antepenúltima', {
            'fields': (
                'third_last_ua',
                'third_last_year',
            )
        }),
    )


@admin.register(MovimentacoesPermanentes)
class MovimentacoesPermanentesAdmin(admin.ModelAdmin):
    list_display = (
        'codigo',
        'tombo',
        'acao',
        'origem',
        'destino',
        'usuario',
        'data_hora',
    )

    ordering = ('-id',)

    search_fields = (
        'codigo',
        'tombo__tombo',
        'nome_resp_uso_ext',
        'matricula_resp_uso_ext',
        'sei',
    )

    list_filter = (
        'acao',
    )

    readonly_fields = (
        'usuario',
        'data_hora',
        'origem',
    )

    autocomplete_fields = (
        'tombo',
        'destino',
    )

    fieldsets = (
        ('SEI da Movimentação', {
            'fields': (
                'sei',
                'codigo',
            )
        }),

        ('Movimentação', {
            'fields': (
                'tombo',
                'acao',
                'origem',
                'destino',
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

        ('Registro', {
            'fields': (
                'usuario',
                'data_hora',
            )
        }),
    )


@admin.register(UseExternal)
class UseExternalAdmin(admin.ModelAdmin):
    list_display = (
        'tombo',
        'responsible',
        'registration_responsible',
        'user',
        'date_renovation',
    )

    search_fields = (
        'responsible',
        'registration_responsible',
        'user',
        'cpf_user',
        'email_responsible',
        'email_user',
    )

    list_filter = (
        'date_renovation',
    )

    autocomplete_fields = (
        'tombo',
    )

    fieldsets = (
        ('Bem Permanente', {
            'fields': (
                'tombo',
            )
        }),

        ('Responsável pelo Uso Externo', {
            'fields': (
                'responsible',
                'registration_responsible',
                'contact_responsible',
                'email_responsible',
            )
        }),

        ('Usuário', {
            'fields': (
                'user',
                'cpf_user',
                'email_user',
                'phone_user',
            )
        }),

        ('Vigência', {
            'fields': (
                'date_renovation',
            )
        }),
    )
