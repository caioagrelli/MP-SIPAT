from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from dimrcbp.models import (
    Catalogo, Description, Type, Groups,
    SolicitacaoCatalogo, ItemSolicitacaoCatalogo,
    BensPermanentes, MovimentacaoBem,
)
from dempam.models import InfoUA
from dimms.models import CatalogoConsumo, SolicitacaoCatalogoConsumo, ItemSolicitacaoCatalogoConsumo

CART_KEY = 'catalogo_cart'
TIPOS_VALIDOS = ('perm', 'cons')


def _get_cart(request):
    return request.session.get(CART_KEY, {})


def _save_cart(request, cart):
    request.session[CART_KEY] = cart
    request.session.modified = True


# ──────────────────────────────────────────────────────────────────────────────
# CATÁLOGO — MARKETPLACE (permanentes + consumo juntos)
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def catalogo_lista(request):
    q_descricao  = request.GET.get('descricao', '').strip()
    q_grupo      = request.GET.get('grupo', '').strip()
    q_tipo_perm  = request.GET.get('tipo', '').strip()
    q_categoria  = request.GET.get('categoria', '').strip()  # 'perm' | 'cons' | ''

    cart       = _get_cart(request)
    cart_count = sum(cart.values())

    # ── Bens Permanentes ──
    qs_perm = Catalogo.objects.select_related(
        'description', 'description__type', 'description__type__gruop'
    )
    if q_descricao:
        qs_perm = qs_perm.filter(description__description__icontains=q_descricao)
    if q_grupo:
        qs_perm = qs_perm.filter(description__type__gruop__pk=q_grupo)
    if q_tipo_perm:
        qs_perm = qs_perm.filter(description__type__pk=q_tipo_perm)

    itens_perm = []
    if q_categoria in ('perm', ''):
        for item in qs_perm:
            key = f'perm:{item.pk}'
            item.tipo        = 'perm'
            item.tipo_label  = 'Permanente'
            item.no_carrinho = key in cart
            item.qt_carrinho = cart.get(key, 0)
            item.nome        = str(item.description)
            item.foto        = item.photo if item.photo else None
            item.grupo_label = f'{item.description.type.gruop} › {item.description.type}' if item.description and item.description.type else ''
            item.estoque_info = None
            itens_perm.append(item)

    # ── Bens de Consumo (catálogo separado do estoque) ──
    qs_cons = CatalogoConsumo.objects.select_related('efisco').filter(ativo=True)
    if q_descricao:
        qs_cons = qs_cons.filter(
            Q(description__icontains=q_descricao) |
            Q(mark__icontains=q_descricao) |
            Q(efisco__descricao_efisco__icontains=q_descricao)
        )
    if q_grupo:
        qs_cons = qs_cons.filter(grupo_consumo=q_grupo)

    itens_cons = []
    if q_categoria in ('cons', ''):
        for item in qs_cons:
            key = f'cons:{item.pk}'
            item.tipo        = 'cons'
            item.tipo_label  = 'Consumo'
            item.no_carrinho = key in cart
            item.qt_carrinho = cart.get(key, 0)
            item.nome        = item.description
            item.foto        = item.photo if item.photo else None
            item.grupo_label = item.get_grupo_consumo_display()
            item.estoque_info = None
            itens_cons.append(item)

    itens = itens_perm + itens_cons

    grupos = Groups.objects.all().order_by('group')
    tipos  = Type.objects.all().order_by('type')

    return render(request, 'dimrcbp/catalogo/marketplace.html', {
        'itens':      itens,
        'grupos':     grupos,
        'tipos':      tipos,
        'cart':       cart,
        'cart_count': cart_count,
        'filtros': {
            'descricao':  q_descricao,
            'grupo':      q_grupo,
            'tipo':       q_tipo_perm,
            'categoria':  q_categoria,
        },
    })


# ──────────────────────────────────────────────────────────────────────────────
# CARRINHO — ADD / REMOVE / CLEAR
# tipo: 'perm' (bem permanente / Catalogo) | 'cons' (bem de consumo / Estoque)
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def catalogo_cart_add(request, tipo, pk):
    if tipo not in TIPOS_VALIDOS:
        return HttpResponseBadRequest()
    if tipo == 'perm':
        get_object_or_404(Catalogo, pk=pk)
    else:
        get_object_or_404(CatalogoConsumo, pk=pk)

    qty  = max(1, int(request.POST.get('qty', 1)))
    cart = _get_cart(request)
    key  = f'{tipo}:{pk}'
    cart[key] = qty  # define (não acumula) — o input já diz quanto o usuário quer
    _save_cart(request, cart)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'count': sum(cart.values()), 'item_qty': cart[key]})
    return redirect(request.META.get('HTTP_REFERER', 'dimrcbp:catalogo_lista'))


