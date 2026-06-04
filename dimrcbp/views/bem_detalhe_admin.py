from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, get_object_or_404

from dimrcbp.models import BensPermanentes, HistoricoMudanca, MovimentacaoBem


@login_required
@permission_required('dimrcbp.view_benspermanentes', raise_exception=True)
def bem_detalhe_admin(request, tombo):
    bem = get_object_or_404(
        BensPermanentes.objects.select_related(
            'description__type__gruop',
            'history_tombo__current_ua',
            'history_tombo__last_ua',
            'history_tombo__penultimate_ua',
            'history_tombo__third_last_ua',
            'supllier',
        ),
        tombo=tombo,
    )
    historico = (
        HistoricoMudanca.objects
        .filter(bem=bem)
        .select_related('alterado_por')
        .order_by('-data')
    )
    movimentacoes = (
        MovimentacaoBem.objects
        .filter(bem=bem)
        .select_related('ua_origem', 'ua_destino', 'responsavel')
        .order_by('-data')[:5]
    )
    return render(request, 'dimrcbp/bem_detalhe_admin.html', {
        'bem': bem,
        'historico': historico,
        'movimentacoes': movimentacoes,
    })
