from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone

from accounts.models import Profile
from dimrcbp.models import AtribuicaoBem, BensPermanentes, PeriodoInventario, Inventario
from dimrcbp.forms import InventarioForm

BENS_POR_PAGINA = 30


@login_required
def meus_bens(request):
    periodo = PeriodoInventario.get_periodo_ativo()
    status_filtro = request.GET.get('status', '').strip() if periodo else ''

    # Para cada bem, verifica se já tem registro no inventário ativo
    tombos_registrados = set()
    if periodo:
        tombos_registrados = set(
            Inventario.objects.filter(n_inventario=periodo)
            .values_list('bem__tombo', flat=True)
        )

    atribuicoes_qs = (
        AtribuicaoBem.objects
        .filter(user=request.user, ativo=True)
        .select_related(
            'bem__description__type',
            'bem__history_tombo__current_ua',
        )
        .order_by('bem__tombo')
    )
    bens_atribuidos_ids = set(atribuicoes_qs.values_list('bem_id', flat=True))

    # Bens das UAs que o usuário é membro ("Membro de", Painel Gerencial),
    # à parte dos bens atribuídos individualmente
    profile, _ = Profile.objects.get_or_create(user=request.user)
    uas_membro = profile.uas.all().order_by('ua')

    bens_membro_qs = (
        BensPermanentes.objects
        .filter(history_tombo__current_ua__in=uas_membro)
        .exclude(pk__in=bens_atribuidos_ids)
    )

    # KPIs do inventário (sobre TODOS os bens geridos, não só a página atual)
    todos_bens_ids = list(bens_atribuidos_ids) + list(bens_membro_qs.values_list('pk', flat=True))
    total_geral = len(todos_bens_ids)
    registrados_geral = 0
    dias_restantes = None
    if periodo:
        if todos_bens_ids:
            registrados_geral = Inventario.objects.filter(
                n_inventario=periodo, bem_id__in=todos_bens_ids
            ).count()
        dias_restantes = (periodo.fim - timezone.now().date()).days
    pendentes_geral = total_geral - registrados_geral

    # Filtro por status (só faz sentido com período ativo)
    if status_filtro == 'pendente':
        atribuicoes_qs = atribuicoes_qs.exclude(bem__tombo__in=tombos_registrados)
    elif status_filtro == 'registrado':
        atribuicoes_qs = atribuicoes_qs.filter(bem__tombo__in=tombos_registrados)

    total_atribuicoes = atribuicoes_qs.count()
    atribuicoes = Paginator(atribuicoes_qs, BENS_POR_PAGINA).get_page(request.GET.get('pagina'))

    bens_por_ua = []
    for ua in uas_membro:
        bens_ua_qs = (
            BensPermanentes.objects
            .filter(history_tombo__current_ua=ua)
            .exclude(pk__in=bens_atribuidos_ids)
            .select_related('description__type', 'history_tombo__current_ua')
            .order_by('tombo')
        )
        if status_filtro == 'pendente':
            bens_ua_qs = bens_ua_qs.exclude(tombo__in=tombos_registrados)
        elif status_filtro == 'registrado':
            bens_ua_qs = bens_ua_qs.filter(tombo__in=tombos_registrados)

        total_ua = bens_ua_qs.count()
        if total_ua:
            param = f'pagina_ua_{ua.pk}'
            pagina_ua = Paginator(bens_ua_qs, BENS_POR_PAGINA).get_page(request.GET.get(param))
            bens_por_ua.append({'ua': ua, 'bens': pagina_ua, 'total': total_ua, 'param': param})

    return render(request, 'dimrcbp/meus_bens.html', {
        'atribuicoes':       atribuicoes,
        'total':             total_atribuicoes,
        'inventario_ativo':  bool(periodo),
        'periodo':           periodo,
        'tombos_registrados': tombos_registrados,
        'bens_por_ua':       bens_por_ua,
        'total_bens_uas':    sum(grupo['total'] for grupo in bens_por_ua),
        'total_geral':       total_geral,
        'registrados_geral': registrados_geral,
        'pendentes_geral':   pendentes_geral,
        'dias_restantes':    dias_restantes,
        'status_filtro':     status_filtro,
    })


def _e_membro_da_ua(request, ua_id):
    if not ua_id:
        return False
    profile, _ = Profile.objects.get_or_create(user=request.user)
    return profile.uas.filter(pk=ua_id).exists()


