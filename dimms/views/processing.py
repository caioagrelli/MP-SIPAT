# bibliotecas padrões do Python
import json
import os
import unicodedata
from datetime import datetime

# Importações padrões do Django Unchained   'What kind of dentist are you?' - Quentin Tarantino
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.contrib.staticfiles import finders

#bibliotecas externas
import qrcode
from io import BytesIO
from qrcode.constants import ERROR_CORRECT_M
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm

from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

# Importações do Código
from ..models import Solicitacao, Tramitacao, Estoque
from ..forms import (
    SolicitacaoForm, SolicitacaoItemFormSet, TramitacaoCreateForm, SolicitacaoStatusUpdateForm,
    SolicitacaoEditForm, ReceberSolicitacaoForm, AnexarTermoAssinadoForm,
)
from ..utils import StatusTramitacao, parse_quantidade
from dempam.models import InfoUA


def _normalizar_busca(texto):
    """Maiúsculo e sem acento, pra comparar 'promotoria' com 'PROMOTÓRIA' etc."""
    if not texto:
        return ''
    sem_acento = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')
    return sem_acento.upper()

# =========================================================
# CAMPOS DESTINADOS PARA GERENCIAR/VISUALIZAR SOLICITAÇÕES
# =========================================================


''' Solicitações '''
# Página Principal
@login_required
def processing(request):
    query        = request.GET.get('q', '').strip()
    filtro_status = request.GET.get('status', '').strip()

    # Base: exclui rascunhos de outros usuários
    solicitacoes = (
        Solicitacao.objects
        .select_related('ua_order', 'user_responsible')
        .filter(
            Q(situation='RASCUNHO', user_responsible=request.user) |
            ~Q(situation='RASCUNHO')
        )
        .order_by('-data_order')
    )

    if query:
        query_normalizado = _normalizar_busca(query)
        uas_compativeis = [
            ua.pk for ua in InfoUA.objects.only('pk', 'ua', 'sigla')
            if query_normalizado in _normalizar_busca(ua.sigla) or query_normalizado in _normalizar_busca(ua.ua)
        ]
        solicitacoes = solicitacoes.filter(
            Q(request_code__icontains=query)             |
            Q(numero_pe_integrado__icontains=query)       |
            Q(user_order__icontains=query)               |
            Q(observation_order__icontains=query)        |
            Q(user_responsible__username__icontains=query)   |
            Q(user_responsible__first_name__icontains=query) |
            Q(user_responsible__last_name__icontains=query)  |
            Q(ua_order_id__in=uas_compativeis)
        )

    if filtro_status:
        solicitacoes = solicitacoes.filter(situation=filtro_status)

    # Anexa última tramitação em cada solicitação
    for s in solicitacoes:
        s.ultima_tramitacao = s.tramitacao.order_by('-date_update', '-id').first()

    # KPIs — calculados sobre o queryset já filtrado (sem rascunhos alheios)
    base_kpi = (
        Solicitacao.objects
        .filter(
            Q(situation='RASCUNHO', user_responsible=request.user) |
            ~Q(situation='RASCUNHO')
        )
    )

    context = {
        'tramitacoes':     solicitacoes,
        'query':           query,
        'filtro_status':   filtro_status,

        'total_tramitacoes': solicitacoes.count(),

        'total_atendimento':          base_kpi.filter(situation='ATENDIMENTO').count(),
        'total_aguardando_separacao': base_kpi.filter(situation='AGUAR_SEPARACAO').count(),
        'total_separada':             base_kpi.filter(situation='SEPARADA').count(),
        'total_expedicao':            base_kpi.filter(situation='EXPEDICAO').count(),
        'total_recebida':             base_kpi.filter(situation='RECEBIDA').count(),
        'total_cancelada':            base_kpi.filter(situation='CANCELADA').count(),
        'total_rascunho':             base_kpi.filter(situation='RASCUNHO', user_responsible=request.user).count(),
    }

    return render(request, 'dimms/processing/processing.html', context)

# Detalhes de cada Solicitação (Página Individual)
@login_required
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

    tramitacao_recebimento = (
        historico_tramitacao.filter(update=StatusTramitacao.recebida).last()
    )

    etapas_fluxo = [
        {"codigo": "ATENDIMENTO", "label": "Em atendimento"},
        {"codigo": "AGUAR_SEPARACAO", "label": "Aguardando separação"},
        {"codigo": "SEPARADA", "label": "Separada"},
        {"codigo": "EXPEDICAO", "label": "Em expedição"},
        {"codigo": "RECEBIDA", "label": "Recebida"},
    ]

    ordem_status = {
        "ATENDIMENTO": 0,
        "AGUAR_SEPARACAO": 1,
        "SEPARADA": 2,
        "EXPEDICAO": 3,
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
        'tramitacao_recebimento': tramitacao_recebimento,
        'anexar_termo_form': AnexarTermoAssinadoForm(),
    }

    return render(request, 'dimms/processing/details_processing.html', context)

# Detalhe de cada Etapa da solicitação (Página Individual)
@login_required
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

    return render(request, "dimms/processing/course.html", context)

