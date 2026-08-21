from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.shortcuts import render, redirect
from django.contrib import messages

from dimrcbp.forms import CadastroBemForm
from dimrcbp.models import BensPermanentes, HistoryUas, sincronizar_atribuicao


def _criar_bem_serie(form, tombo, ua_inicial):
    bem = BensPermanentes.objects.create(
        tombo=tombo,
        description=form.cleaned_data['description'],
        mark=form.cleaned_data['mark'],
        model=form.cleaned_data['model'],
        n_series=form.cleaned_data['n_series'],
        acquisition_date=form.cleaned_data['acquisition_date'],
        garantia_vencimento=form.cleaned_data.get('garantia_vencimento'),
        value=form.cleaned_data['value'],
        state=form.cleaned_data.get('state'),
        situacion=form.cleaned_data.get('situacion'),
        entry_method=form.cleaned_data.get('entry_method') or 'Compra',
        n_empenho=form.cleaned_data.get('n_empenho') or 'S/Número',
        n_process=form.cleaned_data.get('n_process') or 'S/Número',
        modality=form.cleaned_data.get('modality') or 'Pregão Eletrônico',
        supllier=form.cleaned_data.get('supllier'),
        locate=form.cleaned_data.get('locate'),
    )
    HistoryUas.objects.create(
        tombo=bem,
        current_ua=ua_inicial,
        current_year=form.cleaned_data.get('current_year'),
    )
    sincronizar_atribuicao(bem, ua_inicial)
    return bem


@login_required
@permission_required('dimrcbp.add_benspermanentes', raise_exception=True)
def cadastro_bem(request):
    if request.method == 'POST':
        form = CadastroBemForm(request.POST, request.FILES)
        if form.is_valid():
            ua_inicial = form.cleaned_data.get('current_ua')

            if form.cleaned_data.get('modo_serie'):
                inicio = form.cleaned_data['tombo_inicio']
                fim = form.cleaned_data['tombo_fim']
                ja_existentes = set(form.cleaned_data.get('tombos_existentes') or [])

                criados = []
                with transaction.atomic():
                    for n in range(inicio, fim + 1):
                        tombo = str(n)
                        if tombo in ja_existentes:
                            continue
                        _criar_bem_serie(form, tombo, ua_inicial)
                        criados.append(tombo)

                messages.success(
                    request,
                    f'{len(criados)} bens cadastrados com sucesso (tombos {inicio} a {fim}).',
                )
                if ja_existentes:
                    exemplos = ', '.join(sorted(ja_existentes, key=int)[:15])
                    sufixo = '…' if len(ja_existentes) > 15 else ''
                    messages.warning(
                        request,
                        f'{len(ja_existentes)} tombo(s) já existiam e foram ignorados: {exemplos}{sufixo}',
                    )
            else:
                bem = form.save()

                HistoryUas.objects.create(
                    tombo=bem,
                    current_ua=ua_inicial,
                    current_year=form.cleaned_data.get('current_year'),
                )
                sincronizar_atribuicao(bem, ua_inicial)

                messages.success(request, f'Bem "{bem}" cadastrado com sucesso.')

            return redirect('dimrcbp:homepage')
        else:
            messages.error(request, 'Corrija os erros abaixo antes de salvar.')
    else:
        form = CadastroBemForm()

    return render(request, 'dimrcbp/cadastro_bem.html', {'form': form})
