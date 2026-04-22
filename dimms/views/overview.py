# Importações do Python 
import os
from io import BytesIO

# Importações do Dj Ango
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles import finders

# Bibliotecas externas
import qrcode
from qrcode.constants import ERROR_CORRECT_M

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import mm
from reportlab.lib.utils import ImageReader

# Importações do Código
from .. models import Estoque
from .. forms import EstoqueForm

# =============================================================
# CAMPOS DESTINADOS PARA A VISUALIZAÇÃO/MANUTENÇÃO DE CADA BEM
# =============================================================


''' Overview (Visualização dos bens)'''
# Página Principal do bem
@login_required
def overview(request, pk):
    item = get_object_or_404(Estoque.objects.select_related("item_shock", "locate"), pk=pk)
    return render(request, 'dimms/overview.html', {
        'item': item
    })
    
# Gerar QR Code da página da Overview
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


''' Editar dados do bem '''
@login_required
def overview_edit(request, pk):
    item = get_object_or_404(Estoque.objects.select_related('item_shock', 'locate'), pk=pk)
    if request.method == 'POST':
        form = EstoqueForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            edited = form.save(commit=False)
            edited.updated_by = request.user
            edited.save()
            from django.contrib import messages
            messages.success(request, 'Item atualizado com sucesso.')
            return redirect('dimms:overview', pk=pk)
    else:
        form = EstoqueForm(instance=item)
    return render(request, 'dimms/overview_edit.html', {'form': form, 'item': item})


''' Etiquetas dos Bem '''   # Pra terminar
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

# Pequeno
@login_required
def label_mini(request):
    return redirect('dimms:homepage')
