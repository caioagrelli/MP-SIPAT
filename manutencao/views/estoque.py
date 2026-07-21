from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect

from ..models import EstoqueManutencao
from ..forms import EstoqueManutencaoForm


@login_required
@permission_required('manutencao.access_manutencao', raise_exception=True)
def estoque_planilha(request):
    """Visualização simples, em formato de planilha, do estoque de manutenção."""
    itens = EstoqueManutencao.objects.select_related('locate').order_by('efisco')

    busca = request.GET.get('q', '').strip()
    if busca:
        itens = itens.filter(
            Q(efisco__icontains=busca) |
            Q(descricao__icontains=busca) |
            Q(mark__icontains=busca)
        )

    locate_id = request.GET.get('locate', '').strip()
    if locate_id:
        itens = itens.filter(locate_id=locate_id)

    return render(request, 'manutencao/estoque_planilha.html', {
        'itens': itens,
        'busca': busca,
        'total': itens.count(),
    })


@login_required
@permission_required('manutencao.access_manutencao', raise_exception=True)
def estoque_entrada(request):
    """Dar entrada no estoque — busca por E-Fisco: se já existir, soma a
    quantidade informada; se não existir, cadastra o item na hora."""
    form = EstoqueManutencaoForm()

    if request.method == 'POST':
        efisco = request.POST.get('efisco', '').strip()
        existente = EstoqueManutencao.objects.filter(efisco__iexact=efisco).first() if efisco else None

        qtd_str = request.POST.get('amount_shock', '').strip()
        try:
            qtd = int(qtd_str)
            if qtd < 1:
                raise ValueError
        except (ValueError, TypeError):
            qtd = None

        if existente:
            if qtd is None:
                messages.error(request, 'Informe uma quantidade válida (mínimo 1).')
                form = EstoqueManutencaoForm(request.POST)
            else:
                with transaction.atomic():
                    existente.amount_shock += qtd

                    descricao = request.POST.get('descricao', '').strip()
                    if descricao:
                        existente.descricao = descricao

                    mark = request.POST.get('mark', '').strip()
                    if mark:
                        existente.mark = mark

                    locate_id = request.POST.get('locate') or None
                    if locate_id:
                        existente.locate_id = locate_id

                    validity = request.POST.get('validity') or None
                    existente.validity = validity or existente.validity

                    form_input = request.POST.get('form_input', '').strip()
                    if form_input:
                        existente.form_input = form_input

                    if request.FILES.get('photo'):
                        existente.photo = request.FILES['photo']

                    existente.updated_by = request.user
                    existente.save()

                messages.success(
                    request,
                    f'Adicionadas {qtd} unidade(s) ao item "{existente.efisco}". '
                    f'Estoque atual: {existente.amount_shock}.'
                )
                return redirect('manutencao:homepage')
        else:
            form = EstoqueManutencaoForm(request.POST, request.FILES)
            if form.is_valid():
                novo = form.save(commit=False)
                novo.updated_by = request.user
                novo.save()
                messages.success(request, f'Item "{novo.efisco}" cadastrado e adicionado ao estoque com sucesso.')
                return redirect('manutencao:homepage')

    return render(request, 'manutencao/estoque_entrada.html', {'form': form})


# Busca de item já existente no estoque (autocomplete)
@login_required
@permission_required('manutencao.access_manutencao', raise_exception=True)
def estoque_search(request):
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse([], safe=False)
    resultados = (
        EstoqueManutencao.objects
        .filter(Q(efisco__icontains=q) | Q(descricao__icontains=q))
        .select_related('locate')
        .values(
            'id', 'efisco', 'descricao', 'medida', 'grupo', 'mark',
            'amount_shock', 'locate_id',
        )
        [:20]
    )
    return JsonResponse(list(resultados), safe=False)
