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
def create_update(request, pk):
    solicitacao = get_object_or_404(Solicitacao, pk=pk)

    if request.method == 'POST':
        form = TramitacaoForm(request.POST, request.FILES)

        if form.is_valid():
            tramitacao = form.save(commit=False)
            tramitacao.request_update = solicitacao
            tramitacao.user_update = request.user

            if not tramitacao.responsible_update:
                tramitacao.responsible_update = request.user.get_full_name() or request.user.username

            tramitacao.save()

            messages.success(request, 'Tramitação registrada com sucesso.')
            return redirect('dimms:processing_detail', pk=solicitacao.pk)
    else:
        form = TramitacaoForm()

    context = {
        'form': form,
        'solicitacao': solicitacao,
    }
    return render(request, 'dimms/create_update.html', context)