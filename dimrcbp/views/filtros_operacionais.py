from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from django.db.models import Q

from dimrcbp.models import BensPermanentes
from dimrcbp.utils import SituacaoFisica, EstadoConservacao
from dempam.models import InfoUA


@login_required
@permission_required('dimrcbp.view_benspermanentes', raise_exception=True)
def filtros_operacionais(request):
    qs = (
        BensPermanentes.objects
        .select_related(
            'description__type__gruop',
            'history_tombo__current_ua',
            'supllier',
        )
        .order_by('tombo')
    )

    tombo       = request.GET.get('tombo', '').strip()
    n_process   = request.GET.get('n_process', '').strip()
    descricao   = request.GET.get('descricao', '').strip()
    ua_id       = request.GET.get('ua', '').strip()
    situacion   = request.GET.get('situacion', '').strip()
    state       = request.GET.get('state', '').strip()

    pesquisou = any([tombo, n_process, descricao, ua_id, situacion, state])

    if tombo:
        qs = qs.filter(tombo__icontains=tombo)
    if n_process:
        qs = qs.filter(n_process__icontains=n_process)
    if descricao:
        qs = qs.filter(
            Q(description__description__icontains=descricao) |
            Q(description__subdescription__icontains=descricao)
        )
    if ua_id:
        qs = qs.filter(history_tombo__current_ua_id=ua_id)
    if situacion:
        qs = qs.filter(situacion=situacion)
    if state:
        qs = qs.filter(state=state)

    uas = InfoUA.objects.order_by('ua')

    return render(request, 'dimrcbp/filtros_operacionais.html', {
        'bens':        qs if pesquisou else BensPermanentes.objects.none(),
        'total':       qs.count() if pesquisou else 0,
        'pesquisou':   pesquisou,
        'uas':         uas,
        'situacoes':   SituacaoFisica.choices,
        'estados':     EstadoConservacao.choices,
        # valores para repovoar o form
        'f_tombo':     tombo,
        'f_n_process': n_process,
        'f_descricao': descricao,
        'f_ua':        ua_id,
        'f_situacion': situacion,
        'f_state':     state,
    })
