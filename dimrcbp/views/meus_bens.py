from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404
from django.contrib import messages

from accounts.models import Profile
from dimrcbp.models import AtribuicaoBem, BensPermanentes, PeriodoInventario, Inventario
from dimrcbp.forms import InventarioForm


@login_required
def meus_bens(request):
    atribuicoes = (
        AtribuicaoBem.objects
        .filter(user=request.user, ativo=True)
        .select_related(
            'bem__description__type',
            'bem__history_tombo__current_ua',
        )
        .order_by('bem__tombo')
    )
    periodo = PeriodoInventario.get_periodo_ativo()

    # Para cada bem, verifica se já tem registro no inventário ativo
    tombos_registrados = set()
    if periodo:
        tombos_registrados = set(
            Inventario.objects.filter(n_inventario=periodo)
            .values_list('bem__tombo', flat=True)
        )

    # Bens das UAs que o usuário é membro ("Membro de", Painel Gerencial),
    # à parte dos bens atribuídos individualmente
    bens_atribuidos_ids = {at.bem_id for at in atribuicoes}
    profile, _ = Profile.objects.get_or_create(user=request.user)
    uas_membro = profile.uas.all().order_by('ua')

    bens_por_ua = []
    for ua in uas_membro:
        bens_ua = (
            BensPermanentes.objects
            .filter(history_tombo__current_ua=ua)
            .exclude(pk__in=bens_atribuidos_ids)
            .select_related('description__type', 'history_tombo__current_ua')
            .order_by('tombo')
        )
        if bens_ua:
            bens_por_ua.append({'ua': ua, 'bens': bens_ua, 'total': bens_ua.count()})

    return render(request, 'dimrcbp/meus_bens.html', {
        'atribuicoes':       atribuicoes,
        'total':             atribuicoes.count(),
        'inventario_ativo':  bool(periodo),
        'periodo':           periodo,
        'tombos_registrados': tombos_registrados,
        'bens_por_ua':       bens_por_ua,
        'total_bens_uas':    sum(grupo['total'] for grupo in bens_por_ua),
    })


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

    if not atribuicao:
        # sem atribuição individual: só pode ver se for membro da UA atual do bem
        profile, _ = Profile.objects.get_or_create(user=request.user)
        ua_atual_id = bem.history_tombo.current_ua_id if hasattr(bem, 'history_tombo') and bem.history_tombo else None
        e_membro_da_ua = bool(ua_atual_id) and profile.uas.filter(pk=ua_atual_id).exists()
        if not e_membro_da_ua:
            raise Http404()

    periodo = PeriodoInventario.get_periodo_ativo()
    registro_inventario = None
    if periodo and atribuicao:
        registro_inventario = Inventario.objects.filter(
            n_inventario=periodo, bem=bem
        ).first()

    return render(request, 'dimrcbp/meus_bens_detalhe.html', {
        'atribuicao':          atribuicao,
        'bem':                 bem,
        'inventario_ativo':    bool(periodo) and bool(atribuicao),
        'periodo':             periodo,
        'registro_inventario': registro_inventario,
        'form_inventario':     InventarioForm(instance=registro_inventario) if periodo and atribuicao else None,
    })


@login_required
def registrar_inventario(request, tombo):
    periodo = PeriodoInventario.get_periodo_ativo()
    if not periodo:
        messages.error(request, 'Não há período de inventário ativo.')
        return redirect('dimrcbp:detalhe_bem', tombo=tombo)

    atribuicao = get_object_or_404(
        AtribuicaoBem,
        bem__tombo=tombo,
        user=request.user,
        ativo=True,
    )

    if request.method != 'POST':
        return redirect('dimrcbp:detalhe_bem', tombo=tombo)

    registro_existente = Inventario.objects.filter(
        n_inventario=periodo, bem=atribuicao.bem
    ).first()

    form = InventarioForm(request.POST, request.FILES, instance=registro_existente)
    if form.is_valid():
        registro = form.save(commit=False)
        registro.n_inventario  = periodo
        registro.bem           = atribuicao.bem
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

    atribuicao = get_object_or_404(
        AtribuicaoBem,
        bem__tombo=tombo,
        user=request.user,
        ativo=True,
    )

    if request.method != 'POST':
        return redirect('dimrcbp:detalhe_bem', tombo=tombo)

    foto = request.FILES.get('foto')
    if not foto:
        messages.error(request, 'Selecione uma imagem para enviar.')
        return redirect('dimrcbp:detalhe_bem', tombo=tombo)

    bem = atribuicao.bem
    bem.photo = foto
    bem.save(update_fields=['photo'])
    messages.success(request, 'Foto atualizada com sucesso.')
    return redirect('dimrcbp:detalhe_bem', tombo=tombo)
