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


''' Etiquetas dos Bem '''
@login_required
def label(request, pk):
    item = get_object_or_404(
        Estoque.objects.select_related("item_shock", "locate"),
        pk=pk
    )

    url = request.build_absolute_uri(
        reverse("dimms:overview", args=[item.pk])
    )

    # QR code
    qr = qrcode.QRCode(error_correction=ERROR_CORRECT_M, box_size=10, border=1)
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_buf = BytesIO()
    qr_img.save(qr_buf, format="PNG")
    qr_buf.seek(0)
    qr_reader = ImageReader(qr_buf)

    # Logo
    logo_reader = None
    logo_path = finders.find("img/brasao-mppe.png")
    if logo_path and os.path.exists(logo_path):
        logo_reader = ImageReader(logo_path)

    # Dados do item
    shock = getattr(item, "item_shock", None)
    efisco_val = getattr(shock, "efisco", None) or "—"
    medida_val = getattr(shock, "medida", None) or "—"
    desc_text = (item.description_manual or "Sem descrição")[:55]
    marca_val = item.mark or "—"
    qtd_val = str(item.amount_shock) if item.amount_shock is not None else "—"
    safe_efisco = "".join(ch for ch in efisco_val if ch.isalnum() or ch in ("-", "_")) or "sem_efisco"

    # PDF 80×50 mm
    w, h = 80 * mm, 50 * mm
    resp = HttpResponse(content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="etiqueta_{safe_efisco}.pdf"'

    c = canvas.Canvas(resp, pagesize=(w, h))
    m = 3 * mm

    # Fundo branco
    c.setFillColorRGB(1, 1, 1)
    c.rect(0, 0, w, h, fill=1, stroke=0)

    # Faixa superior escura
    band_h = 16 * mm
    c.setFillColorRGB(0.12, 0.18, 0.26)
    c.rect(0, h - band_h, w, band_h, fill=1, stroke=0)

    # Logo sobre a faixa
    if logo_reader:
        c.drawImage(logo_reader, m, h - band_h + 2.5 * mm, width=11 * mm, height=11 * mm, mask="auto")

    # Título na faixa
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(16 * mm, h - 7 * mm, "MPPE — Bens de Consumo")
    c.setFont("Helvetica", 6)
    c.setFillColorRGB(0.65, 0.72, 0.85)
    c.drawString(16 * mm, h - 11 * mm, "Sistema de Gestão de Almoxarifado")

    # E-Fisco em destaque (direita da faixa)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 9)
    c.drawRightString(w - m, h - 8 * mm, f"E-Fisco: {efisco_val}")

    # QR (canto inferior esquerdo)
    qr_size = 28 * mm
    c.drawImage(qr_reader, m, m, width=qr_size, height=qr_size, mask="auto")

    # Área de texto à direita do QR
    x_text = m + qr_size + 3 * mm
    text_w = w - x_text - m

    # Descrição (quebra de linha automática, até 3 linhas)
    c.setFillColorRGB(0.1, 0.13, 0.2)
    c.setFont("Helvetica-Bold", 6.5)
    words = desc_text.split()
    line, lines = "", []
    for word in words:
        test = f"{line} {word}".strip()
        if c.stringWidth(test, "Helvetica-Bold", 6.5) < text_w:
            line = test
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)

    y = h - band_h - 5 * mm
    for ln in lines[:3]:
        c.drawString(x_text, y, ln)
        y -= 7

    # Linha divisória sutil
    y -= 2
    c.setStrokeColorRGB(0.8, 0.83, 0.9)
    c.setLineWidth(0.4)
    c.line(x_text, y, w - m, y)
    y -= 5

    # Marca / Medida / Qtd
    c.setFont("Helvetica", 6)
    c.setFillColorRGB(0.3, 0.38, 0.5)
    c.drawString(x_text, y, f"Marca: {marca_val}")
    y -= 7
    c.drawString(x_text, y, f"Und: {medida_val}   Qtd: {qtd_val}")

    c.showPage()
    c.save()
    return resp

# Pequeno
@login_required
def label_mini(request):
    return redirect('dimms:homepage')
