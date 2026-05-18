import os
from datetime import datetime
from io import BytesIO

from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.staticfiles import finders
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader

from dimrcbp.models import HistoricoMudanca


@login_required
@permission_required('dimrcbp.view_benspermanentes', raise_exception=True)
def relatorio_mudanca(request, pk):
    h = get_object_or_404(
        HistoricoMudanca.objects.select_related('bem__description', 'alterado_por'),
        pk=pk,
    )

    logo_reader = None
    logo_path = finders.find('img/brasao-mppe.png')
    if logo_path and os.path.exists(logo_path):
        logo_reader = ImageReader(logo_path)

    resp = HttpResponse(content_type='application/pdf')
    resp['Content-Disposition'] = f'inline; filename="alteracao_tombo_{h.bem.tombo}_{pk}.pdf"'

    w, h_page = A4
    c = canvas.Canvas(resp, pagesize=A4)

    # ── Cabeçalho ──────────────────────────────────────────────
    c.setFillColor(colors.HexColor('#1e2d42'))
    c.rect(0, h_page - 42 * mm, w, 42 * mm, fill=1, stroke=0)

    if logo_reader:
        c.drawImage(logo_reader, 14 * mm, h_page - 36 * mm, width=20 * mm, height=20 * mm, mask='auto')

    c.setFillColor(colors.white)
    c.setFont('Helvetica-Bold', 13)
    c.drawString(40 * mm, h_page - 18 * mm, 'MINISTÉRIO PÚBLICO DE PERNAMBUCO')
    c.setFont('Helvetica', 9)
    c.drawString(40 * mm, h_page - 25 * mm, 'SIPAT — Sistema Integrado Patrimonial')
    c.setFont('Helvetica-Bold', 10)
    c.drawString(40 * mm, h_page - 33 * mm, 'TERMO DE ALTERAÇÃO DE BEM PERMANENTE')

    c.setFont('Helvetica', 8)
    c.drawRightString(w - 14 * mm, h_page - 18 * mm, f'Registro #{h.pk}')
    c.drawRightString(w - 14 * mm, h_page - 25 * mm, h.data.strftime('%d/%m/%Y %H:%M'))

    y = h_page - 55 * mm

    # ── Seção: Bem ─────────────────────────────────────────────
    def section(c, y, title):
        c.setFillColor(colors.HexColor('#1e2d42'))
        c.rect(14 * mm, y - 7 * mm, w - 28 * mm, 8 * mm, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont('Helvetica-Bold', 8.5)
        c.drawString(17 * mm, y - 4.5 * mm, title.upper())
        return y - 15 * mm

    def row(c, y, label, value, shade=False):
        rh = 7 * mm
        if shade:
            c.setFillColor(colors.HexColor('#f7f8fc'))
            c.rect(14 * mm, y - rh, w - 28 * mm, rh, fill=1, stroke=0)
        c.setFillColor(colors.HexColor('#7380a0'))
        c.setFont('Helvetica-Bold', 7.5)
        c.drawString(17 * mm, y - 4.8 * mm, label.upper())
        c.setFillColor(colors.HexColor('#1a2035'))
        c.setFont('Helvetica', 8.5)
        c.drawString(72 * mm, y - 4.8 * mm, str(value) if value else '—')
        c.setStrokeColor(colors.HexColor('#e2e5ef'))
        c.setLineWidth(0.3)
        c.line(14 * mm, y - rh, w - 14 * mm, y - rh)
        return y - rh

    y = section(c, y, 'Identificação do Bem')
    bem = h.bem
    for i, (lbl, val) in enumerate([
        ('Tombo',          bem.tombo),
        ('Descrição',      str(bem.description)[:80]),
        ('Marca / Modelo', f'{bem.mark} — {bem.model}'),
        ('N° de Série',    bem.n_series or '—'),
    ]):
        y = row(c, y, lbl, val, shade=(i % 2 == 1))

    y -= 6 * mm

    # ── Seção: Alteração ───────────────────────────────────────
    y = section(c, y, 'Dados da Alteração')
    for i, (lbl, val) in enumerate([
        ('Alterado por', h.alterado_por.get_full_name() or h.alterado_por.username),
        ('Data',         h.data.strftime('%d/%m/%Y às %H:%M')),
        ('Campos',       f'{len(h.campos)} campo(s) modificado(s)'),
    ]):
        y = row(c, y, lbl, val, shade=(i % 2 == 1))

    y -= 6 * mm

    # ── Tabela de diff ─────────────────────────────────────────
    y = section(c, y, 'Campos Alterados')

    # cabeçalho da tabela
    col_w = (w - 28 * mm) / 3
    c.setFillColor(colors.HexColor('#eff4ff'))
    c.rect(14 * mm, y - 7 * mm, w - 28 * mm, 7 * mm, fill=1, stroke=0)
    c.setFillColor(colors.HexColor('#1d4ed8'))
    c.setFont('Helvetica-Bold', 7.5)
    c.drawString(17 * mm,                   y - 4.5 * mm, 'CAMPO')
    c.drawString(17 * mm + col_w,           y - 4.5 * mm, 'VALOR ANTERIOR')
    c.drawString(17 * mm + col_w * 2,       y - 4.5 * mm, 'NOVO VALOR')
    y -= 7 * mm

    for i, (campo, info) in enumerate(h.campos.items()):
        rh = 8 * mm
        if i % 2 == 0:
            c.setFillColor(colors.HexColor('#f7f8fc'))
            c.rect(14 * mm, y - rh, w - 28 * mm, rh, fill=1, stroke=0)

        c.setFillColor(colors.HexColor('#3d4966'))
        c.setFont('Helvetica-Bold', 8)
        c.drawString(17 * mm, y - 5.5 * mm, info.get('label', campo))

        c.setFillColor(colors.HexColor('#b91c1c'))
        c.setFont('Helvetica', 8)
        c.drawString(17 * mm + col_w, y - 5.5 * mm, str(info.get('de', '') or '—')[:38])

        c.setFillColor(colors.HexColor('#15803d'))
        c.setFont('Helvetica-Bold', 8)
        c.drawString(17 * mm + col_w * 2, y - 5.5 * mm, str(info.get('para', ''))[:38])

        c.setStrokeColor(colors.HexColor('#e2e5ef'))
        c.setLineWidth(0.3)
        c.line(14 * mm, y - rh, w - 14 * mm, y - rh)
        y -= rh

    # ── Assinatura ─────────────────────────────────────────────
    y -= 16 * mm
    if y < 45 * mm:
        c.showPage()
        y = h_page - 30 * mm

    sig_w = 70 * mm
    c.setStrokeColor(colors.HexColor('#c8cfe0'))
    c.setLineWidth(0.6)
    c.line(14 * mm, y, 14 * mm + sig_w, y)
    c.setFillColor(colors.HexColor('#7380a0'))
    c.setFont('Helvetica', 7.5)
    nome = h.alterado_por.get_full_name() or h.alterado_por.username
    c.drawCentredString(14 * mm + sig_w / 2, y - 5 * mm, nome)
    c.drawCentredString(14 * mm + sig_w / 2, y - 9.5 * mm, 'Responsável pela Alteração')

    # ── Rodapé ─────────────────────────────────────────────────
    c.setFillColor(colors.HexColor('#e2e5ef'))
    c.rect(0, 0, w, 10 * mm, fill=1, stroke=0)
    c.setFillColor(colors.HexColor('#7380a0'))
    c.setFont('Helvetica', 7)
    c.drawCentredString(
        w / 2, 3.8 * mm,
        f'SIPAT — Gerado em {datetime.now().strftime("%d/%m/%Y às %H:%M")} | '
        f'Tombo {bem.tombo} | Alteração #{h.pk}'
    )

    c.showPage()
    c.save()
    return resp
