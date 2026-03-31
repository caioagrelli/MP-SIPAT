# Bibliotecas padrão do DJungle, You're in the jungle baby n-n-n-n-n-n-n-n knees, knees
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.contrib import messages

# Importação do código
from ..models import Estoque, BensConsumo            # Models do Estoque 
from ..forms import EstoqueForm, BensConsumoForm     # Forms para adicionar bens no Estoque 

# ========================================================
# CAMPOS DESTINADOS PARA GERENCIAR PARTES/AÇÕES DO ESTOQUE
# ========================================================


''' Estoque '''
# Adicionar itens no estoque 
@login_required
def stock_add(request):
    if request.method == 'POST':
        form = EstoqueForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                dados = form.cleaned_data

                estoque_existente = Estoque.objects.filter(
                    item_shock=dados['item_shock'],
                    mark=dados['mark'],
                    locate=dados['locate'],
                    validity=dados['validity'],
                ).first()

                if estoque_existente:
                    estoque_existente.amount_shock += dados['amount_shock']

                    estoque_existente.description_manual = dados['description_manual']
                    estoque_existente.monthly_consumption = dados['monthly_consumption']
                    estoque_existente.essential = dados['essential']
                    estoque_existente.form_input = dados['form_input']
                    estoque_existente.method = dados['method']

                    if dados.get('photo'):
                        estoque_existente.photo = dados['photo']

                    estoque_existente.updated_by = request.user
                    estoque_existente.save()

                    messages.success(
                        request,
                        'Item já existente no estoque. Quantidade atualizada com sucesso.'
                    )
                else:
                    novo_item = form.save(commit=False)
                    novo_item.updated_by = request.user
                    novo_item.save()

                    messages.success(
                        request,
                        'Novo item adicionado ao estoque com sucesso.'
                    )

                return redirect('dimms:homepage')
    else:
        form = EstoqueForm()

    return render(request, 'dimms/stock/stock_add.html', {
        'form': form
    })
    


''' Bem de Consumo '''
# Página para visualizar bens de consumo
@login_required
def bensconsumo(request):
    itens = BensConsumo.objects.all().order_by('efisco')

    busca = request.GET.get('q', '').strip()
    grupo = request.GET.get('grupo', '').strip()

    if busca:
        itens = itens.filter(
            Q(efisco__icontains=busca) |
            Q(descricao_efisco__icontains=busca)
        )

    if grupo:
        itens = itens.filter(grupo_consumo=grupo)

    grupos = BensConsumo._meta.get_field('grupo_consumo').choices

    context = {
        'itens': itens,
        'busca': busca,
        'grupo_selecionado': grupo,
        'grupos': grupos,
    }

    return render(request, 'dimms/stock/bensconsumo.html', context)

# Cadastrar Bem de Consumo
@login_required
def bensconsumo_add(request):
    if request.method == 'POST':
        form = BensConsumoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Bem de consumo cadastrado com sucesso!')
            return redirect('dimms:bensconsumo')
    else:
        form = BensConsumoForm()

    context = {
        'form': form
    }
    
    return render(request, 'dimms/stock/bensconsumo_add.html', context)

@login_required
def bensconsumo_delete(request, pk):
    item = get_object_or_404(BensConsumo, pk=pk)

    if request.method == 'POST':
        if item.bem_estoque.exists():
            messages.error(
                request,
                'Não é possível excluir este bem de consumo, pois ele está associado a itens no estoque.'
            )
            return redirect('dimms:bensconsumo')

        try:
            item.delete()
            messages.success(request, 'Bem de consumo excluído com sucesso!')
        except ProtectedError:
            messages.error(
                request,
                'Não é possível excluir este bem de consumo, pois existem registros vinculados no estoque.'
            )

        return redirect('dimms:bensconsumo')

    context = {
        'item': item,
        'tem_estoque': item.bem_estoque.exists(),
    }
    return render(request, 'dimms/stock/bensconsumo_delete.html', context)


@login_required
def bensconsumo_edit(request, pk):
    item = get_object_or_404(BensConsumo, pk=pk)

    if request.method == 'POST':
        form = BensConsumoForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Bem de consumo atualizado com sucesso!')
            return redirect('dimms:bensconsumo')
    else:
        form = BensConsumoForm(instance=item)

    context = {
        'form': form,
        'item': item,
    }
    return render(request, 'dimms/stock/bensconsumo_edit.html', context)