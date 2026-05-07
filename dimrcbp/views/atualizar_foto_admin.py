from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect

from dimrcbp.models import BensPermanentes


@login_required
@permission_required('dimrcbp.change_benspermanentes', raise_exception=True)
def atualizar_foto_admin(request, tombo):
    if request.method != 'POST':
        return redirect('dimrcbp:bem_detalhe_admin', tombo=tombo)

    bem = get_object_or_404(BensPermanentes, tombo=tombo)
    foto = request.FILES.get('foto')

    if not foto:
        messages.error(request, 'Selecione uma imagem para enviar.')
        return redirect('dimrcbp:bem_detalhe_admin', tombo=tombo)

    bem.photo = foto
    bem.save(update_fields=['photo'])
    messages.success(request, 'Foto atualizada com sucesso.')
    return redirect('dimrcbp:bem_detalhe_admin', tombo=tombo)
