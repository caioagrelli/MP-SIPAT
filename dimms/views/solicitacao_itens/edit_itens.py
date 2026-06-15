import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.core.serializers.json import DjangoJSONEncoder

from ...models import Solicitacao
from ...forms import SolicitacaoItemFormSet


STATUS_EDITAVEIS = ["ATENDIMENTO", "AGUAR_SEPARACAO", "RASCUNHO"]


@login_required
def edit_solicitacao_itens(request, pk):
    solicitacao = get_object_or_404(Solicitacao, pk=pk)

    if solicitacao.situation not in STATUS_EDITAVEIS:
        messages.error(
            request,
            'Não é possível editar itens de uma solicitação com status igual ou superior a "Separada".'
        )
        return redirect("dimms:details_processing", pk=pk)

    if request.method == "POST":
        formset = SolicitacaoItemFormSet(request.POST, instance=solicitacao)
        if formset.is_valid():
            formset.save()
            messages.success(request, "Itens da solicitação atualizados com sucesso.")
            return redirect("dimms:details_processing", pk=pk)
    else:
        formset = SolicitacaoItemFormSet(instance=solicitacao)

    itens_iniciais = list(
        solicitacao.bens_solicitados
        .select_related("item_order__item_shock")
        .values(
            "id",
            "item_order_id",
            "amount_order",
            "item_order__item_shock__efisco",
            "item_order__item_shock__descricao_efisco",
        )
    )

    context = {
        "solicitacao": solicitacao,
        "formset": formset,
        "itens_iniciais_json": json.dumps(itens_iniciais, cls=DjangoJSONEncoder),
    }
    return render(request, "dimms/solicitacao_itens/edit_itens.html", context)
