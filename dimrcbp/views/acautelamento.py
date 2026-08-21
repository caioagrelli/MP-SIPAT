import os
from datetime import datetime

from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.contrib.staticfiles import finders
from django.db.models import Max, Q
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from dimrcbp.models import BensPermanentes, UseExternal, HistoricoMudanca
from dimrcbp.forms import UseExternalForm

ACAUTELAMENTOS_POR_PAGINA = 30


# ──────────────────────────────────────────────────────────────────────────────
# LISTA DE BENS EM ACAUTELAMENTO — mostra o acautelamento mais recente de cada bem
# ──────────────────────────────────────────────────────────────────────────────

@login_required
@permission_required('dimrcbp.view_benspermanentes', raise_exception=True)
def lista_acautelamentos(request):
    query = request.GET.get('q', '').strip()

    # um bem pode ter vários registros de acautelamento ao longo do tempo —
    # aqui pegamos só o mais recente de cada tombo
    ultimos_ids = (
        UseExternal.objects
        .values('tombo')
        .annotate(ultimo_id=Max('id'))
        .values_list('ultimo_id', flat=True)
    )
    qs = (
        UseExternal.objects
        .filter(id__in=ultimos_ids)
        .select_related('tombo__description', 'tombo__history_tombo__current_ua')
        .order_by('-date_renovation')
    )

    if query:
        qs = qs.filter(
            Q(tombo__tombo__icontains=query) |
            Q(responsible__icontains=query) |
            Q(registration_responsible__icontains=query) |
            Q(user__icontains=query)
        )

    total = qs.count()
    hoje = timezone.now().date()
    vencidos = qs.filter(date_renovation__lt=hoje).count()

    pagina = Paginator(qs, ACAUTELAMENTOS_POR_PAGINA).get_page(request.GET.get('pagina'))

    return render(request, 'dimrcbp/movimentacao/lista_acautelamentos.html', {
        'acautelamentos': pagina,
        'total': total,
        'vencidos': vencidos,
        'query': query,
        'hoje': hoje,
    })


# ──────────────────────────────────────────────────────────────────────────────
# ACAUTELAMENTO (USO EXTERNO) — atribui o bem a um responsável de uso externo
# ──────────────────────────────────────────────────────────────────────────────

@login_required
@permission_required('dimrcbp.change_benspermanentes', raise_exception=True)
def acautelamento(request, tombo):
    bem = get_object_or_404(
        BensPermanentes.objects.select_related('history_tombo__current_ua', 'description'),
        tombo=tombo,
    )

    if request.method == 'POST':
        form = UseExternalForm(request.POST)
        if form.is_valid():
            acautelamento = form.save(commit=False)
            acautelamento.tombo = bem
            acautelamento.save()

            # Registra também no histórico de alterações do bem, pra aparecer
            # junto com as demais edições na tela de detalhe.
            HistoricoMudanca.objects.create(
                bem=bem,
                alterado_por=request.user,
                justificativa='Acautelamento (uso externo) registrado.',
                campos={
                    'acautelamento': {
                        'label': 'Acautelamento (Uso Externo)',
                        'de': '—',
                        'para': f'{acautelamento.responsible} · renovação em {acautelamento.date_renovation:%d/%m/%Y}',
                    },
                },
            )

            messages.success(request, f'Acautelamento registrado para {acautelamento.responsible}.')
            return redirect('dimrcbp:bem_detalhe_admin', tombo=bem.tombo)
    else:
        form = UseExternalForm()

    historico = UseExternal.objects.filter(tombo=bem).order_by('-date_renovation')

    return render(request, 'dimrcbp/movimentacao/acautelamento.html', {
        'bem': bem,
        'form': form,
        'historico': historico,
    })


# ──────────────────────────────────────────────────────────────────────────────
# TERMO DE ACAUTELAMENTO — PDF pra assinatura do responsável pelo uso externo
# ──────────────────────────────────────────────────────────────────────────────

