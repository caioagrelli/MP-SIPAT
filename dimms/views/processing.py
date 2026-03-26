# Importações padrões do Django Unchained   'What kind of dentist are you?' - Quentin Tarantino 
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.decorators import login_required

# Importações do Código
from ..models import Solicitacao, Tramitacao
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