# Comprovante PDF de uma etapa de tramitação
@login_required
def comprovante_tramitacao(request, solicitacao_pk, tramitacao_pk):
    solicitacao = get_object_or_404(
        Solicitacao.objects.select_related('ua_order', 'user_responsible'),
        pk=solicitacao_pk,
    )
    tramitacao = get_object_or_404(
        Tramitacao.objects.select_related('request_update', 'user_update'),
        pk=tramitacao_pk,
        request_update=solicitacao,
    )

    logo_reader = None
    logo_path = finders.find('img/brasao-mppe.png')
    if logo_path and os.path.exists(logo_path):
        logo_reader = ImageReader(logo_path)

    resp = HttpResponse(content_type='application/pdf')
    safe_code = "".join(c for c in str(solicitacao.request_code) if c.isalnum() or c in ('-', '_'))
    resp['Content-Disposition'] = f'inline; filename="comprovante_{safe_code}_etapa{tramitacao.pk}.pdf"'

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
            f'{solicitacao.request_code} | Etapa #{tramitacao.pk}'
        )

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
    c.drawString(42 * mm, h_page - 34 * mm, 'COMPROVANTE DE ETAPA DE TRAMITAÇÃO')

    c.setFont('Helvetica', 8)
    c.drawRightString(w - 14 * mm, h_page - 18 * mm, f'Solicitação: {solicitacao.request_code}')
    c.drawRightString(w - 14 * mm, h_page - 25 * mm, f'Etapa #: {tramitacao.pk}')
    if tramitacao.date_update:
        c.drawRightString(w - 14 * mm, h_page - 32 * mm, tramitacao.date_update.strftime('%d/%m/%Y %H:%M'))

    y = h_page - 57 * mm

    # ── Dados da Solicitação ──────────────────────────────────────────────────
    y = section('Dados da Solicitação', y)
    user_resp = solicitacao.user_responsible
    resp_nome = user_resp.get_full_name() or user_resp.username if user_resp else '—'
    for i, (lbl, val) in enumerate([
        ('Código',              solicitacao.request_code),
        ('UA Solicitante',      str(solicitacao.ua_order) if solicitacao.ua_order else '—'),
        ('Usuário Solicitante', solicitacao.user_order or '—'),
        ('Responsável',         resp_nome),
        ('Situação Atual',      solicitacao.get_situation_display() if hasattr(solicitacao, 'get_situation_display') else solicitacao.situation),
    ]):
        y = row(lbl, val, y, shade=(i % 2 == 1))

    y -= 6 * mm

    # ── Dados da Etapa ────────────────────────────────────────────────────────
    y = section('Dados da Etapa', y)
    registrado_por = '—'
    if tramitacao.user_update:
        registrado_por = tramitacao.user_update.get_full_name() or tramitacao.user_update.username
    data_str = tramitacao.date_update.strftime('%d/%m/%Y às %H:%M') if tramitacao.date_update else '—'
    etapa_display = tramitacao.get_update_display() if hasattr(tramitacao, 'get_update_display') else tramitacao.update
    linhas_etapa = [
        ('ID da Etapa',              f'#{tramitacao.pk}'),
        ('Status / Etapa',           etapa_display or '—'),
        ('Data de Registro',         data_str),
        ('Registrado por',           registrado_por),
        ('Responsável Operacional',  tramitacao.responsible_update or '—'),
    ]
    if tramitacao.matricula_recebedor or tramitacao.cargo_recebedor or tramitacao.empresa_orgao_recebedor:
        linhas_etapa += [
            ('Matrícula de Quem Recebeu',       tramitacao.matricula_recebedor or '—'),
            ('Cargo/Função de Quem Recebeu',    tramitacao.cargo_recebedor or '—'),
            ('Empresa/Órgão de Quem Recebeu',   tramitacao.empresa_orgao_recebedor or '—'),
        ]
    for i, (lbl, val) in enumerate(linhas_etapa):
        y = row(lbl, val, y, shade=(i % 2 == 1))

    y -= 6 * mm

    # ── Observação ────────────────────────────────────────────────────────────
    if tramitacao.observation_update:
        if y < 50 * mm:
            footer()
            c.showPage()
            y = h_page - 30 * mm

        y = section('Observação', y)
        obs_text = tramitacao.observation_update or ''
        c.setFillColor(colors.HexColor('#1a2035'))
        c.setFont('Helvetica', 8.5)
        max_w = w - 34 * mm
        words = obs_text.replace('\r\n', '\n').replace('\r', '\n')
        from reportlab.lib.utils import simpleSplit
        lines = []
        for paragraph in words.split('\n'):
            lines += simpleSplit(paragraph, 'Helvetica', 8.5, max_w) or ['']
        for line in lines[:20]:
            if y < 20 * mm:
                footer()
                c.showPage()
                y = h_page - 30 * mm
            c.drawString(17 * mm, y - 4 * mm, line)
            y -= 6 * mm
        y -= 4 * mm

    # ── Foto ──────────────────────────────────────────────────────────────────
    if tramitacao.photo_update:
        try:
            photo_path = tramitacao.photo_update.path
            if os.path.exists(photo_path):
                max_img_h = 150 * mm
                max_img_w = w - 28 * mm

                if y < max_img_h + 30 * mm:
                    footer()
                    c.showPage()
                    y = h_page - 30 * mm

                y = section('Foto / Evidência Visual', y)

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

    # ── Assinatura ────────────────────────────────────────────────────────────
    if y < 60 * mm:
        footer()
        c.showPage()
        y = h_page - 30 * mm

    y -= 10 * mm
    sig_w = 80 * mm
    sig_x = (w - sig_w) / 2

    c.setStrokeColor(colors.HexColor('#c8cfe0'))
    c.setLineWidth(0.6)
    c.line(sig_x, y, sig_x + sig_w, y)
    c.setFillColor(colors.HexColor('#7380a0'))
    c.setFont('Helvetica', 7.5)
    c.drawCentredString(sig_x + sig_w / 2, y - 5 * mm, registrado_por)
    c.drawCentredString(sig_x + sig_w / 2, y - 9.5 * mm, 'Responsável pela Atualização')

    footer()
    c.showPage()
    c.save()
    return resp


