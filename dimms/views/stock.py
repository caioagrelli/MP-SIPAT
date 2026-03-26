# Bibliotecas padrão do DJungle, You're in the jungle baby n-n-n-n-n-n-n-n knees, knees
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.db import transaction
from django.contrib import messages

# Importação do código
from ..models import Estoque        # Models do Estoque 
from ..forms import EstoqueForm     # Forms para adicionar bens no Estoque 

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