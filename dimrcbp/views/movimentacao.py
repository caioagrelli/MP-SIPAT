import os
from datetime import datetime
from io import BytesIO

from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.contrib.staticfiles import finders
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from dimrcbp.models import (
    BensPermanentes,
    SolicitacaoTransferencia,
    MovimentacaoBem,
)
from dempam.models import InfoUA


# ──────────────────────────────────────────────────────────────────────────────
# LISTA GERAL DE SOLICITAÇÕES (painel estilo DIMMS)
# ──────────────────────────────────────────────────────────────────────────────

@login_required
@permission_required('dimrcbp.view_benspermanentes', raise_exception=True)
def lista_solicitacoes(request):
    query         = request.GET.get('q', '').strip()
    filtro_status = request.GET.get('status', 'PENDENTE').strip()

    qs = (
        SolicitacaoTransferencia.objects
        .select_related('bem__description', 'solicitante', 'ua_destino', 'decidido_por')
        .order_by('-data')
    )

    if filtro_status:
        qs = qs.filter(status=filtro_status)

    if query:
        qs = qs.filter(
            Q(codigo__icontains=query)               |
            Q(bem__tombo__icontains=query)           |
            Q(motivo__icontains=query)               |
            Q(solicitante__first_name__icontains=query) |
            Q(solicitante__last_name__icontains=query)  |
            Q(solicitante__username__icontains=query)
        )

    base = SolicitacaoTransferencia.objects
    context = {
        'solicitacoes':    qs,
        'total':           qs.count(),
        'filtro_status':   filtro_status,
        'query':           query,
        'total_pendente':  base.filter(status='PENDENTE').count(),
        'total_aprovada':  base.filter(status='APROVADA').count(),
        'total_rejeitada': base.filter(status='REJEITADA').count(),
        'total_cancelada': base.filter(status='CANCELADA').count(),
    }
    return render(request, 'dimrcbp/movimentacao/lista.html', context)


# ──────────────────────────────────────────────────────────────────────────────
# CRIAR SOLICITAÇÃO DE TRANSFERÊNCIA
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def criar_solicitacao(request):
    tombo = request.GET.get('tombo', '').strip()
    bem_pre = None
    if tombo:
        bem_pre = BensPermanentes.objects.filter(tombo=tombo).first()

    if request.method == 'POST':
        bem_ids    = request.POST.getlist('bem')
        ua_dest_id = request.POST.get('ua_destino')
        motivo     = request.POST.get('motivo', '').strip()

        errors = []
        if not bem_ids:
            errors.append('Selecione ao menos um bem.')
        if not ua_dest_id:
            errors.append('Selecione a UA destino.')
        if not motivo:
            errors.append('Informe o motivo.')

        bens_validos = []
        if not errors:
            ua_destino = get_object_or_404(InfoUA, pk=ua_dest_id)
            for bid in bem_ids:
                bem = get_object_or_404(BensPermanentes, pk=bid)
                if SolicitacaoTransferencia.objects.filter(bem=bem, status='PENDENTE').exists():
                    errors.append(f'Já existe uma solicitação pendente para o bem {bem.tombo}.')
                else:
                    bens_validos.append(bem)

        if not errors:
            for bem in bens_validos:
                SolicitacaoTransferencia.objects.create(
                    bem=bem,
                    ua_destino=ua_destino,
                    solicitante=request.user,
                    motivo=motivo,
                )
            qty = len(bens_validos)
            messages.success(request, f'{qty} solicitação(ões) de transferência criada(s) com sucesso.')
            return redirect('dimrcbp:lista_solicitacoes')

        for e in errors:
            messages.error(request, e)

    bens  = BensPermanentes.objects.select_related('description').order_by('tombo')
    uas   = InfoUA.objects.select_related('circunscricao_predio').order_by('ua')
    context = {
        'bens':    bens,
        'uas':     uas,
        'bem_pre': bem_pre,
    }
    return render(request, 'dimrcbp/movimentacao/criar_solicitacao.html', context)


# ──────────────────────────────────────────────────────────────────────────────
# ANALISAR / DECIDIR SOLICITAÇÃO
# ──────────────────────────────────────────────────────────────────────────────