# PDF completo da solicitação
@login_required
def pdf_solicitacao(request, pk):
    from reportlab.lib.utils import simpleSplit

    solicitacao = get_object_or_404(
        Solicitacao.objects.select_related('ua_order', 'user_responsible'),
        pk=pk,
    )
    itens = (
        solicitacao.bens_solicitados
        .select_related('item_order__item_shock')
        .all()
    )
    tramitacoes = (
        solicitacao.tramitacao
        .select_related('user_update')
        .order_by('date_update', 'id')
    )

    logo_reader = None
    logo_path = finders.find('img/brasao-mppe.png')
    if logo_path and os.path.exists(logo_path):
        logo_reader = ImageReader(logo_path)

    resp = HttpResponse(content_type='application/pdf')
    safe_code = "".join(c for c in str(solicitacao.request_code) if c.isalnum() or c in ('-', '_'))
    resp['Content-Disposition'] = f'inline; filename="solicitacao_{safe_code}.pdf"'

    w, h_page = A4
    cv = canvas.Canvas(resp, pagesize=A4)

    # ── helpers ───────────────────────────────────────────────────────────────
    def draw_footer(page_num):
        cv.setFillColor(colors.HexColor('#e2e5ef'))
        cv.rect(0, 0, w, 10 * mm, fill=1, stroke=0)
        cv.setFillColor(colors.HexColor('#7380a0'))
        cv.setFont('Helvetica', 7)
        cv.drawCentredString(
            w / 2, 3.8 * mm,
            f'SIPAT — Gerado em {datetime.now().strftime("%d/%m/%Y às %H:%M")} | '
            f'{solicitacao.request_code} | Pág. {page_num}'
        )

    def section(title, y):
        cv.setFillColor(colors.HexColor('#1e2d42'))
        cv.rect(14 * mm, y - 7 * mm, w - 28 * mm, 8 * mm, fill=1, stroke=0)
        cv.setFillColor(colors.white)
        cv.setFont('Helvetica-Bold', 8.5)
        cv.drawString(17 * mm, y - 4.5 * mm, title.upper())
        return y - 15 * mm

    def row(label, value, y, shade=False):
        rh = 7 * mm
        if shade:
            cv.setFillColor(colors.HexColor('#f7f8fc'))
            cv.rect(14 * mm, y - rh, w - 28 * mm, rh, fill=1, stroke=0)
        cv.setFillColor(colors.HexColor('#7380a0'))
        cv.setFont('Helvetica-Bold', 7.5)
        cv.drawString(17 * mm, y - 4.8 * mm, label.upper())
        cv.setFillColor(colors.HexColor('#1a2035'))
        cv.setFont('Helvetica', 8.5)
        cv.drawString(75 * mm, y - 4.8 * mm, str(value) if value else '—')
        cv.setStrokeColor(colors.HexColor('#e2e5ef'))
        cv.setLineWidth(0.3)
        cv.line(14 * mm, y - rh, w - 14 * mm, y - rh)
        return y - rh

    def check_page(y, page_num, needed=20):
        if y < needed * mm:
            draw_footer(page_num)
            cv.showPage()
            page_num += 1
            _draw_header(page_num)
            y = h_page - 32 * mm
        return y, page_num

    def _draw_header(page_num):
        cv.setFillColor(colors.HexColor('#1e2d42'))
        cv.rect(0, h_page - 22 * mm, w, 22 * mm, fill=1, stroke=0)
        if logo_reader:
            cv.drawImage(logo_reader, 14 * mm, h_page - 18 * mm, width=12 * mm, height=12 * mm, mask='auto')
        cv.setFillColor(colors.white)
        cv.setFont('Helvetica-Bold', 10)
        cv.drawString(30 * mm, h_page - 11 * mm, 'MINISTÉRIO PÚBLICO DE PERNAMBUCO — SIPAT')
        cv.setFont('Helvetica', 8)
        cv.drawString(30 * mm, h_page - 17 * mm, f'Solicitação: {solicitacao.request_code}')
        cv.setFont('Helvetica', 7.5)
        cv.drawRightString(w - 14 * mm, h_page - 11 * mm, f'Pág. {page_num}')
        cv.drawRightString(w - 14 * mm, h_page - 17 * mm, datetime.now().strftime('%d/%m/%Y %H:%M'))

    # ── Capa / Cabeçalho principal (pág. 1) ──────────────────────────────────
    page_num = 1
    cv.setFillColor(colors.HexColor('#1e2d42'))
    cv.rect(0, h_page - 44 * mm, w, 44 * mm, fill=1, stroke=0)

    if logo_reader:
        cv.drawImage(logo_reader, 14 * mm, h_page - 37 * mm, width=22 * mm, height=22 * mm, mask='auto')

    cv.setFillColor(colors.white)
    cv.setFont('Helvetica-Bold', 13)
    cv.drawString(42 * mm, h_page - 18 * mm, 'MINISTÉRIO PÚBLICO DE PERNAMBUCO')
    cv.setFont('Helvetica', 9)
    cv.drawString(42 * mm, h_page - 25 * mm, 'SIPAT — Sistema Integrado Patrimonial')
    cv.setFont('Helvetica-Bold', 10)
    cv.drawString(42 * mm, h_page - 34 * mm, 'SOLICITAÇÃO DE MATERIAL DE CONSUMO')

    cv.setFont('Helvetica', 8)
    cv.drawRightString(w - 14 * mm, h_page - 18 * mm, f'Código: {solicitacao.request_code}')
    cv.drawRightString(w - 14 * mm, h_page - 25 * mm, f'Data: {solicitacao.data_order.strftime("%d/%m/%Y") if solicitacao.data_order else "—"}')
    cv.drawRightString(w - 14 * mm, h_page - 32 * mm, f'Situação: {solicitacao.get_situation_display()}')

    y = h_page - 57 * mm

    # ── Dados da Solicitação ──────────────────────────────────────────────────
    y = section('Dados da Solicitação', y)
    resp_nome = '—'
    if solicitacao.user_responsible:
        resp_nome = solicitacao.user_responsible.get_full_name() or solicitacao.user_responsible.username
    for i, (lbl, val) in enumerate([
        ('Código',           solicitacao.request_code),
        ('UA Solicitante',   str(solicitacao.ua_order) if solicitacao.ua_order else '—'),
        ('Usuário',          solicitacao.user_order or '—'),
        ('Responsável',      resp_nome),
        ('Data',             solicitacao.data_order.strftime('%d/%m/%Y %H:%M') if solicitacao.data_order else '—'),
        ('Situação Atual',   solicitacao.get_situation_display()),
        ('Observação',       solicitacao.observation_order or '—'),
    ]):
        y, page_num = check_page(y, page_num)
        y = row(lbl, val, y, shade=(i % 2 == 1))

    y -= 6 * mm

    # ── Itens Solicitados ─────────────────────────────────────────────────────
    y, page_num = check_page(y, page_num, needed=30)
    y = section('Itens Solicitados', y)

    # cabeçalho da tabela
    col_efisco = 17 * mm
    col_desc   = 42 * mm
    col_qty    = w - 40 * mm
    col_unit   = w - 25 * mm

    cv.setFillColor(colors.HexColor('#f0f2f7'))
    cv.rect(14 * mm, y - 7 * mm, w - 28 * mm, 7 * mm, fill=1, stroke=0)
    cv.setFillColor(colors.HexColor('#3d4966'))
    cv.setFont('Helvetica-Bold', 7.5)
    cv.drawString(col_efisco, y - 4.5 * mm, 'E-FISCO')
    cv.drawString(col_desc,   y - 4.5 * mm, 'DESCRIÇÃO')
    cv.drawRightString(col_qty,  y - 4.5 * mm, 'QTD')
    cv.drawRightString(col_unit, y - 4.5 * mm, 'UNID.')
    cv.setStrokeColor(colors.HexColor('#e2e5ef'))
    cv.setLineWidth(0.3)
    cv.line(14 * mm, y - 7 * mm, w - 14 * mm, y - 7 * mm)
    y -= 7 * mm

    for i, item in enumerate(itens):
        y, page_num = check_page(y, page_num)
        rh = 7 * mm
        if i % 2 == 1:
            cv.setFillColor(colors.HexColor('#f7f8fc'))
            cv.rect(14 * mm, y - rh, w - 28 * mm, rh, fill=1, stroke=0)
        efisco = str(item.item_order.item_shock.efisco) if item.item_order and item.item_order.item_shock else '—'
        desc   = str(item.item_order.item_shock.descricao_efisco) if item.item_order and item.item_order.item_shock else '—'
        unid   = str(item.item_order.item_shock.medida) if item.item_order and item.item_order.item_shock else '—'
        qty    = str(item.amount_order)

        # trunca descrição se necessário
        max_desc_w = col_qty - col_desc - 4 * mm
        desc_lines = simpleSplit(desc, 'Helvetica', 8, max_desc_w)
        desc_short = desc_lines[0] if desc_lines else desc

        cv.setFillColor(colors.HexColor('#1a2035'))
        cv.setFont('Helvetica', 8)
        cv.drawString(col_efisco, y - 4.8 * mm, efisco)
        cv.drawString(col_desc,   y - 4.8 * mm, desc_short)
        cv.setFont('Helvetica-Bold', 8)
        cv.drawRightString(col_qty,  y - 4.8 * mm, qty)
        cv.setFont('Helvetica', 8)
        cv.drawRightString(col_unit, y - 4.8 * mm, unid)

        cv.setStrokeColor(colors.HexColor('#e2e5ef'))
        cv.setLineWidth(0.3)
        cv.line(14 * mm, y - rh, w - 14 * mm, y - rh)
        y -= rh

    y -= 6 * mm

    # ── Histórico de Tramitação ───────────────────────────────────────────────
    y, page_num = check_page(y, page_num, needed=30)
    y = section('Histórico de Tramitação', y)

    for t_idx, tram in enumerate(tramitacoes):
        y, page_num = check_page(y, page_num, needed=28)

        registrado = '—'
        if tram.user_update:
            registrado = tram.user_update.get_full_name() or tram.user_update.username
        data_str = tram.date_update.strftime('%d/%m/%Y %H:%M') if tram.date_update else '—'
        etapa    = tram.get_update_display() if hasattr(tram, 'get_update_display') else tram.update

        for i, (lbl, val) in enumerate([
            (f'Etapa #{tram.pk} — Status', etapa or '—'),
            ('Data', data_str),
            ('Registrado por', registrado),
            ('Responsável operacional', tram.responsible_update or '—'),
        ]):
            y, page_num = check_page(y, page_num)
            y = row(lbl, val, y, shade=(i % 2 == 1))

        if tram.observation_update:
            y, page_num = check_page(y, page_num)
            obs_lines = simpleSplit(tram.observation_update.replace('\r\n', ' ').replace('\n', ' '),
                                    'Helvetica', 8, w - 34 * mm)
            for line in obs_lines[:5]:
                y, page_num = check_page(y, page_num)
                cv.setFillColor(colors.HexColor('#1a2035'))
                cv.setFont('Helvetica-Oblique', 8)
                cv.drawString(17 * mm, y - 4 * mm, line)
                y -= 6 * mm

        # separador entre etapas
        if t_idx < tramitacoes.count() - 1:
            cv.setStrokeColor(colors.HexColor('#c8cfe0'))
            cv.setLineWidth(0.5)
            cv.line(14 * mm, y - 2 * mm, w - 14 * mm, y - 2 * mm)
            y -= 8 * mm

    draw_footer(page_num)
    cv.showPage()
    cv.save()
    return resp


