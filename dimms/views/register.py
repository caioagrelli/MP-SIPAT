# BIBLIOTECAS PADRÃO PYTHON
import os
import urllib.request
from io import BytesIO

# DJANGO
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.contrib import messages
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
from ..forms import *


@login_required
def create_request(request):
    if request.method == 'POST':
        form = SolicitacaoForm(request.POST, request.FILES)
        formset = SolicitacaoItemFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            solicitacao = form.save(commit=False)
            solicitacao.user_responsible = request.user
            solicitacao.save()

            formset.instance = solicitacao
            formset.save()

            messages.success(request, 'Solicitação criada com sucesso.')
            return redirect('dimms:processing')
    else:
        form = SolicitacaoForm()
        formset = SolicitacaoItemFormSet()

    context = {
        'form': form,
        'formset': formset,
    }
    return render(request, 'dimms/create_request.html', context)


@login_required
def create_update(request):
    if request.method == 'POST':
        form = TramitacaoCreateForm(request.POST, request.FILES)

        if form.is_valid():
            tramitacao = form.save(commit=False)
            tramitacao.user_update = request.user

            if not tramitacao.responsible_update:
                tramitacao.responsible_update = (
                    request.user.get_full_name() or request.user.username
                )

            tramitacao.save()

            messages.success(request, 'Tramitação registrada com sucesso.')
            return redirect('dimms:processing')
    else:
        form = TramitacaoCreateForm()

    ultimas_solicitacoes = Solicitacao.objects.select_related('ua_order').order_by('-data_order')[:8]

    context = {
        'form': form,
        'ultimas_solicitacoes': ultimas_solicitacoes,
    }
    return render(request, 'dimms/create_update.html', context)

@login_required
def update_request(request, pk):
    solicitacao = get_object_or_404(Solicitacao, pk=pk)

    if request.method == 'POST':
        form = SolicitacaoStatusUpdateForm(request.POST, request.FILES, instance=solicitacao)

        if form.is_valid():
            solicitacao_atualizada = form.save()

            observacao = form.cleaned_data.get('observacao_tramitacao')
            documento = form.cleaned_data.get('documents_update')
            foto = form.cleaned_data.get('photo_update')

            Tramitacao.objects.create(
                request_update=solicitacao_atualizada,
                update=solicitacao_atualizada.situation,
                responsible_update=request.user.get_full_name() or request.user.username,
                observation_update=observacao,
                documents_update=documento,
                photo_update=foto,
                user_update=request.user,
            )

            messages.success(request, 'Solicitação atualizada com sucesso.')
            return redirect('dimms:details_processing', pk=solicitacao.pk)
    else:
        form = SolicitacaoStatusUpdateForm(instance=solicitacao)

    historico = solicitacao.tramitacao.order_by('-date_update', '-id')[:10]

    context = {
        'form': form,
        'solicitacao': solicitacao,
        'historico': historico,
    }
    return render(request, 'dimms/update_request.html', context)