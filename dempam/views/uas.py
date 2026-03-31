# bibliotecas do django
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

# importações do código
from ..forms import InfoUAForm
from ..models import InfoUA

# =========================================
# VIEWS DAS UAS (UNIDADES ADMINISTRATIVAS)
# =========================================



''' Unidades Administrativas '''
# Página inicial das UAs
@login_required
def ua_homepage(request):
    query = request.GET.get("q", "").strip()

    uas = InfoUA.objects.select_related("circunscricao_predio").all().order_by("ua")

    if query:
        uas = uas.filter(
            Q(ua__icontains=query) |
            Q(responsavel_ua__icontains=query) |
            Q(email_ua__icontains=query) |
            Q(circunscricao_predio__local__icontains=query)
        )

    context = {
        "uas": uas,
        "query": query,
    }
    return render(request, "dempam/uas/ua_homepage.html", context)

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

'''#' Editar UA existente
@login_required
def ua_update(request, pk):
    ua = get_object_or_404(InfoUA, pk=pk)

    if request.method == "POST":
        form = InfoUAForm(request.POST, instance=ua)
        if form.is_valid():
            form.save()
            messages.success(request, "UA atualizada com sucesso.")
            return redirect("dempam:ua_homepage")
    else:
        form = InfoUAForm(instance=ua)

    context = {
        "form": form,
        "ua_obj": ua,
        "page_title": "Editar UA",
        "button_label": "Atualizar UA",
    }
    return render(request, "dempam/uas/ua_update.html", context)'''