# Leitura de Guia de Remessa (PDF → JSON)
@login_required
def parse_guia_remessa(request):
    import re
    import pdfplumber

    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método inválido.'}, status=405)

    pdf_file = request.FILES.get('pdf')
    if not pdf_file:
        return JsonResponse({'ok': False, 'error': 'Nenhum arquivo enviado.'}, status=400)

    try:
        ua_nome       = ''
        requisitante  = ''
        efiscos_qtds  = {}   # {efisco_str: quantidade_int}

        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        if not row or len(row) < 2:
                            continue
                        cell0 = str(row[0] or '').strip()
                        cell1 = str(row[1] or '').strip()

                        # Linha de detalhes: UA
                        if 'unidade administrativa' in cell0.lower() or 'unidade adm' in cell0.lower():
                            ua_nome = cell1

                        # Linha de itens: extrai requisitante e E-Fisco/quantidade
                        # Formato: "REQ.xxx / Requisitante: NOME"
                        if 'requisitante:' in cell0.lower():
                            match = re.search(r'[Rr]equisitante:\s*(.+)', cell0)
                            if match:
                                requisitante = match.group(1).strip().title()

                        # Linhas de item: coluna 0 = código, coluna 1 = descrição, coluna 3 = quantidade
                        if len(row) >= 4:
                            desc = str(row[1] or '')
                            qty_raw = str(row[3] or '').strip()
                            efisco_match = re.search(r'\((\d{7})\)', desc)
                            if efisco_match and qty_raw:
                                efisco = efisco_match.group(1)
                                try:
                                    qty = parse_quantidade(qty_raw)
                                except (ValueError, TypeError):
                                    qty = 0
                                if qty > 0:
                                    efiscos_qtds[efisco] = efiscos_qtds.get(efisco, 0) + qty

        if not efiscos_qtds:
            return JsonResponse({'ok': False, 'error': 'Nenhum item encontrado no PDF. Verifique se é uma Guia de Remessa válida.'})

        # Busca os Estoques correspondentes aos E-Fiscos encontrados
        estoques = (
            Estoque.objects
            .select_related('item_shock')
            .filter(item_shock__efisco__in=list(efiscos_qtds.keys()))
        )

        itens_encontrados = []
        nao_encontrados   = []

        efisco_para_estoque = {e.item_shock.efisco: e for e in estoques}

        for efisco, qty in efiscos_qtds.items():
            estoque = efisco_para_estoque.get(efisco)
            if estoque:
                itens_encontrados.append({
                    'id':           estoque.pk,
                    'efisco':       estoque.item_shock.efisco,
                    'descricao':    estoque.item_shock.descricao_efisco,
                    'amount_shock': estoque.amount_shock,
                    'amount_order': min(qty, estoque.amount_shock),
                })
            else:
                nao_encontrados.append(efisco)

        # Tenta encontrar a UA pelo nome
        from dempam.models import InfoUA
        ua_obj = None
        if ua_nome:
            # busca por correspondência parcial case-insensitive
            ua_obj = InfoUA.objects.filter(ua__icontains=ua_nome).first()
            if not ua_obj:
                # tenta com as primeiras palavras
                palavras = ua_nome.split()[:3]
                for p in palavras:
                    ua_obj = InfoUA.objects.filter(ua__icontains=p).first()
                    if ua_obj:
                        break

        return JsonResponse({
            'ok': True,
            'ua': {'id': ua_obj.pk, 'nome': ua_obj.ua} if ua_obj else {'id': None, 'nome': ua_nome},
            'requisitante': requisitante,
            'itens': itens_encontrados,
            'nao_encontrados': nao_encontrados,
        })

    except Exception as exc:
        return JsonResponse({'ok': False, 'error': f'Erro ao processar PDF: {exc}'}, status=500)


