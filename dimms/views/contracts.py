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
def contracts(request):
    hoje = timezone.now().date()

    contratos = (
        Contrato.objects
        .select_related('fornecedor')
        .order_by('-id')
    )

    total_contratos = contratos.count()

    contratos_vigentes_qs = contratos.filter(
        inicio_vigencia__isnull=False,
        final_vigencia__isnull=False,
        inicio_vigencia__lte=hoje,
        final_vigencia__gte=hoje,
    )

    contratos_encerrados_qs = contratos.filter(
        final_vigencia__isnull=False,
        final_vigencia__lt=hoje
    )

    # PROVISÓRIO:
    # contratos em análise = contratos sem início e sem fim de vigência definidos
    contratos_analise_qs = contratos.filter(
        inicio_vigencia__isnull=True,
        final_vigencia__isnull=True
    )

    contratos_vigentes = contratos_vigentes_qs.count()
    contratos_encerrados = contratos_encerrados_qs.count()
    contratos_analise = contratos_analise_qs.count()

    ultimos_contratos = contratos[:8]
    contratos_em_analise_lista = contratos_analise_qs[:5]
    contratos_vigentes_lista = contratos_vigentes_qs[:5]

    context = {
        'total_contratos': total_contratos,
        'contratos_vigentes': contratos_vigentes,
        'contratos_encerrados': contratos_encerrados,
        'contratos_analise': contratos_analise,
        'ultimos_contratos': ultimos_contratos,
        'contratos_em_analise_lista': contratos_em_analise_lista,
        'contratos_vigentes_lista': contratos_vigentes_lista,
    }

    return render(request, 'dimms/contracts.html', context)