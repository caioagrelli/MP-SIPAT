from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from dimms.models import (
    CatalogoConsumo, SolicitacaoCatalogoConsumo, ItemSolicitacaoCatalogoConsumo,
    BensConsumo,
)
from dimms.utils import GrupoConsumo, UnidadesMedida
from dempam.models import InfoUA


# ──────────────────────────────────────────────────────────────────────────────
# CATÁLOGO — LISTAGEM PÚBLICA (qualquer usuário autenticado)
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def catalogo_consumo_lista(request):
    q       = request.GET.get('q', '').strip()
    q_grupo = request.GET.get('grupo', '').strip()

    qs = CatalogoConsumo.objects.select_related('efisco').filter(ativo=True)

    if q:
        qs = qs.filter(
            Q(description__icontains=q) | Q(mark__icontains=q) |
            Q(efisco__descricao_efisco__icontains=q)
        )
    if q_grupo:
        qs = qs.filter(grupo_consumo=q_grupo)

    qs = qs.order_by('grupo_consumo', 'description')

    return render(request, 'dimms/catalogo/lista.html', {
        'itens':   qs,
        'grupos':  GrupoConsumo.choices,
        'query':   q,
        'q_grupo': q_grupo,
    })


# ──────────────────────────────────────────────────────────────────────────────
# CATÁLOGO — CRUD ADMIN
# ──────────────────────────────────────────────────────────────────────────────

@login_required
@permission_required('dimms.add_catalogoconsumo', raise_exception=True)
def catalogo_consumo_admin_lista(request):
    q       = request.GET.get('q', '').strip()
    q_grupo = request.GET.get('grupo', '').strip()
    q_ativo = request.GET.get('ativo', '1').strip()

    qs = CatalogoConsumo.objects.select_related('efisco').order_by('grupo_consumo', 'description')
    if q:
        qs = qs.filter(Q(description__icontains=q) | Q(mark__icontains=q))
    if q_grupo:
        qs = qs.filter(grupo_consumo=q_grupo)
    if q_ativo == '1':
        qs = qs.filter(ativo=True)
    elif q_ativo == '0':
        qs = qs.filter(ativo=False)

    return render(request, 'dimms/catalogo/admin_lista.html', {
        'itens':  qs,
        'grupos': GrupoConsumo.choices,
        'query':  q,
        'q_grupo': q_grupo,
        'q_ativo': q_ativo,
    })


@login_required
@permission_required('dimms.add_catalogoconsumo', raise_exception=True)
def catalogo_consumo_criar(request):
    grupos    = GrupoConsumo.choices
    medidas   = UnidadesMedida.choices
    efiscos   = BensConsumo.objects.all().order_by('descricao_efisco')
    erros     = {}

    if request.method == 'POST':
        description = request.POST.get('description', '').strip()
        mark        = request.POST.get('mark', '').strip()
        detalhes    = request.POST.get('detalhes', '').strip()
        medida      = request.POST.get('medida', 'UNIDADE')
        grupo       = request.POST.get('grupo_consumo', '')
        efisco_pk   = request.POST.get('efisco', '').strip() or None
        foto        = request.FILES.get('photo')
        ativo       = request.POST.get('ativo') == 'on'

        if not description:
            erros['description'] = 'Campo obrigatório.'
        if not grupo:
            erros['grupo_consumo'] = 'Campo obrigatório.'

        if not erros:
            item = CatalogoConsumo(
                description=description, mark=mark, detalhes=detalhes,
                medida=medida, grupo_consumo=grupo, ativo=ativo,
            )
            if efisco_pk:
                item.efisco = get_object_or_404(BensConsumo, pk=efisco_pk)
            if foto:
                item.photo = foto
            item.save()
            messages.success(request, f'"{item}" adicionado ao catálogo de consumo.')
            return redirect('dimms:catalogo_consumo_admin')

    val = {
        'description':  request.POST.get('description', ''),
        'mark':         request.POST.get('mark', ''),
        'detalhes':     request.POST.get('detalhes', ''),
        'medida':       request.POST.get('medida', 'UNIDADE'),
        'grupo_consumo': request.POST.get('grupo_consumo', ''),
        'efisco':       request.POST.get('efisco', ''),
        'ativo':        request.POST.get('ativo', 'on'),
    } if request.method == 'POST' else {
        'description': '', 'mark': '', 'detalhes': '',
        'medida': 'UNIDADE', 'grupo_consumo': '', 'efisco': '', 'ativo': 'on',
    }
    return render(request, 'dimms/catalogo/form.html', {
        'acao': 'Cadastrar', 'grupos': grupos, 'medidas': medidas,
        'efiscos': efiscos, 'erros': erros, 'item': None, 'val': val,
    })


