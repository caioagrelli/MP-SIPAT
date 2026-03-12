# BIBLIOTECAS PADRÃO PYTHON
import os
import urllib.request
from io import BytesIO

# DJANGO
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.urls import reverse
from datetime import datetime
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles import finders

# BIBLIOTECAS EXTERNAS
import qrcode
from qrcode.constants import ERROR_CORRECT_M

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import mm
from reportlab.lib.utils import ImageReader

# MODELOS DO PROJETO
from ..models import *
from ..utils import *


@login_required
def processing(request):
    query        = request.GET.get('q', '').strip()
    filtro_status = request.GET.get('status', '').strip()

    # Base: exclui rascunhos de outros usuários
    solicitacoes = (
        Solicitacao.objects
        .select_related('ua_order', 'user_responsible')
        .filter(
            Q(situation='RASCUNHO', user_responsible=request.user) |
            ~Q(situation='RASCUNHO')
        )
        .order_by('-data_order')
    )

    if query:
        solicitacoes = solicitacoes.filter(
            Q(request_code__icontains=query)             |
            Q(user_order__icontains=query)               |
            Q(observation_order__icontains=query)        |
            Q(user_responsible__username__icontains=query)   |
            Q(user_responsible__first_name__icontains=query) |
            Q(user_responsible__last_name__icontains=query)
        )

    if filtro_status:
        solicitacoes = solicitacoes.filter(situation=filtro_status)

    # Anexa última tramitação em cada solicitação
    for s in solicitacoes:
        s.ultima_tramitacao = s.tramitacao.order_by('-date_update', '-id').first()

    # KPIs — calculados sobre o queryset já filtrado (sem rascunhos alheios)
    base_kpi = (
        Solicitacao.objects
        .filter(
            Q(situation='RASCUNHO', user_responsible=request.user) |
            ~Q(situation='RASCUNHO')
        )
    )

    context = {
        'tramitacoes':     solicitacoes,
        'query':           query,
        'filtro_status':   filtro_status,

        'total_tramitacoes': solicitacoes.count(),

        'total_atendimento':          base_kpi.filter(situation='ATENDIMENTO').count(),
        'total_aguardando_separacao': base_kpi.filter(situation='AGUAR_SEPARACAO').count(),
        'total_separada':             base_kpi.filter(situation='SEPARADA').count(),
        'total_expedicao':            base_kpi.filter(situation='EXPEDICAO').count(),
        'total_recebida':             base_kpi.filter(situation='RECEBIDA').count(),
        'total_cancelada':            base_kpi.filter(situation='CANCELADA').count(),
        'total_rascunho':             base_kpi.filter(situation='RASCUNHO', user_responsible=request.user).count(),
    }

    return render(request, 'dimms/processing.html', context)

def details_processing(request, pk):
    solicitacao = get_object_or_404(
        Solicitacao.objects
        .select_related('ua_order', 'user_responsible'),
        pk=pk
    )

    itens_solicitados = (
        solicitacao.bens_solicitados
        .select_related('item_order__item_shock')
        .all()
    )

    historico_tramitacao = (
        solicitacao.tramitacao
        .select_related('user_update')
        .order_by('date_update', 'id')
    )

    ultima_tramitacao = historico_tramitacao.last()

    etapas_fluxo = [
        {"codigo": "ATENDIMENTO", "label": "Em atendimento"},
        {"codigo": "AGUAR_SEPARACAO", "label": "Aguardando separação"},
        {"codigo": "SEPARADA", "label": "Separada"},
        {"codigo": "EXPEDICAO", "label": "Em expedição"},
        {"codigo": "RECEBIDA", "label": "Recebida"},
    ]

    ordem_status = {
        "ATENDIMENTO": 0,
        "AGUARD_SEPARACAO": 1,
        "SEPARADA": 2,
        "EXPEDICAO": 3,
        "RECEBIDA": 4,
    }

    status_atual = solicitacao.situation
    indice_atual = ordem_status.get(status_atual, -1)

    for i, etapa in enumerate(etapas_fluxo):
        etapa["concluida"] = i < indice_atual
        etapa["atual"] = i == indice_atual
        etapa["pendente"] = i > indice_atual

    context = {
        'solicitacao': solicitacao,
        'itens_solicitados': itens_solicitados,
        'historico_tramitacao': historico_tramitacao,
        'ultima_tramitacao': ultima_tramitacao,
        'etapas_fluxo': etapas_fluxo,
    }

    return render(request, 'dimms/details_processing.html', context)

def course(request, solicitacao_pk, tramitacao_pk):
    solicitacao = get_object_or_404(
        Solicitacao.objects.select_related('ua_order', 'user_responsible'),
        pk=solicitacao_pk
    )

    tramitacao = get_object_or_404(
        Tramitacao.objects.select_related('request_update', 'user_update'),
        pk=tramitacao_pk,
        request_update=solicitacao
    )

    context = {
        "solicitacao": solicitacao,
        "tramitacao": tramitacao,
        "destino": "Destino não configurado",  # depois você troca pelo campo real
    }

    return render(request, "dimms/course.html", context)