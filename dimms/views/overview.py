# Importações do Python
import os
from io import BytesIO
from datetime import datetime

# Importações do Dj Ango
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles import finders
from django.core.paginator import Paginator

# Bibliotecas externas
import qrcode
from qrcode.constants import ERROR_CORRECT_M

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

# Importações do Código
from .. models import Estoque, Tramitacao
from .. forms import EstoqueForm

# =============================================================
# CAMPOS DESTINADOS PARA A VISUALIZAÇÃO/MANUTENÇÃO DE CADA BEM
# =============================================================


''' Overview (Visualização dos bens)'''
# Página Principal do bem
@login_required
def overview(request, pk):
    item = get_object_or_404(Estoque.objects.select_related("item_shock", "locate"), pk=pk)

    tram_qs = (
        Tramitacao.objects
        .filter(request_update__bens_solicitados__item_order=item)
        .select_related('request_update__ua_order', 'user_update')
        .distinct()
        .order_by('-date_update', '-id')
    )
    paginator = Paginator(tram_qs, 10)
    page_obj  = paginator.get_page(request.GET.get('page'))

    return render(request, 'dimms/overview.html', {
        'item':     item,
        'page_obj': page_obj,
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


''' Ficha Técnica PDF '''
@login_required
def ficha_tecnica(request, pk):
    item  = get_object_or_404(Estoque.objects.select_related('item_shock', 'locate', 'updated_by'), pk=pk)
    shock = item.item_shock

    logo_reader = None
    logo_path = finders.find('img/brasao-mppe.png')
    if logo_path and os.path.exists(logo_path):
        logo_reader = ImageReader(logo_path)

    safe_name = "".join(c for c in str(shock.efisco) if c.isalnum() or c in ('-', '_')) or f'item_{pk}'
    resp = HttpResponse(content_type='application/pdf')
    resp['Content-Disposition'] = f'inline; filename="ficha_tecnica_{safe_name}.pdf"'

    w, h_page = A4
    c = canvas.Canvas(resp, pagesize=A4)

    # ── helpers ───────────────────────────────────────────────────────────────
    def section(title, y):
        c.setFillColor(colors.HexColor('#1e2d42'))
        c.rect(14 * mm, y - 7 * mm, w - 28 * mm, 8 * mm, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont('Helvetica-Bold', 8.5)
        c.drawString(17 * mm, y - 4.5 * mm, title.upper())
        return y - 15 * mm

    def row(label, value, y, shade=False):
        rh = 7 * mm
        if shade:
            c.setFillColor(colors.HexColor('#f7f8fc'))
            c.rect(14 * mm, y - rh, w - 28 * mm, rh, fill=1, stroke=0)
        c.setFillColor(colors.HexColor('#7380a0'))
        c.setFont('Helvetica-Bold', 7.5)
        c.drawString(17 * mm, y - 4.8 * mm, label.upper())
        c.setFillColor(colors.HexColor('#1a2035'))
        c.setFont('Helvetica', 8.5)
        c.drawString(75 * mm, y - 4.8 * mm, str(value) if value else '—')
        c.setStrokeColor(colors.HexColor('#e2e5ef'))
        c.setLineWidth(0.3)
        c.line(14 * mm, y - rh, w - 14 * mm, y - rh)
        return y - rh

    def footer():
        c.setFillColor(colors.HexColor('#e2e5ef'))
        c.rect(0, 0, w, 10 * mm, fill=1, stroke=0)
        c.setFillColor(colors.HexColor('#7380a0'))
        c.setFont('Helvetica', 7)
        c.drawCentredString(
            w / 2, 3.8 * mm,
            f'SIPAT — Gerado em {datetime.now().strftime("%d/%m/%Y às %H:%M")} | '
            f'E-Fisco {shock.efisco}'
        )

    def new_page():
        footer()
        c.showPage()
        return h_page - 30 * mm

    # ── Cabeçalho ─────────────────────────────────────────────────────────────
    c.setFillColor(colors.HexColor('#1e2d42'))
    c.rect(0, h_page - 44 * mm, w, 44 * mm, fill=1, stroke=0)

    if logo_reader:
        c.drawImage(logo_reader, 14 * mm, h_page - 37 * mm, width=22 * mm, height=22 * mm, mask='auto')

    c.setFillColor(colors.white)
    c.setFont('Helvetica-Bold', 13)
    c.drawString(42 * mm, h_page - 18 * mm, 'MINISTÉRIO PÚBLICO DE PERNAMBUCO')
    c.setFont('Helvetica', 9)
    c.drawString(42 * mm, h_page - 25 * mm, 'SIPAT — Sistema Integrado Patrimonial')
    c.setFont('Helvetica-Bold', 10)
    c.drawString(42 * mm, h_page - 34 * mm, 'FICHA TÉCNICA DE BEM DE CONSUMO')

    c.setFont('Helvetica', 8)
    c.drawRightString(w - 14 * mm, h_page - 18 * mm, f'E-Fisco: {shock.efisco}')
    c.drawRightString(w - 14 * mm, h_page - 25 * mm, datetime.now().strftime('%d/%m/%Y %H:%M'))

    y = h_page - 57 * mm

    # ── Identificação ─────────────────────────────────────────────────────────
    y = section('Identificação do Item', y)
    for i, (lbl, val) in enumerate([
        ('Código E-Fisco',      shock.efisco),
        ('Descrição E-Fisco',   shock.descricao_efisco),
        ('Descrição Manual',    item.description_manual),
        ('Grupo',               shock.get_grupo_consumo_display() if shock.grupo_consumo else '—'),
        ('Unidade de Medida',   shock.get_medida_display() if shock.medida else '—'),
        ('Marca',               item.mark or '—'),
    ]):
        y = row(lbl, val, y, shade=(i % 2 == 1))

    y -= 6 * mm

    # ── Estoque ───────────────────────────────────────────────────────────────
    if y < 55 * mm:
        y = new_page()

    y = section('Dados de Estoque', y)
    validade_str = item.validity.strftime('%d/%m/%Y') if item.validity else '—'
    duracao_str  = str(item.duration) if item.duration else '—'
    for i, (lbl, val) in enumerate([
        ('Quantidade em Estoque', item.amount_shock),
        ('Consumo Mensal',        item.monthly_consumption or '—'),
        ('Duração Estimada',      duracao_str),
        ('Validade',              validade_str),
        ('Essencial',             'Sim' if item.essential else 'Não'),
        ('Forma de Entrada',      item.form_input or '—'),
        ('Método de Entrada',     item.method or '—'),
    ]):
        y = row(lbl, val, y, shade=(i % 2 == 1))

    y -= 6 * mm

    # ── Localização ───────────────────────────────────────────────────────────
    if y < 40 * mm:
        y = new_page()

    y = section('Localização', y)
    if item.locate:
        loc_vals = [
            ('Setor / Sala',           item.locate.setor_sala or '—'),
            ('Tipo de Armazenamento',  item.locate.get_tipo_localizacao_display() if hasattr(item.locate, 'get_tipo_localizacao_display') else (item.locate.tipo_localizacao or '—')),
        ]
    else:
        loc_vals = [('Localização', 'Não informada')]
    for i, (lbl, val) in enumerate(loc_vals):
        y = row(lbl, val, y, shade=(i % 2 == 1))

    y -= 6 * mm

    # ── Gestão ────────────────────────────────────────────────────────────────
    if y < 40 * mm:
        y = new_page()

    y = section('Informações de Gestão', y)
    cadastro_str  = item.created_at.strftime('%d/%m/%Y às %H:%M') if item.created_at else '—'
    atualizacao_str = item.updated_at.strftime('%d/%m/%Y às %H:%M') if item.updated_at else '—'
    editado_por   = '—'
    if item.updated_by:
        editado_por = item.updated_by.get_full_name() or item.updated_by.username
    for i, (lbl, val) in enumerate([
        ('Cadastrado em',       cadastro_str),
        ('Última Modificação',  atualizacao_str),
        ('Última Edição por',   editado_por),
    ]):
        y = row(lbl, val, y, shade=(i % 2 == 1))

    y -= 6 * mm

    # ── Foto ──────────────────────────────────────────────────────────────────
    if item.photo:
        try:
            photo_path = item.photo.path
            if os.path.exists(photo_path):
                max_img_h = 100 * mm
                max_img_w = w - 28 * mm

                if y < max_img_h + 30 * mm:
                    y = new_page()

                y = section('Foto do Item', y)

                from PIL import Image as PILImage
                with PILImage.open(photo_path) as pil_img:
                    orig_w, orig_h = pil_img.size

                ratio = orig_w / orig_h
                img_w = min(max_img_w, max_img_h * ratio)
                img_h = img_w / ratio
                if img_h > max_img_h:
                    img_h = max_img_h
                    img_w = img_h * ratio

                img_x = 14 * mm + (max_img_w - img_w) / 2
                img_y = y - img_h
                c.drawImage(ImageReader(photo_path), img_x, img_y, width=img_w, height=img_h, mask='auto')
                y = img_y - 8 * mm
        except Exception:
            pass

    footer()
    c.showPage()
    c.save()
    return resp


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
