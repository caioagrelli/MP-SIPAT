# Importações do Django
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta

# Importações do código
from .models import Estoque, SolicitacaoItens

# ====================================
# SERVICES DA DIMMS (BENS DE CONSUMO)
# ====================================



# função para calcular o consumo mensal de um bem
def recalcular_consumo(days=30):
    """
    Recalcula o consumo mensal de cada item de estoque com base
    nas solicitações dos últimos `days` dias.
    """
    hoje = timezone.now()
    limite = hoje - timedelta(days=days)

    # soma as quantidades por item de estoque
    consumos = (
        SolicitacaoItens.objects
        .filter(
            request_defendant__data_order__gte=limite,
            item_order__isnull=False,
            amount_order__isnull=False,
        )
        .values("item_order")
        .annotate(total=Sum("amount_order"))
    )

    # transforma em dicionário: {id_do_estoque: total}
    mapa_consumo = {
        item["item_order"]: item["total"] or 0
        for item in consumos
    }

    estoques_atualizados = []

    for estoque in Estoque.objects.all():
        novo_consumo = mapa_consumo.get(estoque.id, 0)

        if estoque.monthly_consumption != novo_consumo:
            estoque.monthly_consumption = novo_consumo
            estoques_atualizados.append(estoque)

    if estoques_atualizados:
        Estoque.objects.bulk_update(
            estoques_atualizados,
            ["monthly_consumption"]
        )

    return len(estoques_atualizados)