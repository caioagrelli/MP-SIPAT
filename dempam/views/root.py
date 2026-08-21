# bibliotecas do django
import re
from functools import wraps
from decimal import Decimal
from collections import defaultdict

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from django.db.models import Min, Max, Count, Sum, F
from django.http import JsonResponse
from django.core.paginator import Paginator

# importações do código
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from ..models import InfoUA, Aviso, Municipio
from ..forms import AvisoForm
from ..services import montar_dashboard_usuario
from dimms.models import Estoque, Solicitacao, SolicitacaoItens
from dimrcbp.models import BensPermanentes

# ====================================================
# VIEWS CENTRAIS DO SIPAT (DIRECIONAMENTO DE PÁGINAS)
# ====================================================


def gerencia_dempam_required(view_func):
    """Permite superusuários, staff, ou membros da Gerência DEMPAM — mais restrito
    que management_required (que também libera gestão de usuários/grupos)."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        user = request.user
        if (
            user.is_superuser
            or user.is_staff
            or user.groups.filter(name='Gerência DEMPAM').exists()
        ):
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return wrapper



''' FUNÇÕES PRINCIPAIS DO SIPAT'''
# destinar paginas
def root(request):
    if request.user.is_authenticated:
        return redirect('home')  # Página quando o usuário estiver logado
    next_url = request.GET.get('next', '')
    login_url = f"{settings.LOGIN_URL}?next={next_url}" if next_url else settings.LOGIN_URL
    return redirect(login_url)

#homepage central (futuramente vai ser um app a parte)
@login_required
def home(request):
    context = montar_dashboard_usuario(request.user)
    return render(request, 'global/home.html', context)
  
  
''' Homepage'''
# pagina principal do dempam
@login_required
def homepage(request):
    municipios_com_circunscricao = Municipio.objects.exclude(circunscricao='').order_by('nome')
    circunscricao_por_municipio = {
        m.codigo_ibge: m.circunscricao for m in municipios_com_circunscricao
    }

    def _ordem_circunscricao(label):
        m = re.match(r'^(\d+)ª', label)
        return (0, int(m.group(1))) if m else (1, label)

    circunscricoes = sorted(set(circunscricao_por_municipio.values()), key=_ordem_circunscricao)

    return render(request, 'dempam/homepage.html', {
        'total_setores': InfoUA.objects.count(),
        'total_bens_permanentes': BensPermanentes.objects.count(),
        'total_consumo': Estoque.objects.count(),
        'total_pendencias': Solicitacao.objects.filter(situation='ATENDIMENTO').count(),
        'circunscricao_por_municipio': circunscricao_por_municipio,
        'circunscricoes': circunscricoes,
    })


''' Mapa do Painel Gerencial '''
# Monta o resumo (UAs + bens + pedidos + gasto médio mensal) pra um conjunto de UAs —
# usado tanto pro clique num município quanto pra seleção de uma circunscrição inteira
def _montar_resumo_uas(nome, uas):
    total_bens = BensPermanentes.objects.filter(history_tombo__current_ua__in=uas).count()

    solicitacoes = Solicitacao.objects.filter(ua_order__in=uas)
    total_pedidos = solicitacoes.count()

    itens = (
        SolicitacaoItens.objects
        .filter(
            request_defendant__ua_order__in=uas,
            item_order__isnull=False,
            amount_order__isnull=False,
        )
        .select_related('item_order__item_shock')
    )
    total_gasto = Decimal('0')
    for item in itens:
        preco = item.item_order.item_shock.preco_medio
        if preco:
            total_gasto += item.amount_order * preco

    periodo = solicitacoes.aggregate(primeira=Min('data_order'), ultima=Max('data_order'))
    if periodo['primeira'] and periodo['ultima']:
        meses = (
            (periodo['ultima'].year - periodo['primeira'].year) * 12
            + (periodo['ultima'].month - periodo['primeira'].month)
            + 1
        )
    else:
        meses = 1
    gasto_mensal = total_gasto / meses

    return {
        'nome': nome,
        'uas': list(uas.order_by('ua').values_list('ua', 'sigla')),
        'total_bens': total_bens,
        'total_pedidos': total_pedidos,
        'gasto_mensal': float(gasto_mensal),
    }


# Resumo das UAs de um único município, pro clique no mapa
@login_required
def municipio_resumo(request, codigo_ibge):
    municipio = get_object_or_404(Municipio, codigo_ibge=codigo_ibge)
    uas = InfoUA.objects.filter(municipio=municipio)
    return JsonResponse(_montar_resumo_uas(municipio.nome, uas))


# Resumo agregado de todas as UAs dos municípios de uma circunscrição, pro filtro do mapa
@login_required
def circunscricao_resumo(request, circunscricao):
    uas = InfoUA.objects.filter(municipio__circunscricao=circunscricao)
    return JsonResponse(_montar_resumo_uas(circunscricao, uas))


# Ranking de gasto mensal (consumo) por município e por circunscrição
def _linha_ranking_vazia():
    return {'total_bens': 0, 'total_pedidos': 0, 'total_gasto': Decimal('0'), 'primeira': None, 'ultima': None}


def _finalizar_ranking(dados_por_chave, nomes):
    linhas = []
    for chave, dados in dados_por_chave.items():
        if dados['primeira'] and dados['ultima']:
            meses = (
                (dados['ultima'].year - dados['primeira'].year) * 12
                + (dados['ultima'].month - dados['primeira'].month)
                + 1
            )
        else:
            meses = 1
        linhas.append({
            'nome': nomes[chave],
            'total_bens': dados['total_bens'],
            'total_pedidos': dados['total_pedidos'],
            'gasto_mensal': dados['total_gasto'] / meses,
        })
    linhas.sort(key=lambda l: l['gasto_mensal'], reverse=True)
    return linhas


# Monta o ranking (por município ou por circunscrição) agregando direto no banco
# (GROUP BY), em vez de iterar linha a linha em Python — necessário porque
# BensPermanentes sozinho já passa de 40 mil registros.
def _montar_ranking(campo_agrupamento, filtro_extra=None):
    dados = defaultdict(_linha_ranking_vazia)
    nomes = {}

    solicitacoes = (
        Solicitacao.objects
        .filter(
            **{f'ua_order__{campo_agrupamento}__isnull': False},
            **{f'ua_order__{k}': v for k, v in (filtro_extra or {}).items()},
        )
        .values(f'ua_order__{campo_agrupamento}')
        .annotate(total=Count('id'), primeira=Min('data_order'), ultima=Max('data_order'))
    )
    for linha in solicitacoes:
        chave = linha[f'ua_order__{campo_agrupamento}']
        dados[chave]['total_pedidos'] = linha['total']
        dados[chave]['primeira'] = linha['primeira']
        dados[chave]['ultima'] = linha['ultima']

    itens = (
        SolicitacaoItens.objects
        .filter(
            item_order__isnull=False,
            amount_order__isnull=False,
            item_order__item_shock__preco_medio__isnull=False,
            **{f'request_defendant__ua_order__{campo_agrupamento}__isnull': False},
            **{f'request_defendant__ua_order__{k}': v for k, v in (filtro_extra or {}).items()},
        )
        .annotate(custo=F('amount_order') * F('item_order__item_shock__preco_medio'))
        .values(f'request_defendant__ua_order__{campo_agrupamento}')
        .annotate(total_gasto=Sum('custo'))
    )
    for linha in itens:
        chave = linha[f'request_defendant__ua_order__{campo_agrupamento}']
        dados[chave]['total_gasto'] = linha['total_gasto'] or Decimal('0')

    bens = (
        BensPermanentes.objects
        .filter(
            **{f'history_tombo__current_ua__{campo_agrupamento}__isnull': False},
            **{f'history_tombo__current_ua__{k}': v for k, v in (filtro_extra or {}).items()},
        )
        .values(f'history_tombo__current_ua__{campo_agrupamento}')
        .annotate(total=Count('id'))
    )
    for linha in bens:
        chave = linha[f'history_tombo__current_ua__{campo_agrupamento}']
        dados[chave]['total_bens'] = linha['total']

    if campo_agrupamento == 'municipio':
        for m in Municipio.objects.filter(pk__in=dados.keys()):
            nomes[m.pk] = m.nome
    else:
        nomes = {chave: chave for chave in dados.keys()}

    return _finalizar_ranking(dados, nomes)


@login_required
def ranking_gastos(request):
    ranking_municipios = _montar_ranking('municipio')
    ranking_circunscricoes = _montar_ranking('municipio__circunscricao', filtro_extra={'municipio__circunscricao__gt': ''})

    paginator = Paginator(ranking_municipios, 15)
    pagina_municipios = paginator.get_page(request.GET.get('pagina'))

    return render(request, 'dempam/ranking_gastos.html', {
        'pagina_municipios': pagina_municipios,
        'ranking_circunscricoes': ranking_circunscricoes,
    })


''' Mural de Avisos '''
# Publicar um novo aviso no mural do DEMPAM (exibido em /home/)
@gerencia_dempam_required
def aviso_criar(request):
    if request.method == 'POST':
        form = AvisoForm(request.POST)
        if form.is_valid():
            aviso = form.save(commit=False)
            aviso.autor = request.user
            aviso.save()
            messages.success(request, 'Aviso publicado no mural com sucesso.')
            return redirect('dempam:homepage')
    else:
        form = AvisoForm()

    return render(request, 'dempam/aviso_form.html', {'form': form})


''' Editar um aviso existente do mural '''
@gerencia_dempam_required
def aviso_editar(request, pk):
    aviso = get_object_or_404(Aviso, pk=pk)
    if request.method == 'POST':
        form = AvisoForm(request.POST, instance=aviso)
        if form.is_valid():
            form.save()
            messages.success(request, 'Aviso atualizado com sucesso.')
            return redirect('dempam:aviso_lista')
    else:
        form = AvisoForm(instance=aviso)

    return render(request, 'dempam/aviso_form.html', {'form': form, 'aviso': aviso, 'editando': True})


''' Listar avisos do mural (para gerenciar/excluir) '''
@gerencia_dempam_required
def aviso_lista(request):
    avisos = Aviso.objects.select_related('autor').all()
    return render(request, 'dempam/aviso_lista.html', {'avisos': avisos, 'now': timezone.now()})


''' Excluir um aviso do mural '''
@gerencia_dempam_required
@require_POST
def aviso_excluir(request, pk):
    aviso = get_object_or_404(Aviso, pk=pk)
    aviso.delete()
    messages.success(request, 'Aviso excluído com sucesso.')
    return redirect('dempam:aviso_lista')
