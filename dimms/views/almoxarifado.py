# Importações do Django
import re

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render

# Importações do código
from ..models import Solicitacao, Estoque
from ..utils import StatusTramitacao
from dempam.models import LocalizacaoDEMPAM

# ====================================
# ALMOXARIFADO — ACESSO RÁPIDO (provisório)
# ====================================


''' Busca rápida de solicitações por UA ou código, pensada pro balcão do almoxarifado '''
@login_required
def almoxarifado_acesso_rapido(request):
    query = request.GET.get('q', '').strip()
    resultados = None

    if query:
        resultados = (
            Solicitacao.objects
            .filter(
                Q(request_code__icontains=query) |
                Q(ua_order__ua__icontains=query) |
                Q(ua_order__codigo__icontains=query) |
                Q(ua_order__sigla__icontains=query)
            )
            .select_related('ua_order')
            .order_by('-data_order')[:50]
        )

    abas_situacao = {
        'aguardando': StatusTramitacao.aguar_separada,
        'separadas': StatusTramitacao.separada,
    }

    aba = request.GET.get('aba', 'aguardando').strip()
    if aba not in abas_situacao:
        aba = 'aguardando'

    fila = (
        Solicitacao.objects
        .filter(situation=abas_situacao[aba])
        .select_related('ua_order')
        .order_by('-data_order')
    )

    total_aguardando = Solicitacao.objects.filter(situation=StatusTramitacao.aguar_separada).count()
    total_separadas = Solicitacao.objects.filter(situation=StatusTramitacao.separada).count()

    return render(request, 'dimms/almoxarifado/acesso_rapido.html', {
        'query': query,
        'resultados': resultados,
        'aba': aba,
        'fila': fila[:50],
        'total_fila': fila.count(),
        'total_aguardando': total_aguardando,
        'total_separadas': total_separadas,
    })


''' Busca de bem de consumo (por E-Fisco ou descrição) mostrando localização e quantidade em estoque '''
@login_required
def almoxarifado_item_search(request):
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse([], safe=False)

    itens = (
        Estoque.objects
        .filter(
            Q(item_shock__efisco__icontains=q) |
            Q(item_shock__descricao_efisco__icontains=q) |
            Q(description_manual__icontains=q)
        )
        .select_related('item_shock', 'locate__setor_sala')
        .prefetch_related('outras_localizacoes__setor_sala')
        [:20]
    )

    resultados = []
    for item in itens:
        localizacoes = []
        if item.locate:
            localizacoes.append({
                'codigo': str(item.locate),
                'setor': item.locate.setor_sala.setor if item.locate.setor_sala else '',
                'principal': True,
            })
        for loc in item.outras_localizacoes.all():
            localizacoes.append({
                'codigo': str(loc),
                'setor': loc.setor_sala.setor if loc.setor_sala else '',
                'principal': False,
            })

        resultados.append({
            'id': item.pk,
            'efisco': item.item_shock.efisco,
            'descricao': item.description_manual or item.item_shock.descricao_efisco,
            'quantidade': str(item.amount_shock),
            'medida': item.item_shock.get_medida_display(),
            'localizacoes': localizacoes,
        })

    return JsonResponse(resultados, safe=False)


''' Registrar a mudança de localização de um item (uma ou mais localizações), direto do balcão do almoxarifado '''
@login_required
def mudar_localizacao_estoque(request):
    if request.method != 'POST':
        return JsonResponse({'erro': 'Método não permitido.'}, status=405)

    item = Estoque.objects.filter(pk=request.POST.get('item_id')).select_related('locate').first()
    if not item:
        return JsonResponse({'erro': 'Item não encontrado.'}, status=404)

    localizacao_ids = [lid for lid in request.POST.getlist('localizacao_id') if lid]
    if not localizacao_ids:
        return JsonResponse({'erro': 'Selecione ao menos uma localização.'}, status=400)

    localizacoes_por_id = {
        str(loc.pk): loc
        for loc in LocalizacaoDEMPAM.objects.filter(pk__in=localizacao_ids)
    }
    if len(localizacoes_por_id) != len(set(localizacao_ids)):
        return JsonResponse({'erro': 'Uma ou mais localizações não foram encontradas.'}, status=404)

    # mantém a ordem escolhida pelo usuário — a primeira vira a localização principal
    ordenadas = [localizacoes_por_id[lid] for lid in dict.fromkeys(localizacao_ids)]
    principal, extras = ordenadas[0], ordenadas[1:]

    ja_estava = (
        item.locate_id == principal.pk
        and set(item.outras_localizacoes.values_list('pk', flat=True)) == {loc.pk for loc in extras}
    )
    if ja_estava:
        return JsonResponse({'erro': 'Essa já é a localização atual do item.'}, status=400)

    localizacao_anterior = str(item.locate) if item.locate else None
    item.locate = principal
    item.save(update_fields=['locate'])
    item.outras_localizacoes.set(extras)

    if extras:
        if len(extras) == 1:
            extra_txt = '1 localização adicional'
        else:
            extra_txt = f'{len(extras)} localizações adicionais'
        mensagem = f'{item.item_shock.efisco} movido para {principal} (+{extra_txt}).'
    else:
        mensagem = f'{item.item_shock.efisco} movido para {principal}.'

    return JsonResponse({
        'ok': True,
        'mensagem': mensagem,
        'localizacao_anterior': localizacao_anterior,
        'localizacao_nova': str(principal),
        'total_localizacoes': len(ordenadas),
    })


''' Resolve um intervalo de códigos de localização (ex.: "I11" até "I26") em localizações já cadastradas '''
@login_required
def localizacao_intervalo_ajax(request):
    de = request.GET.get('de', '').strip().upper()
    ate = request.GET.get('ate', '').strip().upper()

    padrao = re.compile(r'^([A-Z]*)(\d+)$')
    m_de, m_ate = padrao.match(de), padrao.match(ate)
    if not m_de or not m_ate:
        return JsonResponse({'erro': 'Informe os códigos de início e fim (ex.: I11 até I26).'}, status=400)

    prefixo_de, num_de = m_de.groups()
    prefixo_ate, num_ate = m_ate.groups()
    if prefixo_de != prefixo_ate:
        return JsonResponse({'erro': 'Início e fim precisam ter o mesmo prefixo (ex.: I11 até I26).'}, status=400)

    inicio, fim = int(num_de), int(num_ate)
    if inicio > fim:
        inicio, fim = fim, inicio
    if fim - inicio > 200:
        return JsonResponse({'erro': 'Intervalo muito grande — limite de 200 localizações por vez.'}, status=400)

    largura = len(num_de)
    codigos = [f'{prefixo_de}{str(n).zfill(largura)}' for n in range(inicio, fim + 1)]

    candidatas = (
        LocalizacaoDEMPAM.objects
        .filter(prateleira_pallet__istartswith=prefixo_de)
        .select_related('setor_sala')
    )
    mapa = {loc.prateleira_pallet.upper(): loc for loc in candidatas if loc.prateleira_pallet}

    encontrados, nao_encontrados = [], []
    for codigo in codigos:
        loc = mapa.get(codigo)
        if loc:
            encontrados.append(loc)
        else:
            nao_encontrados.append(codigo)

    return JsonResponse({
        'resultados': [
            {'id': loc.pk, 'codigo': loc.prateleira_pallet, 'setor': loc.setor_sala.setor if loc.setor_sala else ''}
            for loc in encontrados
        ],
        'nao_encontrados': nao_encontrados,
    })