# Criar uma nova solicitação
@login_required
def create_request(request):
    if request.method == 'POST':
        form = SolicitacaoForm(request.POST, request.FILES)
        formset = SolicitacaoItemFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            solicitacao = form.save(commit=False)
            solicitacao.user_responsible = request.user
            solicitacao.save()

            formset.instance = solicitacao
            formset.save()

            Tramitacao.objects.create(
                request_update=solicitacao,
                update=solicitacao.situation,
                responsible_update=request.user.get_full_name() or request.user.username,
                user_update=request.user,
            )

            messages.success(request, 'Solicitação criada com sucesso.')
            return redirect('dimms:processing')
    else:
        form = SolicitacaoForm()
        formset = SolicitacaoItemFormSet()

    # Constrói lista de itens para repopular o JS após erro de validação
    initial_items = None
    if request.method == 'POST':
        items = []
        for f in formset.forms:
            item_pk = f['item_order'].value()
            if item_pk:
                try:
                    estoque = Estoque.objects.select_related('item_shock').get(pk=item_pk)
                    items.append({
                        'id': estoque.pk,
                        'efisco': estoque.item_shock.efisco,
                        'descricao': estoque.item_shock.descricao_efisco,
                        'amount_shock': str(estoque.amount_shock),
                        'amount_order': f['amount_order'].value() or '',
                    })
                except Estoque.DoesNotExist:
                    items.append(None)
            else:
                items.append(None)
        initial_items = json.dumps(items)

    context = {
        'form': form,
        'formset': formset,
        'initial_items': initial_items,
    }
    return render(request, 'dimms/processing/create_request.html', context)

# Atualizar status de uma solicitação (Pode escolher qual solicitação atualizar)
@login_required
def create_update(request):
    if request.method == 'POST':
        form = TramitacaoCreateForm(request.POST, request.FILES)

        if form.is_valid():
            tramitacao = form.save(commit=False)
            tramitacao.user_update = request.user

            if not tramitacao.responsible_update:
                tramitacao.responsible_update = (
                    request.user.get_full_name() or request.user.username
                )

            tramitacao.save()

            messages.success(request, 'Tramitação registrada com sucesso.')
            return redirect('dimms:processing')
    else:
        form = TramitacaoCreateForm()

    ultimas_solicitacoes = Solicitacao.objects.select_related('ua_order').order_by('-data_order')[:8]

    context = {
        'form': form,
        'ultimas_solicitacoes': ultimas_solicitacoes,
    }
    return render(request, 'dimms/processing/create_update.html', context)