@login_required
@permission_required('dimrcbp.view_benspermanentes', raise_exception=True)
def termo_acautelamento(request, pk):
    ac = get_object_or_404(
        UseExternal.objects.select_related('tombo__description'),
        pk=pk,
    )

    logo_reader = None
    logo_path = finders.find('img/brasao-mppe.png')
    if logo_path and os.path.exists(logo_path):
        logo_reader = ImageReader(logo_path)

    resp = HttpResponse(content_type='application/pdf')
    resp['Content-Disposition'] = f'inline; filename="termo_acautelamento_{ac.pk}.pdf"'

    w, h_page = A4
    c = canvas.Canvas(resp, pagesize=A4)

    # ── Cabeçalho ──────────────────────────────────────────────────────────────
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
    c.drawString(42 * mm, h_page - 34 * mm, 'TERMO DE ACAUTELAMENTO (USO EXTERNO)')

    c.setFont('Helvetica', 8)
    c.drawRightString(w - 14 * mm, h_page - 18 * mm, f'Registro: #{ac.pk}')
    c.drawRightString(w - 14 * mm, h_page - 25 * mm, ac.date_renovation.strftime('Renovação: %d/%m/%Y'))

    y = h_page - 57 * mm

    # helpers
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

    # ── Identificação do Bem ─────────────────────────────────────────────────
    bem = ac.tombo
    y = section('Identificação do Bem', y)
    for i, (lbl, val) in enumerate([
        ('Tombo',          bem.tombo),
        ('Descrição',      str(bem.description)[:80]),
        ('Marca / Modelo', f'{bem.mark} — {bem.model}'),
        ('N° de Série',    bem.n_series or '—'),
        ('Situação',       bem.get_situacion_display() if bem.situacion else '—'),
        ('Estado',         bem.get_state_display()     if bem.state     else '—'),
    ]):
        y = row(lbl, val, y, shade=(i % 2 == 1))

    y -= 6 * mm

    # ── Responsável ──────────────────────────────────────────────────────────
    y = section('Responsável pelo Uso Externo', y)
    for i, (lbl, val) in enumerate([
        ('Nome',                ac.responsible),
        ('CPF',                 ac.cpf_responsible or '—'),
        ('Matrícula',           ac.registration_responsible),
        ('Contato',             ac.contact_responsible or '—'),
        ('Email',               ac.email_responsible or '—'),
        ('Data de Renovação',   ac.date_renovation.strftime('%d/%m/%Y')),
    ]):
        y = row(lbl, val, y, shade=(i % 2 == 1))

    # ── Usuário do bem (se diferente) ────────────────────────────────────────
    if ac.user:
        y -= 6 * mm
        y = section('Usuário do Bem', y)
        for i, (lbl, val) in enumerate([
            ('Nome',      ac.user),
            ('CPF',       ac.cpf_user or '—'),
            ('Telefone',  ac.phone_user or '—'),
            ('Email',     ac.email_user or '—'),
        ]):
            y = row(lbl, val, y, shade=(i % 2 == 1))

    y -= 20 * mm

    # ── Assinaturas ──────────────────────────────────────────────────────────
    if y < 55 * mm:
        c.showPage()
        y = h_page - 30 * mm

    sig_w = 75 * mm
    gap   = (w - 28 * mm - 2 * sig_w) / 3

    x1 = 14 * mm + gap
    c.setStrokeColor(colors.HexColor('#c8cfe0'))
    c.setLineWidth(0.6)
    c.line(x1, y, x1 + sig_w, y)
    c.setFillColor(colors.HexColor('#7380a0'))
    c.setFont('Helvetica', 7.5)
    c.drawCentredString(x1 + sig_w / 2, y - 5 * mm, ac.responsible[:40])
    c.drawCentredString(x1 + sig_w / 2, y - 9.5 * mm, 'Responsável pelo Uso Externo')

    x2 = x1 + sig_w + gap
    c.line(x2, y, x2 + sig_w, y)
    c.drawCentredString(x2 + sig_w / 2, y - 5 * mm, 'DIMRCBP')
    c.drawCentredString(x2 + sig_w / 2, y - 9.5 * mm, 'Ministério Público de Pernambuco')

    # ── Rodapé ───────────────────────────────────────────────────────────────
    c.setFillColor(colors.HexColor('#e2e5ef'))
    c.rect(0, 0, w, 10 * mm, fill=1, stroke=0)
    c.setFillColor(colors.HexColor('#7380a0'))
    c.setFont('Helvetica', 7)
    c.drawCentredString(
        w / 2, 3.8 * mm,
        f'SIPAT — Gerado em {datetime.now().strftime("%d/%m/%Y às %H:%M")} | '
        f'Tombo {bem.tombo} | Acautelamento #{ac.pk}'
    )

    c.showPage()
    c.save()
    return resp
