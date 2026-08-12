from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

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
            messages.error(request, "Corrija os erros indicados abaixo antes de salvar.")
    else:
        formset = SolicitacaoItemFormSet(instance=solicitacao)

    context = {
        "solicitacao": solicitacao,
        "formset": formset,
    }
    return render(request, "dimms/solicitacao_itens/edit_itens.html", context)
