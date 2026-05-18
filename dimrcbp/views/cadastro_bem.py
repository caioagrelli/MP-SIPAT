from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect
from django.contrib import messages

from dimrcbp.forms import CadastroBemForm
from dimrcbp.models import HistoryUas, sincronizar_atribuicao


@login_required
@permission_required('dimrcbp.add_benspermanentes', raise_exception=True)
def cadastro_bem(request):
    if request.method == 'POST':
        form = CadastroBemForm(request.POST, request.FILES)
        if form.is_valid():
            bem = form.save()

            # Cria o HistoryUas vinculado
            ua_inicial = form.cleaned_data.get('current_ua')
            HistoryUas.objects.create(
                tombo=bem,
                current_ua=ua_inicial,
                current_year=form.cleaned_data.get('current_year'),
            )

            # Atribui o bem ao gestor da UA inicial (se houver)
            sincronizar_atribuicao(bem, ua_inicial)

            messages.success(request, f'Bem "{bem}" cadastrado com sucesso.')
            return redirect('dimrcbp:homepage')
        else:
            messages.error(request, 'Corrija os erros abaixo antes de salvar.')
    else:
        form = CadastroBemForm()

    return render(request, 'dimrcbp/cadastro_bem.html', {'form': form})
