# Bibliotecas padrão do DJungle, You're in the jungle baby n-n-n-n-n-n-n-n knees, knees
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.contrib import messages

# Importação do código
from ..models import Estoque, BensConsumo            # Models do Estoque 
from ..forms import EstoqueForm, BensConsumoForm , stock_up  # Forms para adicionar bens no Estoque
from ..services import recalcular_consumo 

# ========================================================
# CAMPOS DESTINADOS PARA GERENCIAR PARTES/AÇÕES DO ESTOQUE
# ========================================================


''' Estoque '''
# Adicionar itens no estoque
@login_required
def stock_add(request):
    form = EstoqueForm()
    mode = 'novo'
    remessa_errors = {}
    remessa_item_pk = ''
    remessa_qty = ''

    if request.method == 'POST':
        mode = request.POST.get('mode', 'novo')

        if mode == 'remessa':
            item_pk  = request.POST.get('remessa_item', '').strip()
            qty_str  = request.POST.get('remessa_qty', '').strip()
            forma    = request.POST.get('remessa_form_input', '').strip()
            metodo   = request.POST.get('remessa_method', '').strip()

            item_obj = None
            qty = None

            if not item_pk:
                remessa_errors['item'] = 'Selecione um item.'
            else:
                item_obj = Estoque.objects.filter(pk=item_pk).first()
                if not item_obj:
                    remessa_errors['item'] = 'Item não encontrado.'

            try:
                qty = int(qty_str)
                if qty < 1:
                    raise ValueError
            except (ValueError, TypeError):
                remessa_errors['qty'] = 'Informe uma quantidade válida (mínimo 1).'

            if not remessa_errors:
                with transaction.atomic():
                    item_obj.amount_shock += qty
                    if forma:
                        item_obj.form_input = forma
                    if metodo:
                        item_obj.method = metodo
                    item_obj.updated_by = request.user
                    item_obj.save()

                messages.success(
                    request,
                    f'Adicionadas {qty} unidades ao item "{item_obj}".'
                )
                return redirect('dimms:homepage')

            remessa_item_pk = item_pk
            remessa_qty = qty_str

        else:
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
                        messages.success(request, 'Item já existente no estoque. Quantidade atualizada com sucesso.')
                    else:
                        novo_item = form.save(commit=False)
                        novo_item.updated_by = request.user
                        novo_item.save()
                        messages.success(request, 'Novo item adicionado ao estoque com sucesso.')

                    return redirect('dimms:homepage')

    estoque_items = Estoque.objects.select_related('item_shock').all().order_by('description_manual')

    return render(request, 'dimms/stock/stock_add.html', {
        'form': form,
        'estoque_items': estoque_items,
        'mode': mode,
        'remessa_errors': remessa_errors,
        'remessa_item_pk': remessa_item_pk,
        'remessa_qty': remessa_qty,
    })

@login_required
def stock_up(request):
    if request.method == "POST":
        form = stock_up(request.POST)
        if form.is_valid():
            item = form.cleaned_data["item_estoque"]
            quantidade = form.cleaned_data["quantidade_entrada"]
            forma_entrada = form.cleaned_data["form_input"]
            metodo = form.cleaned_data["method"]

            item.amount_shock += quantidade

            if forma_entrada:
                item.form_input = forma_entrada

            if metodo:
                item.method = metodo

            item.updated_by = request.user
            item.save()

            messages.success(
                request,
                f"Foram adicionadas {quantidade} unidades ao item {item}."
            )
            return redirect("dimms:homepage")  # troque se quiser
    else:
        form = stock_up()

    return render(
        request,
        "dimms/stock/stock_up.html",
        {"form": form}
    )
    
    
''' Bem de Consumo '''

@login_required
def recalcular_consumo_view(request):
    recalcular_consumo()
    messages.success(request, 'Consumo mensal recalculado com sucesso.')
    return redirect('dimms:bensconsumo')

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