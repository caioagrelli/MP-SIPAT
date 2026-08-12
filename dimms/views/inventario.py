# Importações do Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

# Importações do código
from ..models import ConferenciaEstoque, Estoque, PeriodoInventarioConsumo
from ..utils import DecisaoAjusteEstoque
from dempam.models import LocalizacaoDEMPAM

# ====================================
# INVENTÁRIO MENSAL DE ESTOQUE (DIMMS)
# ====================================


''' Painel do inventário do mês: progresso, busca e fila de itens pendentes/conferidos '''
@login_required
def inventario_homepage(request):
    periodo_id = request.GET.get('periodo')
    if periodo_id:
        periodo = get_object_or_404(PeriodoInventarioConsumo, pk=periodo_id)
    else:
        periodo = PeriodoInventarioConsumo.periodo_atual()

    periodos = PeriodoInventarioConsumo.objects.order_by('-ano', '-mes')

    query = request.GET.get('q', '').strip()
    aba = request.GET.get('aba', 'pendentes').strip()
    if aba not in ('pendentes', 'conferidos'):
        aba = 'pendentes'

    conferidos_ids = periodo.conferencias.values_list('item_id', flat=True)

    itens = (
        Estoque.objects
        .select_related('item_shock', 'locate__setor_sala')
        .order_by('item_shock__descricao_efisco')
    )
    if aba == 'pendentes':
        itens = itens.exclude(pk__in=conferidos_ids)
    else:
        itens = itens.filter(pk__in=conferidos_ids)

    if query:
        itens = itens.filter(
            Q(item_shock__efisco__icontains=query) |
            Q(item_shock__descricao_efisco__icontains=query) |
            Q(description_manual__icontains=query)
        )

    paginator = Paginator(itens, 30)
    pagina = paginator.get_page(request.GET.get('pagina'))

    total_divergencias_pendentes = sum(
        1 for c in periodo.conferencias.all()
        if c.houve_divergencia and c.decisao_ajuste == DecisaoAjusteEstoque.pendente
    )

    return render(request, 'dimms/inventario/homepage.html', {
        'periodo': periodo,
        'periodos': periodos,
        'query': query,
        'aba': aba,
        'pagina': pagina,
        'periodo_atual': periodo.pk == PeriodoInventarioConsumo.periodo_atual().pk,
        'total_divergencias_pendentes': total_divergencias_pendentes,
    })


''' Tela de conferência de um item: confirma/ajusta quantidade e localização '''
@login_required
def inventario_item_conferir(request, pk):
    periodo = PeriodoInventarioConsumo.periodo_atual()
    item = get_object_or_404(
        Estoque.objects.select_related('item_shock', 'locate__setor_sala'),
        pk=pk,
    )
    conferencia_existente = periodo.conferencias.filter(item=item).first()

    if request.method == 'POST':
        quantidade_raw = request.POST.get('quantidade', '').strip().replace(',', '.')
        localizacao_id = request.POST.get('localizacao_id') or None

        try:
            quantidade = float(quantidade_raw)
            if quantidade < 0:
                raise ValueError
        except ValueError:
            messages.error(request, 'Informe uma quantidade válida.')
            return redirect('dimms:inventario_item_conferir', pk=item.pk)

        localizacao = LocalizacaoDEMPAM.objects.filter(pk=localizacao_id).first() if localizacao_id else None

        houve_divergencia = (
            item.amount_shock != quantidade or item.locate_id != (localizacao.pk if localizacao else None)
        )

        ConferenciaEstoque.objects.update_or_create(
            periodo=periodo,
            item=item,
            defaults={
                'quantidade_anterior': item.amount_shock,
                'quantidade_conferida': quantidade,
                'localizacao_anterior': item.locate,
                'localizacao_conferida': localizacao,
                'observacao': request.POST.get('observacao', '').strip(),
                'conferido_por': request.user,
                # a conferência NÃO altera o estoque real — se houver divergência,
                # fica pendente na tela de Divergências até ser investigada e aprovada
                'decisao_ajuste': DecisaoAjusteEstoque.pendente,
                'decidido_por': None,
                'decidido_em': None,
            },
        )

        if houve_divergencia:
            messages.warning(
                request,
                f'{item.description_manual or item.item_shock.efisco} conferido com divergência — '
                f'enviado para a área de Divergências para aprovação.'
            )
        else:
            messages.success(request, f'{item.description_manual or item.item_shock.efisco} conferido sem divergências.')

        proximo_id = request.POST.get('proximo_id')
        query = request.POST.get('q', '')
        if proximo_id:
            url = f"/dimms/inventario/item/{proximo_id}/"
            if query:
                url += f"?q={query}"
            return redirect(url)
        return redirect('dimms:inventario_homepage')

    proximo = (
        Estoque.objects
        .exclude(pk=item.pk)
        .exclude(pk__in=periodo.conferencias.values_list('item_id', flat=True))
        .order_by('item_shock__descricao_efisco')
        .first()
    )

    return render(request, 'dimms/inventario/conferir.html', {
        'periodo': periodo,
        'item': item,
        'conferencia_existente': conferencia_existente,
        'proximo': proximo,
        'query': request.GET.get('q', ''),
    })


