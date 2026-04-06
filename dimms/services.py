# Importações do Django
from django.db.models import Sum
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP
from datetime import timedelta

# Importações do código
from .models import Estoque, SolicitacaoItens

# ====================================
# SERVICES DA DIMMS (BENS DE CONSUMO)
# ====================================



# função para calcular o consumo mensal de um bem
def recalcular_consumo():
    hoje = timezone.now()

    for estoque in Estoque.objects.all():
        if not estoque.created_at:
            estoque.monthly_consumption = 0
            estoque.save(update_fields=["monthly_consumption"])
            continue

        dias_desde_cadastro = max((hoje.date() - estoque.created_at.date()).days, 1)

        total_saida = (
            SolicitacaoItens.objects
            .filter(
                item_order=estoque,
                request_defendant__stock_deducted=True,
            )
            .aggregate(total=Sum("amount_order"))
            .get("total") or 0
        )

        consumo_mensal = (
            Decimal(total_saida) / Decimal(dias_desde_cadastro) * Decimal("30")
        ).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        estoque.monthly_consumption = int(consumo_mensal)
        estoque.save(update_fields=["monthly_consumption"])