@login_required
def catalogo_cart_remove(request, tipo, pk):
    if tipo not in TIPOS_VALIDOS:
        return HttpResponseBadRequest()
    cart = _get_cart(request)
    cart.pop(f'{tipo}:{pk}', None)
    _save_cart(request, cart)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'count': sum(cart.values())})
    return redirect(request.META.get('HTTP_REFERER', 'dimrcbp:catalogo_lista'))


@login_required
def catalogo_cart_update(request, tipo, pk):
    if tipo not in TIPOS_VALIDOS:
        return HttpResponseBadRequest()
    qty  = max(0, int(request.POST.get('qty', 1)))
    cart = _get_cart(request)
    key  = f'{tipo}:{pk}'
    if qty == 0:
        cart.pop(key, None)
    else:
        cart[key] = qty
    _save_cart(request, cart)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'count': sum(cart.values()), 'item_qty': qty})
    return redirect('dimrcbp:catalogo_checkout')


@login_required
def catalogo_cart_clear(request):
    _save_cart(request, {})
    return redirect('dimrcbp:catalogo_lista')


# ──────────────────────────────────────────────────────────────────────────────
# CHECKOUT — cria SolicitacaoCatalogo (permanentes) e Solicitacao (consumo)
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def catalogo_checkout(request):
    cart = _get_cart(request)
    if not cart:
        messages.warning(request, 'Seu carrinho está vazio.')
        return redirect('dimrcbp:catalogo_lista')

    perm_keys = {k: v for k, v in cart.items() if k.startswith('perm:')}
    cons_keys = {k: v for k, v in cart.items() if k.startswith('cons:')}

    # Resolver objetos permanentes
    perm_pks = [int(k.split(':', 1)[1]) for k in perm_keys]
    perm_map  = {str(i.pk): i for i in Catalogo.objects.filter(pk__in=perm_pks).select_related(
        'description', 'description__type', 'description__type__gruop'
    )} if perm_pks else {}

    # Resolver objetos consumo
    cons_pks  = [int(k.split(':', 1)[1]) for k in cons_keys]
    cons_map  = {str(i.pk): i for i in CatalogoConsumo.objects.filter(pk__in=cons_pks).select_related('efisco')} if cons_pks else {}

    cart_perm = [
        {'item': perm_map[k.split(':', 1)[1]], 'qty': v, 'tipo': 'perm'}
        for k, v in perm_keys.items() if k.split(':', 1)[1] in perm_map
    ]
    cart_cons = [
        {'item': cons_map[k.split(':', 1)[1]], 'qty': v, 'tipo': 'cons'}
        for k, v in cons_keys.items() if k.split(':', 1)[1] in cons_map
    ]
    cart_itens = cart_perm + cart_cons

    uas = InfoUA.objects.select_related('circunscricao_predio').order_by('ua')

    if request.method == 'POST':
        ua_id      = request.POST.get('ua_destino')
        observacao = request.POST.get('observacao', '').strip()

        if not ua_id:
            messages.error(request, 'Selecione a UA destino.')
        else:
            ua = get_object_or_404(InfoUA, pk=ua_id)
            codigos = []
            erros   = []

            with transaction.atomic():
                # ── Bens Permanentes ──
                if cart_perm:
                    sol_perm = SolicitacaoCatalogo.objects.create(
                        solicitante=request.user,
                        ua_destino=ua,
                        observacao=observacao,
                    )
                    for ci in cart_perm:
                        for _ in range(ci['qty']):
                            ItemSolicitacaoCatalogo.objects.create(
                                solicitacao=sol_perm,
                                catalogo=ci['item'],
                            )
                    codigos.append(sol_perm.codigo)

                # ── Bens de Consumo ──
                if cart_cons:
                    sol_cons = SolicitacaoCatalogoConsumo.objects.create(
                        solicitante=request.user,
                        ua_destino=ua,
                        observacao=observacao,
                    )
                    for ci in cart_cons:
                        ItemSolicitacaoCatalogoConsumo.objects.create(
                            solicitacao=sol_cons,
                            catalogo=ci['item'],
                            quantidade=ci['qty'],
                        )
                    codigos.append(sol_cons.codigo)

            if erros:
                messages.warning(request, 'Erro ao criar solicitação: ' + '; '.join(erros))
            if codigos:
                _save_cart(request, {})
                msgs = ', '.join(codigos)
                messages.success(request, f'Solicitação(ões) criada(s) com sucesso: {msgs}')
                return redirect('dimrcbp:minhas_solicitacoes')

    return render(request, 'dimrcbp/catalogo/checkout.html', {
        'cart_itens': cart_itens,
        'uas':        uas,
    })


