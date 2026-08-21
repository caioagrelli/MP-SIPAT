from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.shortcuts import render
from django.utils import timezone

from dimrcbp.models import BensPermanentes

ENTRADAS_POR_PAGINA = 30


# ──────────────────────────────────────────────────────────────────────────────
# ENTRADAS — bens permanentes adicionados ao sistema, filtrados por ano de aquisição
# ──────────────────────────────────────────────────────────────────────────────

@login_required
@permission_required('dimrcbp.view_benspermanentes', raise_exception=True)
def entradas(request):
    ano_atual = timezone.now().year

    anos_disponiveis = sorted({
        d.year for d in
        BensPermanentes.objects.exclude(acquisition_date__isnull=True).dates('acquisition_date', 'year')
    }, reverse=True)
    if ano_atual not in anos_disponiveis:
        anos_disponiveis.insert(0, ano_atual)

    try:
        ano = int(request.GET.get('ano', ano_atual))
    except (TypeError, ValueError):
        ano = ano_atual

    busca = request.GET.get('busca', '').strip()

    qs = (
        BensPermanentes.objects
        .filter(acquisition_date__year=ano)
        .select_related('description', 'supllier', 'history_tombo__current_ua')
        .order_by('-acquisition_date', '-id')
    )
    if busca:
        qs = qs.filter(
            Q(tombo__icontains=busca) |
            Q(description__description__icontains=busca) |
            Q(mark__icontains=busca)
        )

    total = qs.count()
    valor_total = qs.aggregate(s=Sum('value'))['s'] or 0

    pagina = Paginator(qs, ENTRADAS_POR_PAGINA).get_page(request.GET.get('pagina'))

    return render(request, 'dimrcbp/movimentacao/entradas.html', {
        'itens': pagina,
        'total': total,
        'valor_total': valor_total,
        'ano': ano,
        'anos_disponiveis': anos_disponiveis,
        'busca': busca,
    })
