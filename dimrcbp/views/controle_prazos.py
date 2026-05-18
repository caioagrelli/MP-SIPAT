from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render
from django.utils import timezone

from dimrcbp.models import BensPermanentes


@login_required
def controle_prazos(request):
    hoje = timezone.now().date()

    qs = BensPermanentes.objects.select_related(
        'description', 'description__type', 'description__type__gruop',
    ).exclude(garantia_vencimento__isnull=True)

    # Filtros
    proximidade  = request.GET.get('proximidade', '')
    busca        = request.GET.get('busca', '').strip()
    entrada_de   = request.GET.get('entrada_de', '').strip()
    entrada_ate  = request.GET.get('entrada_ate', '').strip()
    garantia_de  = request.GET.get('garantia_de', '').strip()
    garantia_ate = request.GET.get('garantia_ate', '').strip()

    if busca:
        qs = qs.filter(
            Q(tombo__icontains=busca) |
            Q(description__description__icontains=busca) |
            Q(mark__icontains=busca)
        )
    if entrada_de:
        qs = qs.filter(acquisition_date__gte=entrada_de)
    if entrada_ate:
        qs = qs.filter(acquisition_date__lte=entrada_ate)
    if garantia_de:
        qs = qs.filter(garantia_vencimento__gte=garantia_de)
    if garantia_ate:
        qs = qs.filter(garantia_vencimento__lte=garantia_ate)

    if proximidade == 'vencidos':
        qs = qs.filter(garantia_vencimento__lt=hoje)
    elif proximidade == 'hoje':
        qs = qs.filter(garantia_vencimento=hoje)
    elif proximidade == '7':
        qs = qs.filter(garantia_vencimento__gte=hoje,
                       garantia_vencimento__lte=hoje + timedelta(days=7))
    elif proximidade == '30':
        qs = qs.filter(garantia_vencimento__gte=hoje,
                       garantia_vencimento__lte=hoje + timedelta(days=30))
    elif proximidade == '90':
        qs = qs.filter(garantia_vencimento__gte=hoje,
                       garantia_vencimento__lte=hoje + timedelta(days=90))

    qs = qs.distinct().order_by('garantia_vencimento')

    # Resumo geral (sem filtros aplicados)
    todos = BensPermanentes.objects.exclude(garantia_vencimento__isnull=True)
    resumo = {
        'vencidos': todos.filter(garantia_vencimento__lt=hoje).count(),
        'hoje':     todos.filter(garantia_vencimento=hoje).count(),
        'em_7':     todos.filter(garantia_vencimento__gt=hoje,
                                 garantia_vencimento__lte=hoje + timedelta(days=7)).count(),
        'em_30':    todos.filter(garantia_vencimento__gt=hoje,
                                 garantia_vencimento__lte=hoje + timedelta(days=30)).count(),
        'total':    todos.count(),
    }

    ALERTA_DIAS = 30
    itens = []
    for b in qs:
        dias = (b.garantia_vencimento - hoje).days
        if dias < 0:
            status = 'vencido'
        elif dias <= ALERTA_DIAS:
            status = 'alerta'
        else:
            status = 'ok'
        itens.append({'bem': b, 'dias': dias, 'status': status})

    return render(request, 'dimrcbp/controle_prazos.html', {
        'itens':   itens,
        'resumo':  resumo,
        'hoje':    hoje,
        'filtros': {
            'proximidade':  proximidade,
            'busca':        busca,
            'entrada_de':   entrada_de,
            'entrada_ate':  entrada_ate,
            'garantia_de':  garantia_de,
            'garantia_ate': garantia_ate,
        },
    })