''' Área de Divergências: itens conferidos cuja quantidade/localização não bate com o estoque atual,
    aguardando investigação e aprovação antes de qualquer alteração real no estoque '''
@login_required
def inventario_divergencias(request):
    periodo_id = request.GET.get('periodo')
    if periodo_id:
        periodo = get_object_or_404(PeriodoInventarioConsumo, pk=periodo_id)
    else:
        periodo = PeriodoInventarioConsumo.periodo_atual()

    periodos = PeriodoInventarioConsumo.objects.order_by('-ano', '-mes')

    aba = request.GET.get('aba', 'pendentes').strip()
    if aba not in ('pendentes', 'decididas'):
        aba = 'pendentes'

    conferencias = (
        periodo.conferencias
        .select_related(
            'item__item_shock', 'item__locate__setor_sala',
            'localizacao_anterior__setor_sala', 'localizacao_conferida__setor_sala',
            'conferido_por', 'decidido_por',
        )
        .order_by('-conferido_em')
    )

    divergentes = [c for c in conferencias if c.houve_divergencia]
    pendentes = [c for c in divergentes if c.decisao_ajuste == DecisaoAjusteEstoque.pendente]
    decididas = [c for c in divergentes if c.decisao_ajuste != DecisaoAjusteEstoque.pendente]

    lista = pendentes if aba == 'pendentes' else decididas

    return render(request, 'dimms/inventario/divergencias.html', {
        'periodo': periodo,
        'periodos': periodos,
        'aba': aba,
        'lista': lista,
        'total_pendentes': len(pendentes),
        'total_decididas': len(decididas),
    })


''' Aprova (aplica no estoque) ou rejeita (mantém o estoque como está) uma divergência '''
@login_required
def inventario_divergencia_decidir(request, pk):
    if request.method != 'POST':
        return redirect('dimms:inventario_divergencias')

    conferencia = get_object_or_404(
        ConferenciaEstoque.objects.select_related('item__item_shock'),
        pk=pk,
    )

    decisao = request.POST.get('decisao')
    if decisao not in (DecisaoAjusteEstoque.aprovado, DecisaoAjusteEstoque.rejeitado):
        messages.error(request, 'Decisão inválida.')
        return redirect('dimms:inventario_divergencias')

    item = conferencia.item
    nome_item = item.description_manual or item.item_shock.efisco

    if decisao == DecisaoAjusteEstoque.aprovado:
        item.amount_shock = conferencia.quantidade_conferida
        item.locate = conferencia.localizacao_conferida
        item.save(update_fields=['amount_shock', 'locate'])
        messages.success(request, f'Ajuste aprovado — estoque de "{nome_item}" atualizado.')
    else:
        messages.success(request, f'Divergência de "{nome_item}" rejeitada — estoque mantido como está.')

    conferencia.decisao_ajuste = decisao
    conferencia.decidido_por = request.user
    conferencia.decidido_em = timezone.now()
    conferencia.save(update_fields=['decisao_ajuste', 'decidido_por', 'decidido_em'])

    aba = request.POST.get('aba', 'pendentes')
    periodo_id = request.POST.get('periodo_id', '')
    url = f"{reverse('dimms:inventario_divergencias')}?aba={aba}"
    if periodo_id:
        url += f"&periodo={periodo_id}"
    return redirect(url)
