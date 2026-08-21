from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count
from django.utils import timezone
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse

from dempam.models import InfoUA
from dimrcbp.models import BensPermanentes, Inventario, PeriodoInventario
from dimrcbp.forms import AbrirInventarioForm

UAS_POR_PAGINA = 30


@login_required
def painel_inventario(request):
    is_admin = request.user.has_perm('dimrcbp.view_inventario')
    e_gestor = InfoUA.objects.filter(gestor=request.user).exists()
    if not is_admin and not e_gestor:
        raise PermissionDenied

    periodos = PeriodoInventario.objects.order_by('-inicio')

    periodo_pk = request.GET.get('periodo')
    if periodo_pk:
        periodo = get_object_or_404(PeriodoInventario, pk=periodo_pk)
    else:
        periodo = PeriodoInventario.get_periodo_ativo() or periodos.first()

    form_abrir = AbrirInventarioForm() if is_admin else None

    if not periodo:
        return render(request, 'dimrcbp/painel_inventario.html', {
            'periodos':   periodos,
            'periodo':    None,
            'is_admin':   is_admin,
            'form_abrir': form_abrir,
        })

    # Total de bens por UA — admin vê todas as UAs (mesmo sem gestor definido),
    # gestor só vê as UAs que ele mesmo gerencia. Agregado direto no banco:
    # evita iterar em Python os ~40 mil bens do sistema.
    bens_qs = BensPermanentes.objects.filter(history_tombo__current_ua__isnull=False)
    if not is_admin:
        bens_qs = bens_qs.filter(history_tombo__current_ua__gestor=request.user)

    totais_por_ua = {
        row['history_tombo__current_ua']: row['total']
        for row in bens_qs.values('history_tombo__current_ua').annotate(total=Count('id'))
    }

    registrados_por_ua = {}
    if totais_por_ua:
        registrados_qs = (
            Inventario.objects
            .filter(n_inventario=periodo, bem__history_tombo__current_ua__in=totais_por_ua.keys())
            .values('bem__history_tombo__current_ua')
            .annotate(registrados=Count('id'))
        )
        registrados_por_ua = {
            row['bem__history_tombo__current_ua']: row['registrados'] for row in registrados_qs
        }

    uas = InfoUA.objects.filter(pk__in=totais_por_ua.keys()).select_related('gestor')

    uas_data = []
    for ua in uas:
        total = totais_por_ua.get(ua.pk, 0)
        registrados = registrados_por_ua.get(ua.pk, 0)
        uas_data.append({
            'ua':          ua,
            'total':       total,
            'registrados': registrados,
            'pendentes':   total - registrados,
            'concluido':   registrados >= total,
        })

    # Pendentes primeiro, depois sem-gestor primeiro, depois alfabético
    uas_data.sort(key=lambda x: (x['concluido'], bool(x['ua'].gestor_id), x['ua'].ua))

    total_bens        = sum(u['total']       for u in uas_data)
    total_registrados = sum(u['registrados'] for u in uas_data)
    total_pendentes   = sum(u['pendentes']   for u in uas_data)
    pct = round(total_registrados / total_bens * 100) if total_bens else 0

    busca = request.GET.get('busca', '').strip()
    uas_filtradas = uas_data
    if busca:
        termo = busca.lower()
        uas_filtradas = [
            u for u in uas_data
            if termo in u['ua'].ua.lower()
            or (u['ua'].gestor and termo in (u['ua'].gestor.get_full_name() or u['ua'].gestor.username).lower())
        ]

    pagina_uas = Paginator(uas_filtradas, UAS_POR_PAGINA).get_page(request.GET.get('pagina'))

    hoje = timezone.now().date()
    return render(request, 'dimrcbp/painel_inventario.html', {
        'periodos':          periodos,
        'periodo':           periodo,
        'busca':             busca,
        'total_uas_filtradas': len(uas_filtradas),
        'uas_data':          pagina_uas,
        'total_uas':         len(uas_data),
        'total_bens':        total_bens,
        'total_registrados': total_registrados,
        'total_pendentes':   total_pendentes,
        'pct':               pct,
        'periodo_ativo':     periodo.inicio <= hoje <= periodo.fim,
        'form_abrir':        form_abrir,
        'is_admin':          is_admin,
    })


@login_required
@permission_required('dimrcbp.add_periodoinventario', raise_exception=True)
def abrir_inventario(request):
    if request.method != 'POST':
        return redirect('dimrcbp:painel_inventario')

    form = AbrirInventarioForm(request.POST)
    if not form.is_valid():
        for erros in form.errors.values():
            for erro in erros:
                messages.error(request, erro)
        return redirect('dimrcbp:painel_inventario')

    inicio = form.cleaned_data['inicio']
    fim = form.cleaned_data['fim']
    descricao = form.cleaned_data['descricao']

    sobreposto = PeriodoInventario.objects.filter(inicio__lte=fim, fim__gte=inicio).exists()
    if sobreposto:
        messages.error(request, 'Já existe um período de inventário que se sobrepõe a essas datas.')
        return redirect('dimrcbp:painel_inventario')

    periodo = PeriodoInventario.objects.create(
        descricao=descricao,
        inicio=inicio,
        fim=fim,
    )
    messages.success(
        request,
        f'"{periodo.descricao}" aberto com sucesso ({inicio.strftime("%d/%m/%Y")} a {fim.strftime("%d/%m/%Y")}).',
    )
    return redirect(reverse('dimrcbp:painel_inventario') + f'?periodo={periodo.pk}')


@login_required
@permission_required('dimrcbp.add_periodoinventario', raise_exception=True)
def fechar_inventario(request, pk):
    if request.method != 'POST':
        return redirect('dimrcbp:painel_inventario')

    periodo = get_object_or_404(PeriodoInventario, pk=pk)
    hoje = timezone.now().date()

    if periodo.fim < hoje:
        messages.warning(request, f'"{periodo.descricao}" já estava encerrado.')
    elif periodo.inicio > hoje:
        messages.error(request, f'"{periodo.descricao}" ainda não começou — não há o que encerrar.')
    else:
        periodo.fim = hoje - timezone.timedelta(days=1)
        periodo.save(update_fields=['fim'])
        messages.success(request, f'"{periodo.descricao}" encerrado com sucesso.')

    return redirect(reverse('dimrcbp:painel_inventario') + f'?periodo={periodo.pk}')
