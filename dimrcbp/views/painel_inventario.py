from collections import defaultdict
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse

from dimrcbp.models import AtribuicaoBem, Inventario, PeriodoInventario
from dimrcbp.forms import AbrirInventarioForm


@login_required
@permission_required('dimrcbp.view_inventario', raise_exception=True)
def painel_inventario(request):
    periodos = PeriodoInventario.objects.order_by('-inicio')

    periodo_pk = request.GET.get('periodo')
    if periodo_pk:
        periodo = get_object_or_404(PeriodoInventario, pk=periodo_pk)
    else:
        periodo = PeriodoInventario.get_periodo_ativo() or periodos.first()

    form_abrir = AbrirInventarioForm()

    if not periodo:
        return render(request, 'dimrcbp/painel_inventario.html', {
            'periodos':   periodos,
            'periodo':    None,
            'form_abrir': form_abrir,
        })

    # Todos os bens com atribuição ativa
    atribuicoes = (
        AtribuicaoBem.objects
        .filter(ativo=True)
        .select_related('bem__description', 'user')
        .order_by('user__first_name', 'user__last_name', 'bem__tombo')
    )

    # Registros já feitos para este período
    registros = {
        r.bem_id: r
        for r in Inventario.objects
                            .filter(n_inventario=periodo)
                            .select_related('bem', 'registrado_por')
    }

    # Agrupa por usuário responsável
    por_usuario = defaultdict(lambda: {'registrados': [], 'pendentes': []})
    for at in atribuicoes:
        bucket = por_usuario[at.user]
        if at.bem_id in registros:
            bucket['registrados'].append({'bem': at.bem, 'registro': registros[at.bem_id]})
        else:
            bucket['pendentes'].append({'bem': at.bem})

    usuarios_data = []
    for user, data in por_usuario.items():
        total = len(data['registrados']) + len(data['pendentes'])
        usuarios_data.append({
            'user':        user,
            'registrados': data['registrados'],
            'pendentes':   data['pendentes'],
            'total':       total,
            'concluido':   len(data['pendentes']) == 0,
        })

    # Pendentes primeiro, depois alfabético
    usuarios_data.sort(key=lambda x: (x['concluido'], x['user'].get_full_name() or x['user'].username))

    total_bens        = sum(u['total']            for u in usuarios_data)
    total_registrados = sum(len(u['registrados']) for u in usuarios_data)
    total_pendentes   = sum(len(u['pendentes'])   for u in usuarios_data)
    pct = round(total_registrados / total_bens * 100) if total_bens else 0

    return render(request, 'dimrcbp/painel_inventario.html', {
        'periodos':          periodos,
        'periodo':           periodo,
        'usuarios_data':     usuarios_data,
        'total_bens':        total_bens,
        'total_registrados': total_registrados,
        'total_pendentes':   total_pendentes,
        'pct':               pct,
        'inventario_ativo':  PeriodoInventario.em_andamento(),
        'form_abrir':        form_abrir,
    })


@login_required
@permission_required('dimrcbp.add_periodoinventario', raise_exception=True)
def abrir_inventario(request):
    if request.method != 'POST':
        return redirect('dimrcbp:painel_inventario')

    form = AbrirInventarioForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Ano inválido.')
        return redirect('dimrcbp:painel_inventario')

    ano = form.cleaned_data['ano']

    if PeriodoInventario.objects.filter(inicio__year=ano).exists():
        messages.error(request, f'Já existe um inventário para o ano {ano}.')
        return redirect('dimrcbp:painel_inventario')

    periodo = PeriodoInventario.objects.create(
        descricao=f'Inventário {ano}',
        inicio=date(ano, 1, 1),
        fim=date(ano, 12, 31),
    )
    messages.success(request, f'Inventário {ano} aberto com sucesso.')
    return redirect(reverse('dimrcbp:painel_inventario') + f'?periodo={periodo.pk}')