@login_required
@permission_required('dimms.change_catalogoconsumo', raise_exception=True)
def catalogo_consumo_editar(request, pk):
    item      = get_object_or_404(CatalogoConsumo, pk=pk)
    grupos    = GrupoConsumo.choices
    medidas   = UnidadesMedida.choices
    efiscos   = BensConsumo.objects.all().order_by('descricao_efisco')
    erros     = {}

    if request.method == 'POST':
        description = request.POST.get('description', '').strip()
        mark        = request.POST.get('mark', '').strip()
        detalhes    = request.POST.get('detalhes', '').strip()
        medida      = request.POST.get('medida', 'UNIDADE')
        grupo       = request.POST.get('grupo_consumo', '')
        efisco_pk   = request.POST.get('efisco', '').strip() or None
        foto        = request.FILES.get('photo')
        ativo       = request.POST.get('ativo') == 'on'

        if not description:
            erros['description'] = 'Campo obrigatório.'
        if not grupo:
            erros['grupo_consumo'] = 'Campo obrigatório.'

        if not erros:
            item.description   = description
            item.mark          = mark
            item.detalhes      = detalhes
            item.medida        = medida
            item.grupo_consumo = grupo
            item.ativo         = ativo
            item.efisco        = get_object_or_404(BensConsumo, pk=efisco_pk) if efisco_pk else None
            if foto:
                item.photo = foto
            item.save()
            messages.success(request, f'"{item}" atualizado.')
            return redirect('dimms:catalogo_consumo_admin')

    if request.method == 'POST':
        val = {
            'description':   request.POST.get('description', ''),
            'mark':          request.POST.get('mark', ''),
            'detalhes':      request.POST.get('detalhes', ''),
            'medida':        request.POST.get('medida', 'UNIDADE'),
            'grupo_consumo': request.POST.get('grupo_consumo', ''),
            'efisco':        request.POST.get('efisco', ''),
            'ativo':         request.POST.get('ativo', ''),
        }
    else:
        val = {
            'description':   item.description,
            'mark':          item.mark,
            'detalhes':      item.detalhes,
            'medida':        item.medida,
            'grupo_consumo': item.grupo_consumo,
            'efisco':        str(item.efisco_id) if item.efisco_id else '',
            'ativo':         'on' if item.ativo else '',
        }
    return render(request, 'dimms/catalogo/form.html', {
        'acao': 'Editar', 'grupos': grupos, 'medidas': medidas,
        'efiscos': efiscos, 'erros': erros, 'item': item, 'val': val,
    })


@login_required
@permission_required('dimms.delete_catalogoconsumo', raise_exception=True)
def catalogo_consumo_excluir(request, pk):
    item = get_object_or_404(CatalogoConsumo, pk=pk)
    if request.method == 'POST':
        nome = str(item)
        item.delete()
        messages.success(request, f'"{nome}" removido do catálogo.')
        return redirect('dimms:catalogo_consumo_admin')
    return render(request, 'dimms/catalogo/excluir.html', {'item': item})


# ──────────────────────────────────────────────────────────────────────────────
# SOLICITAÇÕES — USUÁRIO (suas próprias solicitações)
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def minhas_solicitacoes_consumo(request):
    profile = request.user.profile
    uas = (profile.uas.all() | profile.managed_uas.all()).distinct()
    solicitacoes = (
        SolicitacaoCatalogoConsumo.objects
        .filter(ua_destino__in=uas)
        .prefetch_related('itens__catalogo')
        .select_related('solicitante', 'ua_destino')
        .order_by('-data')
    )
    return render(request, 'dimms/catalogo/minhas_solicitacoes.html', {
        'solicitacoes': solicitacoes,
    })


# ──────────────────────────────────────────────────────────────────────────────
# SOLICITAÇÕES — PAINEL ADMIN (aprovar / rejeitar)
# ──────────────────────────────────────────────────────────────────────────────

@login_required
@permission_required('dimms.change_catalogoconsumo', raise_exception=True)
def painel_solicitacoes_consumo(request):
    filtro = request.GET.get('status', 'PENDENTE').strip()
    q      = request.GET.get('q', '').strip()

    qs = SolicitacaoCatalogoConsumo.objects.select_related(
        'solicitante', 'ua_destino', 'decidido_por'
    ).prefetch_related('itens')

    if filtro:
        qs = qs.filter(status=filtro)
    if q:
        qs = qs.filter(
            Q(codigo__icontains=q) | Q(solicitante__username__icontains=q) |
            Q(solicitante__first_name__icontains=q) | Q(solicitante__last_name__icontains=q)
        )
    qs = qs.order_by('-data')

    base = SolicitacaoCatalogoConsumo.objects
    return render(request, 'dimms/catalogo/painel.html', {
        'solicitacoes':    qs,
        'filtro':          filtro,
        'query':           q,
        'total_pendente':  base.filter(status='PENDENTE').count(),
        'total_atendida':  base.filter(status='ATENDIDA').count(),
        'total_rejeitada': base.filter(status='REJEITADA').count(),
    })


@login_required
@permission_required('dimms.change_catalogoconsumo', raise_exception=True)
def analisar_solicitacao_consumo(request, pk):
    sol = get_object_or_404(
        SolicitacaoCatalogoConsumo.objects
        .prefetch_related('itens__catalogo')
        .select_related('solicitante', 'ua_destino'),
        pk=pk,
    )

    if request.method == 'POST':
        acao = request.POST.get('acao')

        if acao == 'atender' and sol.status == 'PENDENTE':
            sol.status       = 'ATENDIDA'
            sol.obs_decisao  = request.POST.get('obs_decisao', '')
            sol.decidido_por = request.user
            sol.data_decisao = timezone.now()
            sol.save()
            messages.success(request, f'Solicitação {sol.codigo} marcada como atendida.')
            return redirect('dimms:painel_solicitacoes_consumo')

        if acao == 'rejeitar' and sol.status == 'PENDENTE':
            sol.status       = 'REJEITADA'
            sol.obs_decisao  = request.POST.get('obs_decisao', '')
            sol.decidido_por = request.user
            sol.data_decisao = timezone.now()
            sol.save()
            messages.info(request, f'Solicitação {sol.codigo} rejeitada.')
            return redirect('dimms:painel_solicitacoes_consumo')

    return render(request, 'dimms/catalogo/analisar.html', {'sol': sol})
