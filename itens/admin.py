# itens/admin.py
from django.contrib import admin
from .models import Item, Bloco, Setor

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('numero_identificacao', 'nome', 'marca', 'modelo', 'categoria')
    search_fields = ('nome', 'numero_identificacao', 'descricao')

    list_filter = ('categoria', 'marca', 'estado_de_conservacao')


    fieldsets = (
        ('Identificação Principal', {
            'fields': ('numero_identificacao', 'nome', 'categoria', 'foto_do_bem', 'descricao')
        }),
        ('Detalhes Adicionais', {
            'fields': ('marca', 'modelo', 'estado_de_conservacao')
        }),
        ('Controle de Lote', {
            'fields': ('lote', 'bloco')
        }),
    )

@admin.register(Setor)
class SetorAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)

@admin.register(Bloco)
class BlocoAdmin(admin.ModelAdmin):
    # Agora a lista mostra o nome e a qual setor ele pertence
    list_display = ('nome', 'setor')
    search_fields = ('nome',)
    list_filter = ('setor',) # Adiciona um filtro rápido por setor
