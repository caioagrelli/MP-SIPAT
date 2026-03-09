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


# Páginas de detalhes (processing, active balance, register movement)
@login_required 
def processing(request):
    query = request.GET.get('q', '')
    filtro_status = request.GET.get('status', '')

    tramitacoes = [
        {
            "numero": "TRM-2026-001",
            "assunto": "Aquisição de cadeiras ergonômicas",
            "setor_origem": "Almoxarifado",
            "setor_destino": "Compras",
            "responsavel": "Maria Souza",
            "status": "EM_ANDAMENTO",
            "prioridade": "Alta",
            "ultima_atualizacao": "Hoje, 09:15",
        },
        {
            "numero": "TRM-2026-002",
            "assunto": "Reposição de papel A4",
            "setor_origem": "Administrativo",
            "setor_destino": "Almoxarifado",
            "responsavel": "Carlos Lima",
            "status": "CONCLUIDA",
            "prioridade": "Normal",
            "ultima_atualizacao": "Ontem, 16:40",
        },
        {
            "numero": "TRM-2026-003",
            "assunto": "Solicitação de manutenção em ar-condicionado",
            "setor_origem": "Patrimônio",
            "setor_destino": "Infraestrutura",
            "responsavel": "Fernanda Alves",
            "status": "PENDENTE",
            "prioridade": "Alta",
            "ultima_atualizacao": "Hoje, 08:10",
        },
        {
            "numero": "TRM-2026-004",
            "assunto": "Movimentação de notebooks",
            "setor_origem": "TI",
            "setor_destino": "Gabinete",
            "responsavel": "João Pedro",
            "status": "CANCELADA",
            "prioridade": "Baixa",
            "ultima_atualizacao": "03/03/2026",
        },
        {
            "numero": "TRM-2026-005",
            "assunto": "Compra de toners",
            "setor_origem": "Secretaria",
            "setor_destino": "Compras",
            "responsavel": "Ana Beatriz",
            "status": "EM_ANDAMENTO",
            "prioridade": "Normal",
            "ultima_atualizacao": "Hoje, 11:32",
        },
        {
            "numero": "TRM-2026-006",
            "assunto": "Regularização de patrimônio sem tombo",
            "setor_origem": "Patrimônio",
            "setor_destino": "Diretoria",
            "responsavel": "Ricardo Nunes",
            "status": "CONCLUIDA",
            "prioridade": "Alta",
            "ultima_atualizacao": "01/03/2026",
        },
        {
            "numero": "TRM-2026-007",
            "assunto": "Solicitação de material de limpeza",
            "setor_origem": "Serviços Gerais",
            "setor_destino": "Almoxarifado",
            "responsavel": "Paula Mendes",
            "status": "PENDENTE",
            "prioridade": "Normal",
            "ultima_atualizacao": "Hoje, 10:05",
        },
    ]

    if query:
        termo = query.lower()
        tramitacoes = [
            t for t in tramitacoes
            if termo in t["numero"].lower()
            or termo in t["assunto"].lower()
            or termo in t["setor_origem"].lower()
            or termo in t["setor_destino"].lower()
            or termo in t["responsavel"].lower()
        ]

    if filtro_status:
        tramitacoes = [t for t in tramitacoes if t["status"] == filtro_status]

    total = len(tramitacoes)
    total_andamento = sum(1 for t in tramitacoes if t["status"] == "EM_ANDAMENTO")
    total_concluidas = sum(1 for t in tramitacoes if t["status"] == "CONCLUIDA")
    total_pendentes = sum(1 for t in tramitacoes if t["status"] == "PENDENTE")
    total_canceladas = sum(1 for t in tramitacoes if t["status"] == "CANCELADA")

    context = {
        "tramitacoes": tramitacoes,
        "query": query,
        "filtro_status": filtro_status,
        "total_tramitacoes": total,
        "total_andamento": total_andamento,
        "total_concluidas": total_concluidas,
        "total_pendentes": total_pendentes,
        "total_canceladas": total_canceladas,
    }

    return render(request, "dimms/processing.html", context)

@login_required
def details_processing(request, pk):
    solicitacao = {
        "id": pk,
        "numero": f"PROC-2026-{pk:03d}",
        "titulo": "Solicitação de materiais de expediente",
        "descricao": "Solicitação provisória criada apenas para demonstração visual da página de detalhes.",
        "status_atual": "EM_ANDAMENTO",
        "prioridade": "Alta",
        "setor_origem": "Almoxarifado Central",
        "setor_destino": "Diretoria Administrativa",
        "responsavel_atual": "Mariana Alves",
        "solicitante": "Carlos Henrique",
        "data_abertura": "09/03/2026 08:30",
        "ultima_atualizacao": "09/03/2026 14:15",
        "prazo": "12/03/2026",
        "observacoes": "Processo em acompanhamento. Aguardando validação do setor de destino.",
    }

    itens_solicitacao = [
        {
            "codigo": "MAT-001",
            "descricao": "Resma de papel A4",
            "quantidade": 20,
            "unidade": "pacotes",
            "observacao": "Uso administrativo"
        },
        {
            "codigo": "MAT-014",
            "descricao": "Caneta esferográfica azul",
            "quantidade": 50,
            "unidade": "unidades",
            "observacao": "Distribuição interna"
        },
        {
            "codigo": "MAT-020",
            "descricao": "Pasta arquivo",
            "quantidade": 15,
            "unidade": "unidades",
            "observacao": "Arquivo de documentos"
        },
    ]

    historico_status = [
        {
            "data_hora": "09/03/2026 08:30",
            "responsavel": "Carlos Henrique",
            "status": "ABERTA",
            "mudanca": "Solicitação criada no sistema."
        },
        {
            "data_hora": "09/03/2026 09:10",
            "responsavel": "Mariana Alves",
            "status": "EM_TRIAGEM",
            "mudanca": "Solicitação recebida para conferência inicial."
        },
        {
            "data_hora": "09/03/2026 11:45",
            "responsavel": "Mariana Alves",
            "status": "EM_ANDAMENTO",
            "mudanca": "Itens conferidos e encaminhamento iniciado."
        },
        {
            "data_hora": "09/03/2026 14:15",
            "responsavel": "João Pedro",
            "status": "AGUARDANDO_VALIDACAO",
            "mudanca": "Encaminhado ao setor de destino para validação."
        },
    ]

    context = {
        "solicitacao": solicitacao,
        "itens_solicitacao": itens_solicitacao,
        "historico_status": historico_status,
    }

    return render(request, "dimms/details_processing.html", context)


def active_balance(request):
    return render(request, 'dimms/active_balance.html')

def register_movement(request):
    return render(request, 'dimms/register_movement.html')