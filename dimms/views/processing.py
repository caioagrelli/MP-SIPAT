# bibliotecas padrões do Python
import os

# Importações padrões do Django Unchained   'What kind of dentist are you?' - Quentin Tarantino 
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.contrib.staticfiles import finders

#bibliotecas externas
import qrcode
from io import BytesIO
from qrcode.constants import ERROR_CORRECT_M
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm

from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

# Importações do Código
from ..models import Solicitacao, Tramitacao, Estoque
from ..forms import SolicitacaoForm, SolicitacaoItemFormSet, TramitacaoCreateForm, SolicitacaoStatusUpdateForm

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
        solicitacoes = solicitacoes.filter(
            Q(request_code__icontains=query)             |
            Q(user_order__icontains=query)               |
            Q(observation_order__icontains=query)        |
            Q(user_responsible__username__icontains=query)   |
            Q(user_responsible__first_name__icontains=query) |
            Q(user_responsible__last_name__icontains=query)
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

    etapas_fluxo = [
        {"codigo": "ATENDIMENTO", "label": "Em atendimento"},
        {"codigo": "AGUAR_SEPARACAO", "label": "Aguardando separação"},
        {"codigo": "SEPARADA", "label": "Separada"},
        {"codigo": "EXPEDICAO", "label": "Em expedição"},
        {"codigo": "RECEBIDA", "label": "Recebida"},
    ]

    ordem_status = {
        "ATENDIMENTO": 0,
        "AGUARD_SEPARACAO": 1,
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

            messages.success(request, 'Solicitação criada com sucesso.')
            return redirect('dimms:processing')
    else:
        form = SolicitacaoForm()
        formset = SolicitacaoItemFormSet()

    context = {
        'form': form,
        'formset': formset,
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

# Atualizar solicitações a partir delas (Não pode escolher / quando está na pagina individual)
@login_required
def update_request(request, pk):
    solicitacao = get_object_or_404(Solicitacao, pk=pk)

    if request.method == 'POST':
        form = SolicitacaoStatusUpdateForm(request.POST, request.FILES, instance=solicitacao)

        if form.is_valid():
            solicitacao_atualizada = form.save()

            observacao = form.cleaned_data.get('observacao_tramitacao')
            documento = form.cleaned_data.get('documents_update')
            foto = form.cleaned_data.get('photo_update')

            Tramitacao.objects.create(
                request_update=solicitacao_atualizada,
                update=solicitacao_atualizada.situation,
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