@login_required
@permission_required('dimrcbp.change_benspermanentes', raise_exception=True)
def analisar_solicitacao(request, pk):
    sol = get_object_or_404(
        SolicitacaoTransferencia.objects.select_related(
            'bem__description', 'bem__history_tombo__current_ua',
            'solicitante', 'ua_destino',
        ),
        pk=pk,
    )

    if request.method == 'POST':
        decisao    = request.POST.get('decisao')
        obs        = request.POST.get('obs_decisao', '').strip()

        if decisao not in ('APROVADA', 'REJEITADA'):
            messages.error(request, 'Decisão inválida.')
            return redirect('dimrcbp:analisar_solicitacao', pk=pk)

        if sol.status != 'PENDENTE':
            messages.warning(request, 'Esta solicitação já foi decidida.')
            return redirect('dimrcbp:lista_solicitacoes')

        sol.status      = decisao
        sol.obs_decisao = obs
        sol.decidido_por = request.user
        sol.data_decisao = timezone.now()
        sol.save()

        if decisao == 'APROVADA':
            ua_origem = None
            try:
                ua_origem = sol.bem.history_tombo.current_ua
            except Exception:
                pass

            mov = MovimentacaoBem.objects.create(
                bem=sol.bem,
                ua_origem=ua_origem,
                ua_destino=sol.ua_destino,
                responsavel=request.user,
                motivo=f'Via solicitação {sol.codigo}. {obs}'.strip('. '),
                solicitacao=sol,
            )
            messages.success(request, f'Solicitação aprovada. Transferência {mov.codigo} registrada.')
            return redirect('dimrcbp:termo_transferencia', pk=mov.pk)

        messages.info(request, 'Solicitação rejeitada.')
        return redirect('dimrcbp:lista_solicitacoes')

    context = {'sol': sol}
    return render(request, 'dimrcbp/movimentacao/analisar.html', context)


# ──────────────────────────────────────────────────────────────────────────────
# TRANSFERÊNCIA DIRETA (sem solicitação)
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def transferir_bem(request, tombo):
    bem = get_object_or_404(
        BensPermanentes.objects.select_related('history_tombo__current_ua', 'description'),
        tombo=tombo,
    )

    if request.method == 'POST':
        ua_dest_id = request.POST.get('ua_destino')
        motivo     = request.POST.get('motivo', '').strip()

        if not ua_dest_id:
            messages.error(request, 'Selecione a UA destino.')
        else:
            ua_destino = get_object_or_404(InfoUA, pk=ua_dest_id)
            ua_origem  = None
            try:
                ua_origem = bem.history_tombo.current_ua
            except Exception:
                pass

            mov = MovimentacaoBem.objects.create(
                bem=bem,
                ua_origem=ua_origem,
                ua_destino=ua_destino,
                responsavel=request.user,
                motivo=motivo,
            )
            messages.success(request, f'Bem transferido com sucesso. Código: {mov.codigo}')
            return redirect('dimrcbp:termo_transferencia', pk=mov.pk)

    return render(request, 'dimrcbp/movimentacao/transferir.html', {'bem': bem})


# ──────────────────────────────────────────────────────────────────────────────
# LISTA DE MOVIMENTAÇÕES DE UM BEM
# ──────────────────────────────────────────────────────────────────────────────

@login_required
@permission_required('dimrcbp.view_benspermanentes', raise_exception=True)
def historico_movimentacoes(request, tombo):
    bem = get_object_or_404(BensPermanentes.objects.select_related('description'), tombo=tombo)
    movimentacoes = (
        bem.movimentacoes
        .select_related('ua_origem', 'ua_destino', 'responsavel', 'solicitacao')
        .order_by('-data')
    )
    context = {'bem': bem, 'movimentacoes': movimentacoes}
    return render(request, 'dimrcbp/movimentacao/historico.html', context)


# ──────────────────────────────────────────────────────────────────────────────
# TERMO DE TRANSFERÊNCIA (PDF)
# ──────────────────────────────────────────────────────────────────────────────

