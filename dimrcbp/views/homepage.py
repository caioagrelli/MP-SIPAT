from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from ..models import BensPermanentes, MovimentacoesPermanentes, UseExternal
from ..utils import EstadoConservacao, SituacaoFisica

@login_required
def homepage(request):
    query     = request.GET.get('q', '').strip()
    f_state   = request.GET.get('state', '')
    f_situacion = request.GET.get('situacion', '')

    bens = BensPermanentes.objects.select_related('description', 'supllier').all()

    if query:
        bens = bens.filter(tombo__icontains=query) | \
               bens.filter(mark__icontains=query)  | \
               bens.filter(model__icontains=query) | \
               bens.filter(n_series__icontains=query)
        bens = bens.distinct()

    if f_state:
        bens = bens.filter(state=f_state)

    if f_situacion:
        bens = bens.filter(situacion=f_situacion)

    total_bens      = BensPermanentes.objects.count()
    bens_sucata     = BensPermanentes.objects.filter(state=EstadoConservacao.sucata)
    bens_precario   = BensPermanentes.objects.filter(state=EstadoConservacao.precario)
    movimentacoes   = MovimentacoesPermanentes.objects.select_related('tombo', 'destino', 'origem').order_by('-id')[:8]
    uso_externo     = UseExternal.objects.select_related('tombo').order_by('date_renovation')[:8]

    context = {
        'bens':           bens,
        'total_bens':     total_bens,
        'bens_sucata':    bens_sucata,
        'bens_precario':  bens_precario,
        'movimentacoes':  movimentacoes,
        'uso_externo':    uso_externo,
        'query':          query,
        'f_state':        f_state,
        'f_situacion':    f_situacion,
        'estados':        EstadoConservacao.choices,
        'situacoes':      SituacaoFisica.choices,
    }
    return render(request, 'dimrcbp/homepage.html', context)
