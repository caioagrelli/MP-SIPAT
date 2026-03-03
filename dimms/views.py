from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.shortcuts import redirect
from django.db.models import Q
from .models import *


@login_required
def homepage(request):
    query = request.GET.get('q', '').strip()

    itens = Estoque.objects.select_related('item_shock', 'locate').all()

    if query:
        itens = itens.filter(
            Q(item_shock__efisco__icontains=query) |
            Q(mark__icontains=query) |
            Q(description_manual__icontains=query) 
        )

    context = {
        'itens': itens,
        'total_itens': itens.count(),
        'query': query,
    }
    return render(request, 'dimms/homepage.html', context)

@login_required
def detail(request, pk):
    item = get_object_or_404(Estoque.objects.select_related("item_shock", "locate"), pk=pk)
    return render(request, 'dimms/detail.html', {
        'item': item
    })
