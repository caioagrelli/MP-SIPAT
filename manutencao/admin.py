from django.contrib import admin

from .models import EstoqueManutencao


@admin.register(EstoqueManutencao)
class EstoqueManutencaoAdmin(admin.ModelAdmin):
    list_display  = ('efisco', 'descricao', 'amount_shock', 'mark', 'locate', 'updated_at')
    list_filter   = ('grupo', 'medida', 'locate')
    search_fields = ('efisco', 'descricao', 'mark')
    readonly_fields = ('created_at', 'updated_at', 'updated_by')
