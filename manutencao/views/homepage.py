from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q
from django.shortcuts import render

from ..models import EstoqueManutencao


@login_required
@permission_required('manutencao.access_manutencao', raise_exception=True)
def homepage(request):
    query = request.GET.get('q', '').strip()
    grupo = request.GET.get('grupo', '').strip()

    itens = EstoqueManutencao.objects.select_related('locate').all()

    if query:
        itens = itens.filter(
            Q(efisco__icontains=query) |
            Q(descricao__icontains=query) |
            Q(mark__icontains=query)
        )

    if grupo:
        itens = itens.filter(grupo=grupo)

    grupos = EstoqueManutencao._meta.get_field('grupo').choices

    context = {
        'itens': itens,
        'total_itens': EstoqueManutencao.objects.count(),
        'sem_estoque': EstoqueManutencao.objects.filter(amount_shock=0).count(),
        'query': query,
        'grupos': grupos,
        'grupo_selected': grupo,
    }
    return render(request, 'manutencao/homepage.html', context)