@login_required
@permission_required('dimrcbp.view_benspermanentes', raise_exception=True)
def termo_transferencia(request, pk):
    mov = get_object_or_404(
        MovimentacaoBem.objects.select_related(
            'bem__description', 'ua_origem', 'ua_destino',
            'responsavel', 'solicitacao__solicitante',
        ),
        pk=pk,
    )

    logo_reader = None
    logo_path = finders.find('img/brasao-mppe.png')
    if logo_path and os.path.exists(logo_path):
        logo_reader = ImageReader(logo_path)

    resp = HttpResponse(content_type='application/pdf')
    resp['Content-Disposition'] = (
        f'inline; filename="termo_transferencia_{mov.codigo}.pdf"'
    )

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
    c.drawString(42 * mm, h_page - 34 * mm, 'TERMO DE TRANSFERÊNCIA DE BEM PERMANENTE')

    c.setFont('Helvetica', 8)
    c.drawRightString(w - 14 * mm, h_page - 18 * mm, f'Código: {mov.codigo}')
    c.drawRightString(w - 14 * mm, h_page - 25 * mm, mov.data.strftime('%d/%m/%Y %H:%M'))

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

    # ── Identificação do Bem ────────────────────────────────────────────────────
    bem = mov.bem
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

    # ── Movimentação ───────────────────────────────────────────────────────────
    y = section('Dados da Transferência', y)
    ua_origem_str  = mov.ua_origem.ua  if mov.ua_origem  else 'Não informada'
    ua_destino_str = mov.ua_destino.ua if mov.ua_destino else '—'
    resp_nome = mov.responsavel.get_full_name() or mov.responsavel.username
    for i, (lbl, val) in enumerate([
        ('Código da Transferência', mov.codigo),
        ('Data',                   mov.data.strftime('%d/%m/%Y às %H:%M')),
        ('UA Origem',              ua_origem_str),
        ('UA Destino',             ua_destino_str),
        ('Responsável',            resp_nome),
        ('Solicitação Origem',     mov.solicitacao.codigo if mov.solicitacao else 'Transferência direta'),
    ]):
        y = row(lbl, val, y, shade=(i % 2 == 1))

    if mov.motivo:
        y -= 2 * mm
        c.setFillColor(colors.HexColor('#7380a0'))
        c.setFont('Helvetica-Bold', 7.5)
        c.drawString(17 * mm, y - 4.8 * mm, 'MOTIVO')
        y -= 7 * mm
        c.setFillColor(colors.HexColor('#1a2035'))
        c.setFont('Helvetica', 8)
        text = mov.motivo[:300]
        c.drawString(17 * mm, y, text)
        y -= 10 * mm

    y -= 10 * mm

    # ── Assinaturas ────────────────────────────────────────────────────────────
    if y < 70 * mm:
        c.showPage()
        y = h_page - 30 * mm

    sig_w = 75 * mm
    gap   = (w - 28 * mm - 2 * sig_w) / 3

    # UA Origem
    x1 = 14 * mm + gap
    c.setStrokeColor(colors.HexColor('#c8cfe0'))
    c.setLineWidth(0.6)
    c.line(x1, y, x1 + sig_w, y)
    c.setFillColor(colors.HexColor('#7380a0'))
    c.setFont('Helvetica', 7.5)
    c.drawCentredString(x1 + sig_w / 2, y - 5  * mm, ua_origem_str[:40])
    c.drawCentredString(x1 + sig_w / 2, y - 9.5 * mm, 'UA Cedente — Responsável')

    # UA Destino
    x2 = x1 + sig_w + gap
    c.line(x2, y, x2 + sig_w, y)
    c.drawCentredString(x2 + sig_w / 2, y - 5  * mm, ua_destino_str[:40])
    c.drawCentredString(x2 + sig_w / 2, y - 9.5 * mm, 'UA Receptora — Responsável')

    # ── Rodapé ─────────────────────────────────────────────────────────────────
    c.setFillColor(colors.HexColor('#e2e5ef'))
    c.rect(0, 0, w, 10 * mm, fill=1, stroke=0)
    c.setFillColor(colors.HexColor('#7380a0'))
    c.setFont('Helvetica', 7)
    c.drawCentredString(
        w / 2, 3.8 * mm,
        f'SIPAT — Gerado em {datetime.now().strftime("%d/%m/%Y às %H:%M")} | '
        f'Tombo {bem.tombo} | Transferência {mov.codigo}'
    )

    c.showPage()
    c.save()
    return resp
