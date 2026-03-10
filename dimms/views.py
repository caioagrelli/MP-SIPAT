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
from .models import *
from .utils import *

# Páginas Principais
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

@login_required
def overview(request, pk):
    item = get_object_or_404(Estoque.objects.select_related("item_shock", "locate"), pk=pk)
    return render(request, 'dimms/overview.html', {
        'item': item
    })

@login_required
def details(request, pk):
    item = get_object_or_404(Estoque.objects.select_related("item_shock", "locate"), pk=pk)
    return render(request, 'dimms/details.html', {
      'item': item
    })

# Detalhes das listas (low stock, essential, vencimento)
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

    return render(request, 'dimms/low_stock.html', context)

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
        'dimms/essential.html',
        context
    )

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

    return render(request, 'dimms/expiration_alert.html', context)
    
# Gerar QR Code para o item
@login_required
def qrcode_view(request, pk):
    item = get_object_or_404(Estoque, pk=pk)

    # URL que o QR vai abrir
    url = request.build_absolute_uri(
        reverse("dimms:overview", args=[item.pk])
    )

    qr = qrcode.QRCode(error_correction=ERROR_CORRECT_M, box_size=10, border=3)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buf = BytesIO()
    img.save(buf, format="PNG")
    return HttpResponse(buf.getvalue(), content_type="image/png")

# Gerar PDF da etiqueta (QR + E-FISCO + Logo)

# Grande
@login_required
def label(request, pk):
    item = get_object_or_404(
        Estoque.objects.select_related("item_shock"),
        pk=pk
    )

    # URL que o QR vai abrir
    url = request.build_absolute_uri(
        reverse("dimms:overview", args=[item.pk])
    )

    # --- QR (PIL -> BytesIO) ---
    qr = qrcode.QRCode(
        error_correction=ERROR_CORRECT_M,
        box_size=10,
        border=1
    )
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    qr_buf = BytesIO()
    qr_img.save(qr_buf, format="PNG")
    qr_buf.seek(0)
    qr_reader = ImageReader(qr_buf)

    # --- Logo (STATIC local) ---
    logo_reader = None
    logo_path = finders.find("img/brasao-mppe.png")
    if logo_path and os.path.exists(logo_path):
        logo_reader = ImageReader(logo_path)

    # --- Dados do item (com fallback) ---
    efisco = "-"
    if getattr(item, "item_shock", None) and getattr(item.item_shock, "efisco", None):
        efisco = f"E-Fisco: {item.item_shock.efisco}"

    # Filename seguro (evita caracteres estranhos)
    safe_efisco = "".join(ch for ch in efisco if ch.isalnum() or ch in ("-", "_")) or "sem_efisco"

    # --- PDF (80x50mm) ---
    w, h = 80 * mm, 50 * mm
    resp = HttpResponse(content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="etiqueta_{safe_efisco}.pdf"'

    c = canvas.Canvas(resp, pagesize=(w, h))

    # Fundo branco
    c.setFillColorRGB(1, 1, 1)
    c.rect(0, 0, w, h, fill=1, stroke=0)

    # Margens
    m = 4 * mm

    # Logo (top-left)
    if logo_reader:
        c.drawImage(
            logo_reader,
            m,
            h - 18 * mm,
            width=18 * mm,
            height=14 * mm,
            mask="auto"
        )

    # E-FISCO (top-right)
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 14)
    c.drawRightString(w - m, h - 8 * mm, efisco)

    # QR (bottom-left)
    qr_size = 26 * mm
    c.drawImage(
        qr_reader,
        m,
        m,
        width=qr_size,
        height=qr_size,
        mask="auto"
    )

    c.showPage()
    c.save()
    return resp
# Pequeno (Pra fazer)
@login_required
def label_mini(request):
    return redirect('dimms:homepage')

@login_required
def processing(request):
    query = request.GET.get('q', '').strip()
    filtro_status = request.GET.get('status', '').strip()

    solicitacoes = (
        Solicitacao.objects
        .select_related('ua_order', 'user_responsible')
        .order_by('-data_order')
    )

    if query:
        solicitacoes = solicitacoes.filter(
            Q(request_code__icontains=query) |
            Q(user_order__icontains=query) |
            Q(observation_order__icontains=query) |
            Q(user_responsible__username__icontains=query) |
            Q(user_responsible__first_name__icontains=query) |
            Q(user_responsible__last_name__icontains=query)
            # Exemplo, se quiser pesquisar também por UA:
            # | Q(ua_order__nome__icontains=query)
        )

    if filtro_status:
        solicitacoes = solicitacoes.filter(situation=filtro_status)

    for s in solicitacoes:
        s.ultima_tramitacao = s.tramitacao.order_by('-date_update', '-id').first()
    
    context = {
        'tramitacoes': solicitacoes,
        'query': query,
        'filtro_status': filtro_status,

        'total_tramitacoes': solicitacoes.count(),
        'total_processamento': solicitacoes.filter(situation='PROCESSAMENTO').count(),
        'total_separada': solicitacoes.filter(situation='SEPARADA').count(),
        'total_envio': solicitacoes.filter(situation='ENVIO').count(),
        'total_tramitacao': solicitacoes.filter(situation='TRAMITACAO').count(),
        'total_recebida': solicitacoes.filter(situation='RECEBIDA').count(),
        'total_cancelada': solicitacoes.filter(situation='CANCELADA').count(),
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
        {"codigo": "PROCESSAMENTO", "label": "Em preparação"},
        {"codigo": "SEPARADA", "label": "Separada"},
        {"codigo": "ENVIO", "label": "Para envio"},
        {"codigo": "TRAMITACAO", "label": "A caminho"},
        {"codigo": "RECEBIDA", "label": "Recebida"},
    ]

    ordem_status = {
        "PROCESSAMENTO": 0,
        "SEPARADA": 1,
        "ENVIO": 2,
        "TRAMITACAO": 3,
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

def active_balance(request):
    return render(request, 'dimms/active_balance.html')

def register_movement(request):
    return render(request, 'dimms/register_movement.html')