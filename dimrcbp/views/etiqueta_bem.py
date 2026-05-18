import os
from io import BytesIO

from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.staticfiles import finders
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse

import qrcode
from qrcode.constants import ERROR_CORRECT_M

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import mm
from reportlab.lib.utils import ImageReader

from dimrcbp.models import BensPermanentes


@login_required
@permission_required('dimrcbp.view_benspermanentes', raise_exception=True)
def etiqueta_bem(request, tombo):
    bem = get_object_or_404(BensPermanentes.objects.select_related('description'), tombo=tombo)

    url = request.build_absolute_uri(
        reverse('dimrcbp:bem_detalhe_admin', args=[bem.tombo])
    )

    # QR code
    qr = qrcode.QRCode(error_correction=ERROR_CORRECT_M, box_size=10, border=1)
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color='black', back_color='white')
    qr_buf = BytesIO()
    qr_img.save(qr_buf, format='PNG')
    qr_buf.seek(0)
    qr_reader = ImageReader(qr_buf)

    # Logo
    logo_reader = None
    logo_path = finders.find('img/brasao-mppe.png')
    if logo_path and os.path.exists(logo_path):
        logo_reader = ImageReader(logo_path)

    desc_text = str(bem.description)[:50]
    safe_tombo = ''.join(ch for ch in bem.tombo if ch.isalnum() or ch in ('-', '_'))

    # PDF 80×50 mm
    w, h = 80 * mm, 50 * mm
    resp = HttpResponse(content_type='application/pdf')
    resp['Content-Disposition'] = f'inline; filename="etiqueta_{safe_tombo}.pdf"'

    c = canvas.Canvas(resp, pagesize=(w, h))

    # Fundo branco
    c.setFillColorRGB(1, 1, 1)
    c.rect(0, 0, w, h, fill=1, stroke=0)

    m = 3 * mm

    # Logo
    if logo_reader:
        c.drawImage(logo_reader, m, h - 16 * mm, width=13 * mm, height=13 * mm, mask='auto')

    # Faixa superior escura
    c.setFillColorRGB(0.12, 0.18, 0.26)
    c.rect(0, h - 16 * mm, w, 16 * mm, fill=1, stroke=0)

    # Logo sobre a faixa
    if logo_reader:
        c.drawImage(logo_reader, m, h - 14 * mm, width=11 * mm, height=11 * mm, mask='auto')

    # Título na faixa
    c.setFillColorRGB(1, 1, 1)
    c.setFont('Helvetica-Bold', 7)
    c.drawString(16 * mm, h - 7 * mm, 'MPPE — Patrimônio')
    c.setFont('Helvetica', 6)
    c.drawString(16 * mm, h - 11 * mm, 'Sistema Integrado Patrimonial')

    # Tombo em destaque (direita da faixa)
    c.setFont('Helvetica-Bold', 10)
    c.drawRightString(w - m, h - 9 * mm, f'Tombo: {bem.tombo}')

    # QR (esquerda, corpo)
    qr_size = 28 * mm
    c.drawImage(qr_reader, m, m, width=qr_size, height=qr_size, mask='auto')

    # Descrição + marca/modelo (direita do QR)
    x_text = m + qr_size + 3 * mm
    c.setFillColorRGB(0.1, 0.13, 0.2)
    c.setFont('Helvetica-Bold', 6.5)
    # Quebra de linha manual para descrição longa
    words = desc_text.split()
    line, lines = '', []
    for w_word in words:
        test = f'{line} {w_word}'.strip()
        if c.stringWidth(test, 'Helvetica-Bold', 6.5) < (w - x_text - m):
            line = test
        else:
            lines.append(line)
            line = w_word
    if line:
        lines.append(line)

    y = h - 20 * mm
    for ln in lines[:3]:
        c.drawString(x_text, y, ln)
        y -= 7

    c.setFont('Helvetica', 6)
    c.setFillColorRGB(0.3, 0.38, 0.5)
    c.drawString(x_text, y - 2, f'{bem.mark} — {bem.model}')
    c.drawString(x_text, y - 9, f'N° Série: {bem.n_series or "—"}')

    c.showPage()
    c.save()
    return resp