@login_required
def detalhe_bem(request, tombo):
    bem = get_object_or_404(
        BensPermanentes.objects.select_related(
            'description__type__gruop',
            'history_tombo__current_ua',
            'supllier',
        ),
        tombo=tombo,
    )

    atribuicao = AtribuicaoBem.objects.filter(bem=bem, user=request.user, ativo=True).first()
    ua_atual_id = bem.history_tombo.current_ua_id if hasattr(bem, 'history_tombo') and bem.history_tombo else None
    e_membro_da_ua = _e_membro_da_ua(request, ua_atual_id)

    if not atribuicao and not e_membro_da_ua:
        raise Http404()

    # atribuição individual ou membro da UA atual do bem — qualquer um dos dois
    # dá direito a registrar o inventário deste bem
    pode_registrar = bool(atribuicao) or e_membro_da_ua

    periodo = PeriodoInventario.get_periodo_ativo()
    registro_inventario = None
    if periodo and pode_registrar:
        registro_inventario = Inventario.objects.filter(
            n_inventario=periodo, bem=bem
        ).first()

    return render(request, 'dimrcbp/meus_bens_detalhe.html', {
        'atribuicao':          atribuicao,
        'pode_registrar':      pode_registrar,
        'bem':                 bem,
        'inventario_ativo':    bool(periodo) and pode_registrar,
        'periodo':             periodo,
        'registro_inventario': registro_inventario,
        'form_inventario':     InventarioForm(instance=registro_inventario) if periodo and pode_registrar else None,
    })


@login_required
def registrar_inventario(request, tombo):
    periodo = PeriodoInventario.get_periodo_ativo()
    if not periodo:
        messages.error(request, 'Não há período de inventário ativo.')
        return redirect('dimrcbp:detalhe_bem', tombo=tombo)

    bem = get_object_or_404(BensPermanentes.objects.select_related('history_tombo__current_ua'), tombo=tombo)
    atribuicao = AtribuicaoBem.objects.filter(bem=bem, user=request.user, ativo=True).first()
    ua_atual_id = bem.history_tombo.current_ua_id if hasattr(bem, 'history_tombo') and bem.history_tombo else None
    if not atribuicao and not _e_membro_da_ua(request, ua_atual_id):
        raise Http404()

    if request.method != 'POST':
        return redirect('dimrcbp:detalhe_bem', tombo=tombo)

    registro_existente = Inventario.objects.filter(
        n_inventario=periodo, bem=bem
    ).first()

    form = InventarioForm(request.POST, request.FILES, instance=registro_existente)
    if form.is_valid():
        registro = form.save(commit=False)
        registro.n_inventario  = periodo
        registro.bem           = bem
        registro.registrado_por = request.user
        registro.save()
        acao = 'atualizado' if registro_existente else 'registrado'
        messages.success(request, f'Bem {acao} no inventário com sucesso.')
    else:
        for erros in form.errors.values():
            for erro in erros:
                messages.error(request, erro)

    return redirect('dimrcbp:detalhe_bem', tombo=tombo)


@login_required
def atualizar_foto(request, tombo):
    if not PeriodoInventario.em_andamento():
        messages.error(request, 'A atualização de foto só é permitida durante o período de inventário.')
        return redirect('dimrcbp:detalhe_bem', tombo=tombo)

    bem = get_object_or_404(BensPermanentes.objects.select_related('history_tombo__current_ua'), tombo=tombo)
    atribuicao = AtribuicaoBem.objects.filter(bem=bem, user=request.user, ativo=True).first()
    ua_atual_id = bem.history_tombo.current_ua_id if hasattr(bem, 'history_tombo') and bem.history_tombo else None
    if not atribuicao and not _e_membro_da_ua(request, ua_atual_id):
        raise Http404()

    if request.method != 'POST':
        return redirect('dimrcbp:detalhe_bem', tombo=tombo)

    foto = request.FILES.get('foto')
    if not foto:
        messages.error(request, 'Selecione uma imagem para enviar.')
        return redirect('dimrcbp:detalhe_bem', tombo=tombo)

    bem.photo = foto
    bem.save(update_fields=['photo'])
    messages.success(request, 'Foto atualizada com sucesso.')
    return redirect('dimrcbp:detalhe_bem', tombo=tombo)