# Registrar o recebimento de uma solicitação (quem recebeu + foto) e virar "Recebida"
@login_required
def receber_solicitacao(request, pk):
    solicitacao = get_object_or_404(Solicitacao, pk=pk)

    if request.method == 'POST':
        form = ReceberSolicitacaoForm(request.POST, request.FILES)
        if form.is_valid():
            tramitacao = Tramitacao.objects.create(
                request_update=solicitacao,
                update=StatusTramitacao.recebida,
                responsible_update=form.cleaned_data['nome_recebedor'],
                photo_update=form.cleaned_data.get('foto_recebedor'),
                matricula_recebedor=form.cleaned_data.get('matricula_recebedor', ''),
                cargo_recebedor=form.cleaned_data.get('cargo_recebedor', ''),
                empresa_orgao_recebedor=form.cleaned_data.get('empresa_orgao_recebedor', ''),
                user_update=request.user,
            )
            messages.success(request, 'Recebimento registrado com sucesso.')
            return redirect('dimms:receber_confirmacao', solicitacao_pk=solicitacao.pk, tramitacao_pk=tramitacao.pk)
    else:
        form = ReceberSolicitacaoForm()

    return render(request, 'dimms/processing/receber_solicitacao.html', {
        'form': form,
        'solicitacao': solicitacao,
    })


# Registrar o recebimento de várias solicitações separadas de uma vez só —
# um recebedor, uma foto, aplicados a todas as selecionadas
@login_required
def receber_lote(request):
    fila = (
        Solicitacao.objects
        .filter(situation=StatusTramitacao.separada)
        .select_related('ua_order')
        .order_by('-data_order')
    )

    if request.method == 'POST':
        ids_selecionados = request.POST.getlist('solicitacoes')
        nome_recebedor = request.POST.get('nome_recebedor', '').strip()
        matricula_recebedor = request.POST.get('matricula_recebedor', '').strip()
        cargo_recebedor = request.POST.get('cargo_recebedor', '').strip()
        empresa_orgao_recebedor = request.POST.get('empresa_orgao_recebedor', '').strip()
        foto = request.FILES.get('foto_recebedor')

        if not ids_selecionados:
            messages.error(request, 'Selecione ao menos uma solicitação para receber.')
            return redirect('dimms:receber_lote')
        if not nome_recebedor:
            messages.error(request, 'Informe o nome de quem vai receber.')
            return redirect('dimms:receber_lote')

        solicitacoes = list(
            Solicitacao.objects.filter(pk__in=ids_selecionados, situation=StatusTramitacao.separada)
        )
        if not solicitacoes:
            messages.error(request, 'As solicitações selecionadas não estão mais disponíveis para recebimento.')
            return redirect('dimms:receber_lote')

        foto_bytes = None
        foto_ext = '.jpg'
        if foto:
            foto_bytes = foto.read()
            foto_ext = os.path.splitext(foto.name)[1] or '.jpg'

        with transaction.atomic():
            for solicitacao in solicitacoes:
                Tramitacao.objects.create(
                    request_update=solicitacao,
                    update=StatusTramitacao.recebida,
                    responsible_update=nome_recebedor,
                    photo_update=ContentFile(foto_bytes, name=f'foto{foto_ext}') if foto_bytes else None,
                    matricula_recebedor=matricula_recebedor,
                    cargo_recebedor=cargo_recebedor,
                    empresa_orgao_recebedor=empresa_orgao_recebedor,
                    user_update=request.user,
                )

        messages.success(request, f'{len(solicitacoes)} solicitação(ões) recebida(s) com sucesso.')
        return redirect('dimms:almoxarifado_acesso_rapido')

    return render(request, 'dimms/processing/receber_lote.html', {
        'fila': fila,
    })


# Página de confirmação logo após registrar o recebimento — abre o termo em PDF
# pra assinar e já deixa pronto pra anexar o termo assinado de volta
@login_required
def receber_confirmacao(request, solicitacao_pk, tramitacao_pk):
    solicitacao = get_object_or_404(Solicitacao, pk=solicitacao_pk)
    tramitacao = get_object_or_404(
        Tramitacao, pk=tramitacao_pk, request_update=solicitacao,
    )

    return render(request, 'dimms/processing/receber_confirmacao.html', {
        'solicitacao': solicitacao,
        'tramitacao': tramitacao,
        'anexar_termo_form': AnexarTermoAssinadoForm(),
    })