# ──────────────────────────────────────────────────────────────────────────────
# MINHAS SOLICITAÇÕES — página unificada (permanentes + consumo)
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def minhas_solicitacoes(request):
    """Página única do usuário mostrando permanentes + consumo lado a lado."""
    sols_perm = (
        SolicitacaoCatalogo.objects
        .filter(solicitante=request.user)
        .prefetch_related('itens__catalogo')
        .order_by('-data')
    )
    sols_cons = (
        SolicitacaoCatalogoConsumo.objects
        .filter(solicitante=request.user)
        .prefetch_related('itens__catalogo')
        .order_by('-data')
    )
    return render(request, 'dimrcbp/catalogo/minhas_solicitacoes.html', {
        'sols_perm': sols_perm,
        'sols_cons': sols_cons,
    })


@login_required
def minhas_solicitacoes_catalogo(request):
    """Alias para manter compatibilidade com redirecionamentos antigos."""
    return redirect('dimrcbp:minhas_solicitacoes')


# ──────────────────────────────────────────────────────────────────────────────
# PAINEL DE APROVAÇÃO (aprovadores)
# ──────────────────────────────────────────────────────────────────────────────

@login_required
@permission_required('dimrcbp.change_benspermanentes', raise_exception=True)
def painel_solicitacoes_catalogo(request):
    filtro = request.GET.get('status', 'PENDENTE').strip()
    q      = request.GET.get('q', '').strip()

    qs = SolicitacaoCatalogo.objects.select_related(
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

    base = SolicitacaoCatalogo.objects
    return render(request, 'dimrcbp/catalogo/painel.html', {
        'solicitacoes':    qs,
        'filtro':          filtro,
        'query':           q,
        'total_pendente':  base.filter(status='PENDENTE').count(),
        'total_aprovada':  base.filter(status='APROVADA').count(),
        'total_rejeitada': base.filter(status='REJEITADA').count(),
    })


@login_required
@permission_required('dimrcbp.change_benspermanentes', raise_exception=True)
def aprovar_solicitacao_catalogo(request, pk):
    sol = get_object_or_404(
        SolicitacaoCatalogo.objects.prefetch_related(
            'itens__catalogo__description',
            'itens__bem_atribuido',
        ).select_related('solicitante', 'ua_destino'),
        pk=pk,
    )

    if request.method == 'POST':
        acao = request.POST.get('acao')

        if acao == 'rejeitar':
            sol.status       = 'REJEITADA'
            sol.obs_decisao  = request.POST.get('obs_decisao', '')
            sol.decidido_por = request.user
            sol.data_decisao = timezone.now()
            sol.save()
            messages.info(request, 'Solicitação rejeitada.')
            return redirect('dimrcbp:painel_solicitacoes_catalogo')

        if acao == 'atribuir':
            item_id = request.POST.get('item_id')
            bem_id  = request.POST.get('bem_id')
            if item_id and bem_id:
                item = get_object_or_404(ItemSolicitacaoCatalogo, pk=item_id, solicitacao=sol)
                bem  = get_object_or_404(BensPermanentes, pk=bem_id)

                ua_origem = None
                try:
                    ua_origem = bem.history_tombo.current_ua
                except Exception:
                    pass

                with transaction.atomic():
                    item.bem_atribuido = bem
                    item.save()
                    MovimentacaoBem.objects.create(
                        bem=bem,
                        ua_origem=ua_origem,
                        ua_destino=sol.ua_destino,
                        responsavel=request.user,
                        motivo=f'Via solicitação catálogo {sol.codigo}',
                    )

                # Se todos os itens foram atribuídos, marca como aprovada
                if not sol.itens.filter(bem_atribuido__isnull=True).exists():
                    sol.status       = 'APROVADA'
                    sol.decidido_por = request.user
                    sol.data_decisao = timezone.now()
                    sol.obs_decisao  = request.POST.get('obs_decisao', '')
                    sol.save()
                    messages.success(request, f'Solicitação {sol.codigo} totalmente atendida!')
                else:
                    messages.success(request, f'Bem {bem.tombo} atribuído com sucesso.')

            return redirect('dimrcbp:aprovar_solicitacao_catalogo', pk=pk)

    # Busca bens disponíveis por descrição para cada item não atendido
    itens_com_opcoes = []
    for item in sol.itens.all():
        if item.bem_atribuido:
            itens_com_opcoes.append({'item': item, 'disponiveis': []})
        else:
            disponiveis = BensPermanentes.objects.filter(
                description=item.catalogo.description
            ).select_related('history_tombo__current_ua').order_by('tombo')
            itens_com_opcoes.append({'item': item, 'disponiveis': disponiveis})

    return render(request, 'dimrcbp/catalogo/aprovar.html', {
        'sol':              sol,
        'itens_com_opcoes': itens_com_opcoes,
    })


# ──────────────────────────────────────────────────────────────────────────────
# VIEWS EXISTENTES (catálogo admin)
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def catalogo_detalhe(request, pk):
    item = get_object_or_404(
        Catalogo.objects.select_related(
            'description', 'description__type', 'description__type__gruop'
        ),
        pk=pk,
    )
    cart = _get_cart(request)
    return render(request, 'dimrcbp/catalogo_detalhe.html', {
        'item':       item,
        'no_carrinho': str(pk) in cart,
    })


@login_required
@permission_required('dimrcbp.add_catalogo', raise_exception=True)
def catalogo_criar(request):
    grupos     = Groups.objects.all().order_by('group')
    tipos      = Type.objects.all().order_by('type')
    descricoes = Description.objects.select_related('type').order_by('description')
    erros = {}

    if request.method == 'POST':
        efisco    = request.POST.get('efisco', '').strip()
        desc_pk   = request.POST.get('description', '').strip()
        descricao = request.POST.get('descricao', '').strip()
        value     = request.POST.get('value', '').strip() or None
        foto      = request.FILES.get('photo')

        if not efisco:
            erros['efisco'] = 'Campo obrigatório.'
        elif Catalogo.objects.filter(efisco=efisco).exists():
            erros['efisco'] = 'Já existe um item com este código Efisco.'
        if not desc_pk:
            erros['description'] = 'Campo obrigatório.'

        if not erros:
            item = Catalogo(
                efisco=efisco,
                description=get_object_or_404(Description, pk=desc_pk),
                descricao=descricao,
                value=value,
            )
            if foto:
                item.photo = foto
            item.save()
            messages.success(request, f'Item "{item}" adicionado ao catálogo.')
            return redirect('dimrcbp:catalogo_detalhe', pk=item.pk)

    return render(request, 'dimrcbp/catalogo_form.html', {
        'acao': 'Cadastrar', 'grupos': grupos, 'tipos': tipos,
        'descricoes': descricoes, 'erros': erros,
        'val': {
            'efisco': request.POST.get('efisco', ''),
            'description': request.POST.get('description', ''),
            'descricao': request.POST.get('descricao', ''),
            'value': request.POST.get('value', ''),
        },
    })


@login_required
@permission_required('dimrcbp.change_catalogo', raise_exception=True)
def catalogo_editar(request, pk):
    item      = get_object_or_404(Catalogo, pk=pk)
    grupos    = Groups.objects.all().order_by('group')
    tipos     = Type.objects.all().order_by('type')
    descricoes = Description.objects.select_related('type').order_by('description')
    erros = {}

    if request.method == 'POST':
        efisco    = request.POST.get('efisco', '').strip()
        desc_pk   = request.POST.get('description', '').strip()
        descricao = request.POST.get('descricao', '').strip()
        value     = request.POST.get('value', '').strip() or None
        foto      = request.FILES.get('photo')

        if not efisco:
            erros['efisco'] = 'Campo obrigatório.'
        elif Catalogo.objects.filter(efisco=efisco).exclude(pk=pk).exists():
            erros['efisco'] = 'Já existe outro item com este código Efisco.'
        if not desc_pk:
            erros['description'] = 'Campo obrigatório.'

        if not erros:
            item.efisco = efisco
            item.description = get_object_or_404(Description, pk=desc_pk)
            item.descricao = descricao
            item.value = value
            if foto:
                item.photo = foto
            item.save()
            messages.success(request, 'Catálogo atualizado com sucesso.')
            return redirect('dimrcbp:catalogo_detalhe', pk=item.pk)

    src = request.POST if request.method == 'POST' else None
    return render(request, 'dimrcbp/catalogo_form.html', {
        'acao': 'Editar', 'item': item, 'grupos': grupos, 'tipos': tipos,
        'descricoes': descricoes, 'erros': erros,
        'val': {
            'efisco':      src.get('efisco', item.efisco) if src else item.efisco,
            'description': src.get('description', str(item.description_id)) if src else str(item.description_id),
            'descricao':   src.get('descricao', item.descricao) if src else item.descricao,
            'value':       src.get('value', str(item.value or '')) if src else str(item.value or ''),
        },
    })


@login_required
@permission_required('dimrcbp.delete_catalogo', raise_exception=True)
def catalogo_excluir(request, pk):
    item = get_object_or_404(Catalogo, pk=pk)
    if request.method == 'POST':
        nome = str(item)
        item.delete()
        messages.success(request, f'Item "{nome}" excluído do catálogo.')
        return redirect('dimrcbp:catalogo_lista')
    return render(request, 'dimrcbp/catalogo_excluir.html', {'item': item})
