from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

from dimrcbp.models import AtribuicaoBem, PeriodoInventario


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
    return render(request, 'dimrcbp/meus_bens.html', {
        'atribuicoes':     atribuicoes,
        'total':           atribuicoes.count(),
        'inventario_ativo': PeriodoInventario.em_andamento(),
    })


@login_required
def detalhe_bem(request, tombo):
    atribuicao = get_object_or_404(
        AtribuicaoBem.objects.select_related(
            'bem__description__type__gruop',
            'bem__history_tombo__current_ua',
            'bem__supllier',
        ),
        bem__tombo=tombo,
        user=request.user,
        ativo=True,
    )
    return render(request, 'dimrcbp/meus_bens_detalhe.html', {
        'atribuicao':      atribuicao,
        'bem':             atribuicao.bem,
        'inventario_ativo': PeriodoInventario.em_andamento(),
    })


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
