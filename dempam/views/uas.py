# bibliotecas do django
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

# importações do código
from ..forms import InfoUAForm
from ..models import InfoUA, CircunscricaoPredio
from dimms.models import Solicitacao

# =========================================
# VIEWS DAS UAS (UNIDADES ADMINISTRATIVAS)
# =========================================



''' Unidades Administrativas '''
# Página inicial das UAs
@login_required
def ua_homepage(request):
    query = request.GET.get("q", "").strip()
    predio_filter = request.GET.get("predio", "").strip()
    sede_filter = request.GET.get("sede", "").strip()

    total_cadastradas = InfoUA.objects.count()
    total_sedes = InfoUA.objects.filter(sede=True).count()
    total_predios = CircunscricaoPredio.objects.count()

    uas = InfoUA.objects.select_related("circunscricao_predio").all().order_by("ua")

    if query:
        uas = uas.filter(
            Q(ua__icontains=query) |
            Q(responsavel_ua__icontains=query) |
            Q(email_ua__icontains=query) |
            Q(circunscricao_predio__local__icontains=query)
        )

    if predio_filter:
        uas = uas.filter(circunscricao_predio__pk=predio_filter)

    if sede_filter == "1":
        uas = uas.filter(sede=True)
    elif sede_filter == "0":
        uas = uas.filter(sede=False)

    predios = CircunscricaoPredio.objects.order_by("local")

    context = {
        "uas": uas,
        "query": query,
        "predio_filter": predio_filter,
        "sede_filter": sede_filter,
        "predios": predios,
        "total_cadastradas": total_cadastradas,
        "total_sedes": total_sedes,
        "total_predios": total_predios,
    }
    return render(request, "dempam/uas/ua_homepage.html", context)

@login_required
def ua_detail(request, pk):
    ua = get_object_or_404(InfoUA.objects.select_related('circunscricao_predio'), pk=pk)
    solicitacoes = ua.solicitantesconsumo.select_related('user_responsible').order_by('-data_order')

    total = solicitacoes.count()
    em_atendimento = solicitacoes.filter(situation='ATENDIMENTO').count()
    recebidas = solicitacoes.filter(situation='RECEBIDA').count()
    canceladas = solicitacoes.filter(situation='CANCELADA').count()

    return render(request, 'dempam/uas/ua_detail.html', {
        'ua': ua,
        'solicitacoes': solicitacoes,
        'total': total,
        'em_atendimento': em_atendimento,
        'recebidas': recebidas,
        'canceladas': canceladas,
    })


# Cadastrar nova UA
@login_required
def ua_add(request):
    if request.method == "POST":
        form = InfoUAForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "UA cadastrada com sucesso.")
            return redirect("dempam:ua_homepage")
    else:
        form = InfoUAForm()

    context = {
        "form": form,
        "page_title": "Cadastrar UA",
        "button_label": "Salvar UA",
    }
    return render(request, "dempam/uas/ua_add.html", context)

@login_required
def ua_update(request, pk):
    ua = get_object_or_404(InfoUA, pk=pk)

    if request.method == "POST":
        form = InfoUAForm(request.POST, instance=ua)
        if form.is_valid():
            form.save()
            messages.success(request, "UA atualizada com sucesso.")
            return redirect("dempam:ua_detail", pk=pk)
    else:
        form = InfoUAForm(instance=ua)

    return render(request, "dempam/uas/ua_update.html", {
        "form": form,
        "ua_obj": ua,
        "page_title": "Editar UA",
        "button_label": "Atualizar UA",
    })