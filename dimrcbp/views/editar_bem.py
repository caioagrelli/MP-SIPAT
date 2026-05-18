from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse

from dimrcbp.models import BensPermanentes, HistoricoMudanca

CAMPOS_EDITAVEIS = {
    'tombo':            'Tombo',
    'mark':             'Marca / Fabricante',
    'model':            'Modelo',
    'n_series':         'Número de Série',
    'acquisition_date':    'Data de Aquisição',
    'garantia_vencimento': 'Vencimento da Garantia',
    'value':               'Valor Unitário',
    'entry_method':     'Forma de Ingresso',
    'n_empenho':        'N° Empenho',
    'n_process':        'N° Processo',
    'modality':         'Modalidade',
    'state':            'Estado de Conservação',
    'situacion':        'Situação Física',
}


@login_required
@permission_required('dimrcbp.change_benspermanentes', raise_exception=True)
def editar_bem(request, tombo):
    bem = get_object_or_404(BensPermanentes, tombo=tombo)

    if request.method == 'POST':
        justificativa = request.POST.get('justificativa', '').strip()
        campos_alterados = {}

        # Campos de texto
        for campo, label in CAMPOS_EDITAVEIS.items():
            novo = request.POST.get(campo, '').strip()
            atual = str(getattr(bem, campo) or '')
            if novo and novo != atual:
                campos_alterados[campo] = {'label': label, 'de': atual, 'para': novo}
                setattr(bem, campo, novo)

        # Foto
        foto = request.FILES.get('foto')
        if foto:
            foto_anterior = bem.photo.name if bem.photo else None
            campos_alterados['photo'] = {
                'label': 'Foto do Bem',
                'de': foto_anterior or '(sem foto)',
                'para': foto.name,
            }
            bem.photo = foto

        if not campos_alterados:
            messages.warning(request, 'Nenhuma alteração detectada.')
            return redirect('dimrcbp:bem_detalhe_admin', tombo=bem.tombo)

        bem.save()
        registro = HistoricoMudanca.objects.create(
            bem=bem,
            alterado_por=request.user,
            justificativa=justificativa,
            campos=campos_alterados,
        )
        novo_tombo = campos_alterados.get('tombo', {}).get('para', tombo)
        url = reverse('dimrcbp:bem_detalhe_admin', args=[novo_tombo])
        return redirect(f'{url}?historico={registro.pk}')

    return render(request, 'dimrcbp/editar_bem.html', {
        'bem': bem,
        'campos_editaveis': CAMPOS_EDITAVEIS,
    })