# PDF do termo de recebimento de uma solicitação recebida
@login_required
def pdf_termo_recebimento(request, solicitacao_pk, tramitacao_pk):
    solicitacao = get_object_or_404(
        Solicitacao.objects.select_related('ua_order'),
        pk=solicitacao_pk,
    )
    tramitacao = get_object_or_404(
        Tramitacao.objects.select_related('request_update'),
        pk=tramitacao_pk,
        request_update=solicitacao,
    )
    itens = (
        solicitacao.bens_solicitados
        .select_related('item_order__item_shock')
        .all()
    )

    logo_reader = None
    logo_path = finders.find('img/brasao-mppe.png')
    if logo_path and os.path.exists(logo_path):
        logo_reader = ImageReader(logo_path)

    resp = HttpResponse(content_type='application/pdf')
    safe_code = "".join(ch for ch in str(solicitacao.request_code) if ch.isalnum() or ch in ('-', '_'))
    resp['Content-Disposition'] = f'inline; filename="termo_recebimento_{safe_code}.pdf"'

    w, h_page = A4
    c = canvas.Canvas(resp, pagesize=A4)

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
            f'{solicitacao.request_code} | Termo de Recebimento'
        )

    # ── Cabeçalho ─────────────────────────────────────────────────────────
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
    c.drawString(42 * mm, h_page - 34 * mm, 'TERMO DE RECEBIMENTO DE MATERIAL')

    c.setFont('Helvetica', 8)
    c.drawRightString(w - 14 * mm, h_page - 18 * mm, f'Solicitação: {solicitacao.request_code}')
    if tramitacao.date_update:
        c.drawRightString(w - 14 * mm, h_page - 25 * mm, tramitacao.date_update.strftime('%d/%m/%Y %H:%M'))

    y = h_page - 57 * mm

    # ── Dados da Solicitação ──────────────────────────────────────────────
    y = section('Dados da Solicitação', y)
    for i, (lbl, val) in enumerate([
        ('Código',              solicitacao.request_code),
        ('UA Solicitante',      str(solicitacao.ua_order) if solicitacao.ua_order else '—'),
        ('Usuário Solicitante', solicitacao.user_order or '—'),
        ('Recebido por',        tramitacao.responsible_update or '—'),
        ('Data do Recebimento', tramitacao.date_update.strftime('%d/%m/%Y às %H:%M') if tramitacao.date_update else '—'),
    ]):
        y = row(lbl, val, y, shade=(i % 2 == 1))

    y -= 6 * mm

    # ── Itens Recebidos ─────────────────────────────────────────────────────
    if y < 60 * mm:
        footer()
        c.showPage()
        y = h_page - 30 * mm

    y = section('Itens Recebidos', y)
    c.setFillColor(colors.HexColor('#7380a0'))
    c.setFont('Helvetica-Bold', 7)
    c.drawString(17 * mm, y - 4.5 * mm, 'E-FISCO')
    c.drawString(45 * mm, y - 4.5 * mm, 'DESCRIÇÃO')
    c.drawRightString(w - 17 * mm, y - 4.5 * mm, 'QUANTIDADE')
    y -= 8 * mm
    c.setStrokeColor(colors.HexColor('#e2e5ef'))
    c.setLineWidth(0.3)

    for idx, item in enumerate(itens):
        if y < 25 * mm:
            footer()
            c.showPage()
            y = h_page - 30 * mm
        rh = 7 * mm
        if idx % 2 == 1:
            c.setFillColor(colors.HexColor('#f7f8fc'))
            c.rect(14 * mm, y - rh, w - 28 * mm, rh, fill=1, stroke=0)
        c.setFillColor(colors.HexColor('#1a2035'))
        c.setFont('Helvetica', 8)
        efisco = item.item_order.item_shock.efisco if item.item_order and item.item_order.item_shock else '—'
        descricao = str(item.item_order) if item.item_order else '—'
        c.drawString(17 * mm, y - 4.8 * mm, str(efisco))
        c.drawString(45 * mm, y - 4.8 * mm, descricao[:55])
        c.drawRightString(w - 17 * mm, y - 4.8 * mm, str(item.amount_order or '—'))
        c.line(14 * mm, y - rh, w - 14 * mm, y - rh)
        y -= rh

    y -= 8 * mm

    # ── Assinaturas ──────────────────────────────────────────────────────────
    if y < 45 * mm:
        footer()
        c.showPage()
        y = h_page - 30 * mm

    y -= 10 * mm
    sig_w = (w - 40 * mm) / 2
    c.setStrokeColor(colors.HexColor('#c8cfe0'))
    c.setLineWidth(0.6)

    c.line(14 * mm, y, 14 * mm + sig_w, y)
    c.setFillColor(colors.HexColor('#7380a0'))
    c.setFont('Helvetica', 7.5)
    c.drawCentredString(14 * mm + sig_w / 2, y - 5 * mm, solicitacao.user_order or str(solicitacao.ua_order or ''))
    c.drawCentredString(14 * mm + sig_w / 2, y - 9.5 * mm, 'SOLICITANTE')

    c.line(w - 14 * mm - sig_w, y, w - 14 * mm, y)
    c.drawCentredString(w - 14 * mm - sig_w / 2, y - 5 * mm, tramitacao.responsible_update or '')
    c.drawCentredString(w - 14 * mm - sig_w / 2, y - 9.5 * mm, 'RECEBEDOR')

    footer()
    c.showPage()
    c.save()
    return resp


# Anexar o termo de recebimento já assinado (upload posterior)
@login_required
def anexar_termo_assinado(request, solicitacao_pk, tramitacao_pk):
    solicitacao = get_object_or_404(Solicitacao, pk=solicitacao_pk)
    tramitacao = get_object_or_404(
        Tramitacao, pk=tramitacao_pk, request_update=solicitacao,
    )

    if request.method == 'POST':
        form = AnexarTermoAssinadoForm(request.POST, request.FILES)
        if form.is_valid():
            tramitacao.documents_update = form.cleaned_data['termo_assinado']
            tramitacao.save(update_fields=['documents_update'])
            messages.success(request, 'Termo de recebimento assinado anexado com sucesso.')
        else:
            messages.error(request, 'Selecione um arquivo válido para anexar.')

    return redirect('dimms:details_processing', pk=solicitacao.pk)


# Atualizar solicitações a partir delas (Não pode escolher / quando está na pagina individual)
@login_required
def update_request(request, pk):
    solicitacao = get_object_or_404(Solicitacao, pk=pk)

    if request.method == 'POST':
        form = SolicitacaoStatusUpdateForm(request.POST, request.FILES, instance=solicitacao)

        if form.is_valid():
            novo_status = form.cleaned_data['situation']

            observacao = form.cleaned_data.get('observacao_tramitacao')
            documento = form.cleaned_data.get('documents_update')
            foto = form.cleaned_data.get('photo_update')

            # não salvar o form diretamente no Solicitacao: quem atualiza o
            # `situation` precisa ser o Tramitacao.save(), pois é lá que a
            # baixa automática de estoque compara o status antes/depois
            Tramitacao.objects.create(
                request_update=solicitacao,
                update=novo_status,
                responsible_update=request.user.get_full_name() or request.user.username,
                observation_update=observacao,
                documents_update=documento,
                photo_update=foto,
                user_update=request.user,
            )

            messages.success(request, 'Solicitação atualizada com sucesso.')
            return redirect('dimms:details_processing', pk=solicitacao.pk)
    else:
        form = SolicitacaoStatusUpdateForm(instance=solicitacao)

    historico = solicitacao.tramitacao.order_by('-date_update', '-id')[:10]

    context = {
        'form': form,
        'solicitacao': solicitacao,
        'historico': historico,
    }
    return render(request, 'dimms/processing/update_request.html', context)

