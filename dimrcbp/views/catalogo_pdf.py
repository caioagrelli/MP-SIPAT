import os
from datetime import datetime
from io import BytesIO

from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles import finders
from django.http import HttpResponse

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader

from dimrcbp.models import Catalogo


@login_required
def catalogo_pdf(request):
    # ── mesmos filtros da lista ───────────────────────────────────
    qs = Catalogo.objects.select_related(
        'description', 'description__type', 'description__type__gruop'
    )
    q_efisco    = request.GET.get('efisco', '').strip()
    q_descricao = request.GET.get('descricao', '').strip()
    q_grupo     = request.GET.get('grupo', '').strip()
    q_tipo      = request.GET.get('tipo', '').strip()

    if q_efisco:
        qs = qs.filter(efisco__icontains=q_efisco)
    if q_descricao:
        qs = qs.filter(description__description__icontains=q_descricao)
    if q_grupo:
        qs = qs.filter(description__type__gruop__pk=q_grupo)
    if q_tipo:
        qs = qs.filter(description__type__pk=q_tipo)

    itens = list(qs)

    # ── logo ─────────────────────────────────────────────────────
    logo_reader = None
    logo_path = finders.find('img/brasao-mppe.png')
    if logo_path and os.path.exists(logo_path):
        logo_reader = ImageReader(logo_path)

    resp = HttpResponse(content_type='application/pdf')
    resp['Content-Disposition'] = 'inline; filename="catalogo_bens.pdf"'

    PW, PH = A4
    c = canvas.Canvas(resp, pagesize=A4)

    MARGIN   = 14 * mm
    COL_GAP  = 10 * mm
    COLS     = 2
    col_w    = (PW - 2 * MARGIN - (COLS - 1) * COL_GAP) / COLS
    IMG_H    = 60 * mm
    CELL_H   = IMG_H + 52 * mm   # foto + texto

    TOP_BAR  = 38 * mm
    FOOTER_H = 10 * mm
    USABLE_H = PH - TOP_BAR - FOOTER_H - 6 * mm

    def draw_header(c, page_num):
        # barra azul
        c.setFillColor(colors.HexColor('#1e2d42'))
        c.rect(0, PH - TOP_BAR, PW, TOP_BAR, fill=1, stroke=0)

        if logo_reader:
            c.drawImage(logo_reader, MARGIN, PH - TOP_BAR + 6 * mm,
                        width=16 * mm, height=16 * mm, mask='auto')

        c.setFillColor(colors.white)
        c.setFont('Helvetica-Bold', 11)
        c.drawString(MARGIN + 20 * mm, PH - 16 * mm,
                     'MINISTÉRIO PÚBLICO DE PERNAMBUCO')
        c.setFont('Helvetica', 8)
        c.drawString(MARGIN + 20 * mm, PH - 22 * mm,
                     'SIPAT — Sistema Integrado Patrimonial')
        c.setFont('Helvetica-Bold', 9)
        c.drawString(MARGIN + 20 * mm, PH - 29 * mm,
                     'CATÁLOGO DE BENS PERMANENTES')

        c.setFont('Helvetica', 7.5)
        c.drawRightString(PW - MARGIN, PH - 16 * mm,
                          f'{len(itens)} item(ns)')
        c.drawRightString(PW - MARGIN, PH - 22 * mm,
                          datetime.now().strftime('%d/%m/%Y'))
        c.drawRightString(PW - MARGIN, PH - 28 * mm,
                          f'Página {page_num}')

    def draw_footer(c):
        c.setFillColor(colors.HexColor('#e2e5ef'))
        c.rect(0, 0, PW, FOOTER_H, fill=1, stroke=0)
        c.setFillColor(colors.HexColor('#7380a0'))
        c.setFont('Helvetica', 6.5)
        c.drawCentredString(
            PW / 2, 3.5 * mm,
            f'SIPAT — Catálogo de Bens Permanentes — '
            f'Gerado em {datetime.now().strftime("%d/%m/%Y às %H:%M")}',
        )

    def draw_cell(c, x, y, item):
        """Desenha um card de item com foto + dados. y = topo do card."""
        bw = col_w
        bh = CELL_H

        # borda arredondada simulada (ReportLab básico)
        c.setStrokeColor(colors.HexColor('#e2e5ef'))
        c.setLineWidth(0.5)
        c.roundRect(x, y - bh, bw, bh, 4, stroke=1, fill=0)

        # área da foto
        foto_x = x + 2 * mm
        foto_y = y - IMG_H - 2 * mm
        foto_w = bw - 4 * mm
        foto_h = IMG_H

        c.setFillColor(colors.HexColor('#f0f2f7'))
        c.rect(foto_x, foto_y, foto_w, foto_h, fill=1, stroke=0)

        if item.photo and item.photo.name:
            try:
                img_path = item.photo.path
                if os.path.exists(img_path):
                    ir = ImageReader(img_path)
                    iw, ih = ir.getSize()
                    ratio = min(foto_w / iw, foto_h / ih)
                    dw = iw * ratio
                    dh = ih * ratio
                    dx = foto_x + (foto_w - dw) / 2
                    dy = foto_y + (foto_h - dh) / 2
                    c.drawImage(ir, dx, dy, width=dw, height=dh, mask='auto')
            except Exception:
                pass

        # separador
        c.setStrokeColor(colors.HexColor('#e2e5ef'))
        c.setLineWidth(0.4)
        c.line(x, foto_y - 0.5 * mm, x + bw, foto_y - 0.5 * mm)

        # texto
        tx = x + 3 * mm
        ty = foto_y - 5 * mm

        # efisco badge
        efisco_txt = item.efisco
        c.setFillColor(colors.HexColor('#eff4ff'))
        efisco_box_w = min(len(efisco_txt) * 5.5 + 8, bw - 6 * mm)
        c.roundRect(tx - 1 * mm, ty - 4 * mm,
                    efisco_box_w, 6 * mm, 2, fill=1, stroke=0)
        c.setFillColor(colors.HexColor('#1d4ed8'))
        c.setFont('Helvetica-Bold', 8.5)
        c.drawString(tx, ty - 1.5 * mm, efisco_txt)

        ty -= 9 * mm

        # nome da descrição (tipo de bem)
        desc = str(item.description)
        c.setFillColor(colors.HexColor('#1a2035'))
        c.setFont('Helvetica-Bold', 10)
        chars_per_line = int((bw - 6 * mm) / 5.8)
        words = desc.split()
        line, lines = '', []
        for w in words:
            test = f'{line} {w}'.strip()
            if len(test) > chars_per_line:
                if line:
                    lines.append(line)
                line = w
            else:
                line = test
        if line:
            lines.append(line)
        for l in lines[:2]:
            c.drawString(tx, ty, l)
            ty -= 6 * mm

        ty -= 2 * mm

        # descrição livre (até 3 linhas)
        if item.descricao:
            dwords = item.descricao.split()
            dline, dlines = '', []
            for w in dwords:
                test = f'{dline} {w}'.strip()
                if len(test) > chars_per_line + 4:
                    if dline:
                        dlines.append(dline)
                    dline = w
                else:
                    dline = test
            if dline:
                dlines.append(dline)
            c.setFillColor(colors.HexColor('#3d4966'))
            c.setFont('Helvetica', 8)
            for dl in dlines[:3]:
                c.drawString(tx, ty, dl)
                ty -= 5 * mm
            ty -= 2 * mm

        # grupo › tipo
        grupo_tipo = f'{item.description.type.gruop} › {item.description.type}'
        c.setFillColor(colors.HexColor('#7380a0'))
        c.setFont('Helvetica', 8)
        c.drawString(tx, ty, grupo_tipo[:55])
        ty -= 7 * mm

        # valor
        if item.value:
            c.setFillColor(colors.HexColor('#15803d'))
            c.setFont('Helvetica-Bold', 10)
            c.drawString(tx, ty, f'R$ {item.value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'))

    # ── paginação ─────────────────────────────────────────────────
    page_num  = 1
    draw_header(c, page_num)
    draw_footer(c)

    row_gap = 6 * mm
    rows_per_page = int(USABLE_H // (CELL_H + row_gap))

    y_start = PH - TOP_BAR - 6 * mm

    idx = 0
    row_on_page = 0

    for item in itens:
        col = idx % COLS
        row = (idx // COLS) % rows_per_page

        if idx > 0 and col == 0 and row == 0:
            c.showPage()
            page_num += 1
            draw_header(c, page_num)
            draw_footer(c)

        x = MARGIN + col * (col_w + COL_GAP)
        y = y_start - row * (CELL_H + row_gap)

        draw_cell(c, x, y, item)
        idx += 1

    c.showPage()
    c.save()
    return resp
