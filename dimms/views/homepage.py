# Importação Django (acabaram as minhas piadas - Desculpa)
from django.shortcuts import render
from django.db.models import Q
from django.contrib.auth.decorators import login_required


# Importações do código
from ..models import Estoque, BensConsumo

# ===================================================
# CAMPOS DESTINADOS PARA GERENCIAR PÁGINAS INICIAIS
# ===================================================


''' Homepage '''
# Página Principail
def homepage(request):

    query = request.GET.get('q', '').strip()
    grupo = request.GET.get('grupo', '').strip()

    itens = Estoque.objects.select_related('item_shock', 'locate').all()

    # Busca
    if query:
        itens = itens.filter(
            Q(item_shock__efisco__icontains=query) |
            Q(mark__icontains=query) |
            Q(description_manual__icontains=query)
        )

    # Filtro por grupo
    if grupo:
        itens = itens.filter(item_shock__grupo_consumo=grupo)

    grupos = BensConsumo._meta.get_field("grupo_consumo").choices

    # itens essenciais
    item_essential = itens.filter(essential=True)
    
    # estoque baixo 
    estoque_baixo = [item for item in itens if item.low_stock]
    alerta_vencimento = [item for item in itens if item.alerta_vencimento]

    # ordenar alerta_vencimento pela data mais próxima / vencida no topo 
    alerta_vencimento = sorted(alerta_vencimento, key=lambda x: x.validity)

    # ordenar estoque_baixo pelos dias restantes, do maior para o menor
    estoque_baixo = sorted(estoque_baixo, key=lambda x: x.duration, reverse=True)

    context = {
        'itens': itens,
        'total_itens': itens.count(),
        'query': query,
        'grupos': grupos,
        'grupo_selected': grupo,
        'item_essential': item_essential,
        'estoque_baixo': estoque_baixo,
        'alerta_vencimento': alerta_vencimento,
    }

    return render(request, 'dimms/homepage.html', context)


''' Páginas de Alertas '''
# Estoque Baixo
@login_required
def low_stock(request):
    itens = (
        Estoque.objects
        .select_related('item_shock')
        .filter(monthly_consumption__isnull=False)
        .order_by('description_manual')
    )

    estoque_baixo = []

    for item in itens:
        if item.low_stock:
            estoque_baixo.append(item)

    context = {
        'estoque_baixo': estoque_baixo,
    }

    return render(request, 'dimms/alerts/low_stock.html', context)

# Itens Essenciais 
@login_required 
def essential(request):

    itens = Estoque.objects.select_related(
        'item_shock',
        'locate'
    ).filter(essential=True)

    context = {
        'itens': itens,
        'total_itens': itens.count(),
    }

    return render(
        request,
        'dimms/alerts/essential.html',
        context
    )

# Itens perto do vencimento
@login_required    
def expiration_alert(request):
    itens = (
        Estoque.objects
        .select_related('item_shock')
        .filter(validity__isnull=False)
        .order_by('validity', 'description_manual')
    )

    alerta_vencimento = []

    for item in itens:
        if item.alerta_vencimento:
            alerta_vencimento.append(item)

    context = {
        'alerta_vencimento': alerta_vencimento,
    }

    return render(request, 'dimms/alerts/expiration_alert.html', context)