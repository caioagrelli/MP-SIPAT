from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.shortcuts import redirect
from django.db.models import Q
from .models import *


@login_required
def homepage(request):
    query = request.GET.get("q", "").strip()

    itens = Estoque.objects.select_related("item_shock", "locate").all()

    if query:
        itens = itens.filter(
            Q(description_manual__icontains=query) |
            Q(mark__icontains=query) |
            Q(item_shock__nome__icontains=query)  # ajuste se o campo for outro
        )

    context = {
        "itens": itens,
        "total_itens": itens.count(),
        "query": query,
    }
    return render(request, "dimms/homepage.html", context)