# Separação de itens: marca quais bens já foram fisicamente separados e finaliza a etapa
@login_required
def separar_solicitacao(request, pk):
    solicitacao = get_object_or_404(Solicitacao, pk=pk)

    itens = (
        solicitacao.bens_solicitados
        .select_related(
            'item_order__item_shock',
            'item_order__locate__setor_sala',
        )
        .prefetch_related('item_order__outras_localizacoes__setor_sala')
        .all()
    )

    pode_separar = solicitacao.situation in (StatusTramitacao.atendimento, StatusTramitacao.aguar_separada)

    if request.method == 'POST' and pode_separar:
        marcados = set(request.POST.getlist('item_separado'))

        for item in itens:
            item.separado = str(item.pk) in marcados
            item.save(update_fields=['separado'])

        if request.POST.get('acao') == 'finalizar':
            Tramitacao.objects.create(
                request_update=solicitacao,
                update=StatusTramitacao.separada,
                responsible_update=request.user.get_full_name() or request.user.username,
                user_update=request.user,
            )
            messages.success(request, 'Solicitação marcada como Separada.')
            return redirect('dimms:details_processing', pk=solicitacao.pk)

        messages.success(request, 'Progresso da separação salvo.')
        return redirect('dimms:separar_solicitacao', pk=solicitacao.pk)

    context = {
        'solicitacao': solicitacao,
        'itens': itens,
        'pode_separar': pode_separar,
        'total_itens': itens.count(),
        'total_separados': sum(1 for i in itens if i.separado),
    }
    return render(request, 'dimms/processing/separar.html', context)


# qrcode da página de update geral (sendo a partir de uma solicitação)
@login_required
def qrcode_update(request, pk):
    url = request.build_absolute_uri(
        reverse('dimms:update_request', args=[pk])
    )

    img = qrcode.make(url)

    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    return HttpResponse(buffer.getvalue(), content_type='image/png')

# Qr code da página de update específica da solicitação
@login_required
def label_update(request, pk):
    solicitacao = get_object_or_404(Solicitacao, pk=pk)

    url = request.build_absolute_uri(
        reverse("dimms:update_request", args=[solicitacao.pk])
    )

    # --- QR ---
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

    # --- Logo ---
    logo_reader = None
    logo_path = finders.find("img/brasao-mppe.png")
    if logo_path and os.path.exists(logo_path):
        logo_reader = ImageReader(logo_path)

    # --- Dados ---
    request_code = solicitacao.request_code or f"SOL-{solicitacao.pk}"
    safe_code = "".join(
        ch for ch in str(request_code) if ch.isalnum() or ch in ("-", "_")
    ) or f"solicitacao_{solicitacao.pk}"

    # --- PDF A4 paisagem ---
    w, h = landscape(A4)

    resp = HttpResponse(content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="etiqueta_{safe_code}.pdf"'

    c = canvas.Canvas(resp, pagesize=landscape(A4))

    # Fundo
    c.setFillColorRGB(1, 1, 1)
    c.rect(0, 0, w, h, fill=1, stroke=0)

    # Margem geral
    m = 22 * mm

    # Área útil
    inner_x = m
    inner_y = m
    inner_w = w - (2 * m)
    inner_h = h - (2 * m)


    # =========================
    # BLOCO SUPERIOR
    # =========================
    logo_x = inner_x + 18 * mm
    logo_y = h - m - 40 * mm
    logo_w = 34 * mm
    logo_h = 34 * mm

    if logo_reader:
        c.drawImage(
            logo_reader,
            logo_x,
            logo_y,
            width=logo_w,
            height=logo_h,
            mask="auto"
        )

    text_x = logo_x + logo_w + 12 * mm
    title_y = h - m - 18 * mm
    code_y = h - m - 38 * mm

    # Título
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica", 24)
    c.drawString(text_x, title_y, "Etiqueta da Solicitação")

    # Código
    c.setFont("Helvetica-Bold", 38)
    c.drawString(text_x, code_y, str(request_code))

    # =========================
    # BLOCO INFERIOR
    # =========================
    qr_size = 78 * mm
    qr_x = inner_x + 28 * mm
    qr_y = inner_y + 22 * mm

    c.drawImage(
        qr_reader,
        qr_x,
        qr_y,
        width=qr_size,
        height=qr_size,
        mask="auto"
    )

    # Texto auxiliar ao lado do QR
    info_x = qr_x + qr_size + 15 * mm
    info_y_top = qr_y + qr_size - 30 * mm

    c.setFont("Helvetica", 18)
    c.drawString(info_x, info_y_top, "Escaneie para abrir")
    c.drawString(info_x, info_y_top - 12 * mm, "a tela de atualização")




    c.showPage()
    c.save()
    return resp

# Busca de item do Estoque por código E-Fisco (autocomplete nas solicitações)
@login_required
def estoque_search(request):
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse([], safe=False)
    resultados = (
        Estoque.objects
        .filter(
            Q(item_shock__efisco__icontains=q) |
            Q(item_shock__descricao_efisco__icontains=q) |
            Q(description_manual__icontains=q)
        )
        .select_related('item_shock')
        .values('id', 'item_shock__efisco', 'item_shock__descricao_efisco', 'amount_shock', 'mark')
        [:20]
    )
    return JsonResponse(list(resultados), safe=False)


@login_required
def edit_solicitacao(request, pk):
    solicitacao = get_object_or_404(Solicitacao, pk=pk)

    STATUS_EDITAVEIS = ["ATENDIMENTO", "AGUAR_SEPARACAO", "RASCUNHO"]
    if solicitacao.situation not in STATUS_EDITAVEIS:
        messages.error(request, 'Não é possível editar uma solicitação com status igual ou superior a "Separada".')
        return redirect("dimms:details_processing", pk=pk)

    if request.method == "POST":
        form = SolicitacaoEditForm(request.POST, instance=solicitacao)
        if form.is_valid():
            form.save()
            messages.success(request, "Dados da solicitação atualizados com sucesso.")
            return redirect("dimms:details_processing", pk=pk)
    else:
        form = SolicitacaoEditForm(instance=solicitacao)

    return render(request, "dimms/processing/edit_solicitacao.html", {
        "form": form,
        "solicitacao": solicitacao,
    })
