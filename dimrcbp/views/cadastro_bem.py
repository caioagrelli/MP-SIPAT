from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect
from django.contrib import messages

from dimrcbp.forms import CadastroBemForm
from dimrcbp.models import HistoryUas


@login_required
@permission_required('dimrcbp.add_benspermanentes', raise_exception=True)
def cadastro_bem(request):
    if request.method == 'POST':
        form = CadastroBemForm(request.POST, request.FILES)
        if form.is_valid():
            bem = form.save()

            # Cria o HistoryUas vinculado
            HistoryUas.objects.create(
                tombo=bem,
                current_ua=form.cleaned_data.get('current_ua'),
                current_year=form.cleaned_data.get('current_year'),
                current_responsible=form.cleaned_data.get('current_responsible') or '',
                current_registration=form.cleaned_data.get('current_registration') or '',
            )

            messages.success(request, f'Bem "{bem}" cadastrado com sucesso.')
            return redirect('dimrcbp:homepage')
        else:
            messages.error(request, 'Corrija os erros abaixo antes de salvar.')
    else:
        form = CadastroBemForm()

    return render(request, 'dimrcbp/cadastro_bem.html', {'form': form})
