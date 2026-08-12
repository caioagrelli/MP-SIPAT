# Importações do Django     - D(Artocarpus heterophyllus)o
from decimal import Decimal, InvalidOperation

from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse

# Importações do Projeto
from django.db import transaction
from django.db.models.deletion import ProtectedError
from ..models import (
    Artifacts, Proposal, ItensArtifacts, ItensProposal, Supplier, Contrato, SaldoAtivo, BensConsumo,
    AditivoContrato, ItemAditivoContrato,
)
from ..forms import (
    ItensArtifactsForm, ArtifactDocumentsForm, ArtifactsCreateForm,
    ProposalForm, ItensProposalForm, ContratoForm, SaldoAtivoItemForm, SupplierForm,
)
from ..utils import StatusContrato

# ==============================================================
# CAMPOS DESTINADOS PARA GERENCIAR OS ARTEFATOS E AS PROPOSTAS
# ==============================================================


''' Artefatos '''
# Página provisória — módulo em reconstrução (novo fluxo a ser feito do zero)
@login_required
def artifacts_em_breve(request):
    return render(request, 'dimms/artifacts/em_breve.html')

# Página principal dos artefatos
@login_required
def artifacts(request):
    query = request.GET.get('q', '').strip()
    state_selected = request.GET.get('state', '').strip()

    artifacts_list = Artifacts.objects.all().order_by('-updated_at', '-id')

    if query:
        artifacts_list = artifacts_list.filter(
            Q(artifacts_code__icontains=query) |
            Q(description__icontains=query)
        )

    if state_selected:
        artifacts_list = artifacts_list.filter(state=state_selected)

    proposals = Proposal.objects.all().select_related('supplier', 'artifacts_proposal').order_by('-id')

    context = {
        'artifacts': artifacts_list,
        'proposals': proposals,
        'query': query,
        'state_selected': state_selected,
        'state_choices': Artifacts._meta.get_field('state').choices,
        'total_artifacts': Artifacts.objects.count(),
    }

    return render(request, 'dimms/artifacts/artifacts.html', context)

# Detalhes dos artefatos (pagina individual)
@login_required
def artifacts_details(request, pk):
    artifact = get_object_or_404(Artifacts, pk=pk)

    itens_artifact = (
        ItensArtifacts.objects
        .filter(artifacts=artifact)
        .select_related('efisco')
        .order_by('id')
    )

    proposals = (
        Proposal.objects
        .filter(artifacts_proposal=artifact)
        .select_related('supplier')
        .order_by('-id')
    )

    context = {
        'artifact': artifact,
        'itens_artifact': itens_artifact,
        'proposals': proposals,
    }
    return render(request, 'dimms/artifacts/artifacts_details.html', context)

# Editar itens dos artefatos
@login_required
def artifacts_edit(request, pk):
    item = get_object_or_404(ItensArtifacts, pk=pk)

    if request.method == 'POST':
        form = ItensArtifactsForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Item do artefato atualizado com sucesso.')
            return redirect('dimms:artifacts_details', pk=item.artifacts.pk)
    else:
        form = ItensArtifactsForm(instance=item)

    context = {
        'form': form,
        'item': item,
        'artifact': item.artifacts,
    }
    return render(request, 'dimms/artifacts/artifacts_edit.html', context)

# Busca de E-Fisco via AJAX (autocomplete)
@login_required
def efisco_search(request):
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse([], safe=False)
    resultados = (
        BensConsumo.objects
        .filter(Q(efisco__icontains=q) | Q(descricao_efisco__icontains=q))
        .values('id', 'efisco', 'descricao_efisco', 'medida', 'grupo_consumo')
        [:20]
    )
    return JsonResponse(list(resultados), safe=False)


# Adicionar novos Itens para os artefatos (múltiplos de uma vez)
@login_required
def artifacts_add(request, pk):
    artifact = get_object_or_404(Artifacts, pk=pk)

    if request.method == 'POST':
        count = int(request.POST.get('items_count', 0))
        criados = 0
        erros = []

        for i in range(count):
            efisco_id  = request.POST.get(f'item_{i}_efisco_id', '').strip()
            details    = request.POST.get(f'item_{i}_details', '').strip()
            amount     = request.POST.get(f'item_{i}_amount', '').strip()
            value_max  = request.POST.get(f'item_{i}_value_max', '').strip()

            if not efisco_id or not amount:
                continue

            try:
                efisco = BensConsumo.objects.get(pk=efisco_id)
                ItensArtifacts.objects.create(
                    artifacts=artifact,
                    efisco=efisco,
                    details=details,
                    amount=int(amount),
                    value_max=int(value_max) if value_max else None,
                )
                criados += 1
            except Exception as e:
                erros.append(str(e))

        if criados:
            messages.success(request, f'{criados} item(s) adicionado(s) ao artefato com sucesso.')
        for erro in erros:
            messages.error(request, erro)

        return redirect('dimms:artifacts_details', pk=artifact.pk)

    return render(request, 'dimms/artifacts/artifacts_add.html', {'artifact': artifact})

# Gerenciar documentos dos artefatos
@login_required
def artifacts_documents(request, pk):
    artifact = get_object_or_404(Artifacts, pk=pk)

    if request.method == 'POST':
        form = ArtifactDocumentsForm(request.POST, request.FILES, instance=artifact)
        if form.is_valid():
            form.save()
            messages.success(request, 'Documentos do artefato atualizados com sucesso.')
            return redirect('dimms:artifacts_details', pk=artifact.pk)
    else:
        form = ArtifactDocumentsForm(instance=artifact)

    context = {
        'artifact': artifact,
        'form': form,
    }
    return render(request, 'dimms/artifacts/artifacts_documents.html', context)

# Criar um novo artefato
@login_required
def artifacts_create(request):
    if request.method == 'POST':
        form = ArtifactsCreateForm(request.POST, request.FILES)
        supplier_form = SupplierForm(request.POST, prefix='supplier')

        cadastrar_supplier = request.POST.get('cadastrar_supplier') == '1'

        if cadastrar_supplier:
            if form.is_valid() and supplier_form.is_valid():
                with transaction.atomic():
                    artifact = form.save(commit=False)
                    artifact.updated_by = request.user
                    artifact.save()
                    supplier_form.save()
                messages.success(request, 'Artefato e fornecedor cadastrados com sucesso.')
                return redirect('dimms:artifacts_details', pk=artifact.pk)
        else:
            if form.is_valid():
                artifact = form.save(commit=False)
                artifact.updated_by = request.user
                artifact.save()
                messages.success(request, 'Artefato criado com sucesso.')
                return redirect('dimms:artifacts_details', pk=artifact.pk)
            supplier_form = SupplierForm(prefix='supplier')
    else:
        form = ArtifactsCreateForm()
        supplier_form = SupplierForm(prefix='supplier')

    return render(request, 'dimms/artifacts/artifacts_create.html', {
        'form': form,
        'supplier_form': supplier_form,
    })


''' Propostas '''
# ver os detalhes de cada proposta (página individual)
@login_required
def proposal_details(request, pk):
    proposal = get_object_or_404(
        Proposal.objects.select_related('supplier', 'artifacts_proposal'),
        pk=pk
    )

    proposal_items = (
        ItensProposal.objects
        .filter(proposal_item=proposal)
        .select_related(
            'proposal_item',
            'item',
            'item__artifacts',
            'item__efisco',
        )
        .order_by('id')
    )

    total_geral = sum(item.total_value for item in proposal_items)
    artifact = proposal.artifacts_proposal

    context = {
        'proposal': proposal,
        'artifact': artifact,
        'proposal_items': proposal_items,
        'total_geral': total_geral,
    }
    return render(request, 'dimms/artifacts/proposal_details.html', context)

# Aprovar ou recusar Itens da proposta
@login_required
@require_POST
def proposal_status(request, pk):
    proposal_item = get_object_or_404(ItensProposal, pk=pk)
    action = request.POST.get('action')
    reason = request.POST.get('reason', '').strip()

    if action == 'approve':
        proposal_item.state = 'APROVADO'
        proposal_item.reason = ''
        proposal_item.save(update_fields=['state', 'reason'])
        messages.success(request, 'Item aprovado com sucesso.')

    elif action == 'reject':
        if not reason:
            messages.error(request, 'Para recusar, é obrigatório informar o motivo da reprovação.')
            return redirect('dimms:proposal_details', pk=proposal_item.proposal_item.pk)

        proposal_item.state = 'RECUSADO'
        proposal_item.reason = reason
        proposal_item.save(update_fields=['state', 'reason'])
        messages.success(request, 'Item recusado com sucesso.')

    else:
        messages.error(request, 'Ação inválida.')

    return redirect('dimms:proposal_details', pk=proposal_item.proposal_item.pk)


# Criar proposta para um artefato
@login_required
def proposal_create(request, pk):
    artifact = get_object_or_404(Artifacts, pk=pk)

    if request.method == 'POST':
        form = ProposalForm(request.POST)
        if form.is_valid():
            proposal = form.save(commit=False)
            proposal.artifacts_proposal = artifact
            if not proposal.state:
                proposal.state = 'ANALISE'
            proposal.save()
            messages.success(request, f'Proposta {proposal.proposal_code} criada com sucesso.')
            return redirect('dimms:proposal_details', pk=proposal.pk)
    else:
        form = ProposalForm()

    return render(request, 'dimms/artifacts/proposal_create.html', {
        'form': form,
        'artifact': artifact,
        'suppliers': Supplier.objects.all().order_by('supplier'),
    })


# Adicionar item a uma proposta
@login_required
def proposal_item_add(request, pk):
    proposal = get_object_or_404(
        Proposal.objects.select_related('artifacts_proposal', 'supplier'),
        pk=pk
    )
    artifact = proposal.artifacts_proposal

    if request.method == 'POST':
        form = ItensProposalForm(request.POST, artifact=artifact)
        if form.is_valid():
            item = form.save(commit=False)
            item.proposal_item = proposal
            if not item.state:
                item.state = 'ANALISE'
            try:
                item.full_clean()
                item.save()
                messages.success(request, 'Item adicionado à proposta.')
            except Exception as e:
                messages.error(request, str(e))
            return redirect('dimms:proposal_details', pk=proposal.pk)
    else:
        form = ItensProposalForm(artifact=artifact)

    return render(request, 'dimms/artifacts/proposal_item_add.html', {
        'form': form,
        'proposal': proposal,
        'artifact': artifact,
    })


# Remover item de uma proposta
@login_required
@require_POST
def proposal_item_delete(request, pk):
    item = get_object_or_404(ItensProposal, pk=pk)
    proposal_pk = item.proposal_item.pk
    item.delete()
    messages.success(request, 'Item removido da proposta.')
    return redirect('dimms:proposal_details', pk=proposal_pk)


# Criar contrato diretamente (sem proposta), acessível pelo saldo ativo
@login_required
def contrato_criar_saldoativo(request):
    fornecedores = Supplier.objects.order_by('supplier').values_list('supplier', flat=True)

    if request.method == 'POST':
        supplier_name = request.POST.get('supplier_name', '').strip()
        if not supplier_name:
            messages.error(request, 'Informe o nome do fornecedor.')
            form = ContratoForm(request.POST)
            return render(request, 'dimms/saldo_ativo/contrato_create.html', {
                'form': form, 'fornecedores': fornecedores,
            })

        supplier, _ = Supplier.objects.get_or_create(
            supplier=supplier_name,
            defaults={'name_responsible': '', 'cnpj_supplier': '', 'cpf_responsible': ''},
        )

        data = request.POST.copy()
        data['supplier_contract'] = supplier.pk
        form = ContratoForm(data)
        if form.is_valid():
            contrato = form.save()
            messages.success(request, f'Contrato {contrato.contrato} criado. Adicione os itens ao saldo ativo abaixo.')
            return redirect('dimms:contrato_detail', pk=contrato.pk)
    else:
        form = ContratoForm()

    return render(request, 'dimms/saldo_ativo/contrato_create.html', {
        'form': form, 'fornecedores': fornecedores,
    })


# Criar contrato a partir de uma proposta aprovada
@login_required
def contrato_create(request, pk):
    proposal = get_object_or_404(
        Proposal.objects.select_related('supplier', 'artifacts_proposal'),
        pk=pk
    )

    if request.method == 'POST':
        form = ContratoForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                contrato = form.save()
                proposal.state = 'APROVADO'
                proposal.save(update_fields=['state'])
            messages.success(request, f'Contrato {contrato.contrato} criado com sucesso.')
            from django.urls import reverse
            return redirect(reverse('dimms:contrato_detail', args=[contrato.pk]) + f'?from_proposal={proposal.pk}')
    else:
        form = ContratoForm(initial={'supplier_contract': proposal.supplier})

    return render(request, 'dimms/artifacts/contrato_create.html', {
        'form': form,
        'proposal': proposal,
    })


# Detalhes do contrato + gestão do saldo ativo
@login_required
def contrato_detail(request, pk):
    contrato = get_object_or_404(
        Contrato.objects.select_related('supplier_contract'),
        pk=pk
    )
    saldos = SaldoAtivo.objects.filter(
        contrato_saldo=contrato
    ).select_related('efisco')

    from ..models import SolicitacoesSaldoAtivo
    solicitacoes = SolicitacoesSaldoAtivo.objects.filter(
        contrato=contrato
    ).select_related('usuario').order_by('-data_hora')

    form_contrato = ContratoForm(instance=contrato)

    active_tab = request.GET.get('tab', 'info')

    if request.method == 'POST' and 'delete_saldo' in request.POST:
        saldo_id = request.POST.get('saldo_id')
        saldo = get_object_or_404(SaldoAtivo, pk=saldo_id, contrato_saldo=contrato)
        saldo.delete()
        messages.success(request, 'Item removido do saldo ativo.')
        return redirect(f"{request.path}?tab=saldo")

    if request.method == 'POST' and 'edit_contrato' in request.POST:
        form_contrato = ContratoForm(request.POST, instance=contrato)
        if form_contrato.is_valid():
            form_contrato.save()
            messages.success(request, 'Contrato atualizado com sucesso.')
            return redirect(f"{request.path}?tab=editar")
        active_tab = 'editar'

    if request.method == 'POST' and 'delete_contrato' in request.POST:
        if not request.user.has_perm('dimms.delete_contrato'):
            raise PermissionDenied('Você não tem permissão para excluir contratos.')
        if solicitacoes.exists():
            messages.error(
                request,
                'Não é possível excluir: este contrato tem solicitações de saldo ativo vinculadas. '
                'Marque o contrato como "Cancelado" em vez de excluir.'
            )
            return redirect(f"{request.path}?tab=editar")
        try:
            with transaction.atomic():
                saldos.all().delete()
                nome_contrato = contrato.contrato
                contrato.delete()
        except ProtectedError:
            messages.error(
                request,
                'Não é possível excluir: existem itens do saldo ativo deste contrato que já foram '
                'usados em solicitações. Marque o contrato como "Cancelado" em vez de excluir.'
            )
            return redirect(f"{request.path}?tab=editar")
        messages.success(request, f'Contrato "{nome_contrato}" excluído com sucesso.')
        return redirect('dimms:saldo_ativo_homepage')

    from_proposal_pk = request.GET.get('from_proposal')
    from_proposal = None
    if from_proposal_pk:
        from_proposal = Proposal.objects.filter(pk=from_proposal_pk).first()

    aditivos = (
        AditivoContrato.objects
        .filter(contrato=contrato)
        .select_related('criado_por')
        .prefetch_related('itens')
    )

    return render(request, 'dimms/artifacts/contrato_detail.html', {
        'contrato': contrato,
        'saldos': saldos,
        'solicitacoes': solicitacoes,
        'aditivos': aditivos,
        'form_contrato': form_contrato,
        'from_proposal': from_proposal,
        'active_tab': active_tab,
    })


# Tela dedicada para adicionar um item ao saldo ativo de um contrato
@login_required
def contrato_saldo_add(request, pk):
    contrato = get_object_or_404(Contrato, pk=pk)

    if contrato.status == StatusContrato.cancelado:
        messages.error(request, 'Contrato cancelado — não é possível adicionar itens.')
        return redirect(f"{reverse('dimms:contrato_detail', args=[contrato.pk])}?tab=saldo")

    if request.method == 'POST':
        form = SaldoAtivoItemForm(request.POST)
        if form.is_valid():
            saldo = form.save(commit=False)
            saldo.contrato_saldo = contrato
            try:
                saldo.full_clean()
                saldo.save()
                messages.success(request, f'Item {saldo.efisco.efisco} adicionado ao saldo ativo.')
                return redirect(f"{reverse('dimms:contrato_detail', args=[contrato.pk])}?tab=saldo")
            except Exception as e:
                messages.error(request, str(e))
    else:
        form = SaldoAtivoItemForm()

    return render(request, 'dimms/artifacts/contrato_saldo_add.html', {
        'contrato': contrato,
        'form': form,
    })


# Tela dedicada pra criar um aditivo de contrato — acrescenta quantidade em itens já
# existentes no saldo ativo e/ou adiciona itens novos (por E-Fisco) ao contrato
@login_required
def contrato_aditivo_create(request, pk):
    contrato = get_object_or_404(Contrato, pk=pk)

    if contrato.status == StatusContrato.cancelado:
        messages.error(request, 'Contrato cancelado — não é possível criar aditivo.')
        return redirect(f"{reverse('dimms:contrato_detail', args=[contrato.pk])}?tab=aditivo")

    saldos = (
        SaldoAtivo.objects
        .filter(contrato_saldo=contrato)
        .select_related('efisco')
        .order_by('efisco__efisco')
    )

    if request.method == 'POST':
        numero_empenho = request.POST.get('numero_empenho', '').strip()
        documento = request.FILES.get('documento')

        erros = []

        # itens já existentes no contrato — acréscimo de quantidade. Se o item já tem preço
        # cadastrado no saldo, usa ele; se não tem, exige que o preço seja informado agora.
        itens_existentes = []
        for saldo in saldos:
            raw_qtd = request.POST.get(f'qtd_saldo_{saldo.pk}', '').strip().replace(',', '.')
            if not raw_qtd:
                continue
            try:
                qtd = Decimal(raw_qtd)
            except InvalidOperation:
                erros.append(f'Quantidade inválida para "{saldo.efisco.efisco}".')
                continue
            if qtd <= 0:
                continue

            if saldo.preco_unitario:
                preco = saldo.preco_unitario
            else:
                raw_preco = request.POST.get(f'preco_saldo_{saldo.pk}', '').strip().replace(',', '.')
                if not raw_preco:
                    erros.append(f'Informe o preço unitário de "{saldo.efisco.efisco}" pra acrescer a quantidade.')
                    continue
                try:
                    preco = Decimal(raw_preco)
                except InvalidOperation:
                    erros.append(f'Preço unitário inválido para "{saldo.efisco.efisco}".')
                    continue
                if preco <= 0:
                    erros.append(f'Preço unitário de "{saldo.efisco.efisco}" precisa ser maior que zero.')
                    continue

            itens_existentes.append((saldo, qtd, preco))

        # itens novos, adicionados via busca de E-Fisco — preço sempre obrigatório
        itens_novos = []
        novos_count = int(request.POST.get('novos_count', 0) or 0)
        for i in range(novos_count):
            efisco_id = request.POST.get(f'novo_{i}_efisco_id', '').strip()
            qtd_raw = request.POST.get(f'novo_{i}_qtd', '').strip().replace(',', '.')
            preco_raw = request.POST.get(f'novo_{i}_preco', '').strip().replace(',', '.')
            if not efisco_id or not qtd_raw:
                continue
            try:
                qtd = Decimal(qtd_raw)
            except InvalidOperation:
                erros.append('Quantidade inválida em um dos itens novos.')
                continue
            if qtd <= 0:
                continue
            if not preco_raw:
                erros.append('Informe o preço unitário de todos os itens novos.')
                continue
            try:
                preco = Decimal(preco_raw)
            except InvalidOperation:
                erros.append('Preço unitário inválido em um dos itens novos.')
                continue
            if preco <= 0:
                erros.append('Preço unitário dos itens novos precisa ser maior que zero.')
                continue
            itens_novos.append((efisco_id, qtd, preco))

        if erros:
            for erro in erros:
                messages.error(request, erro)
            return redirect('dimms:contrato_aditivo_add', pk=contrato.pk)

        if not itens_existentes and not itens_novos:
            messages.error(request, 'Informe pelo menos um item (existente ou novo) com quantidade a acrescer.')
            return redirect('dimms:contrato_aditivo_add', pk=contrato.pk)

        with transaction.atomic():
            aditivo = AditivoContrato.objects.create(
                contrato=contrato,
                numero_empenho=numero_empenho,
                documento=documento,
                criado_por=request.user,
            )

            for saldo, qtd, preco in itens_existentes:
                saldo_locked = SaldoAtivo.objects.select_for_update().get(pk=saldo.pk)
                ItemAditivoContrato.objects.create(
                    aditivo=aditivo, efisco=saldo_locked.efisco, quantidade_acrescida=qtd,
                    preco_unitario=preco, item_novo=False,
                )
                saldo_locked.quantidade_contrato = (saldo_locked.quantidade_contrato or 0) + qtd
                saldo_locked.saldo_disponivel = (saldo_locked.saldo_disponivel or 0) + qtd
                update_fields = ['quantidade_contrato', 'saldo_disponivel']
                if not saldo_locked.preco_unitario:
                    saldo_locked.preco_unitario = preco
                    update_fields.append('preco_unitario')
                saldo_locked.save(update_fields=update_fields)

            for efisco_id, qtd, preco in itens_novos:
                efisco = get_object_or_404(BensConsumo, pk=efisco_id)
                ItemAditivoContrato.objects.create(
                    aditivo=aditivo, efisco=efisco, quantidade_acrescida=qtd,
                    preco_unitario=preco, item_novo=True,
                )
                saldo_existente = SaldoAtivo.objects.select_for_update().filter(
                    contrato_saldo=contrato, efisco=efisco,
                ).first()
                if saldo_existente:
                    saldo_existente.quantidade_contrato = (saldo_existente.quantidade_contrato or 0) + qtd
                    saldo_existente.saldo_disponivel = (saldo_existente.saldo_disponivel or 0) + qtd
                    update_fields = ['quantidade_contrato', 'saldo_disponivel']
                    if not saldo_existente.preco_unitario:
                        saldo_existente.preco_unitario = preco
                        update_fields.append('preco_unitario')
                    saldo_existente.save(update_fields=update_fields)
                else:
                    SaldoAtivo.objects.create(
                        contrato_saldo=contrato, efisco=efisco, quantidade_contrato=qtd, preco_unitario=preco,
                    )

        messages.success(request, f'Aditivo {aditivo.numero} criado com sucesso — valor total acrescido: R$ {aditivo.valor_total:.2f}')
        return redirect(f"{reverse('dimms:contrato_detail', args=[contrato.pk])}?tab=aditivo")

    return render(request, 'dimms/artifacts/contrato_aditivo_add.html', {
        'contrato': contrato,
        'saldos': saldos,
    })


# Gerar saldo ativo automaticamente dos itens aprovados de uma proposta
@login_required
@require_POST
def contrato_gerar_saldo(request, contrato_pk, proposal_pk):
    contrato = get_object_or_404(Contrato, pk=contrato_pk)
    proposal = get_object_or_404(Proposal, pk=proposal_pk)

    itens_aprovados = ItensProposal.objects.filter(
        proposal_item=proposal,
        state='APROVADO'
    ).select_related('item__efisco')

    criados = 0
    ignorados = 0
    for item in itens_aprovados:
        exists = SaldoAtivo.objects.filter(
            contrato_saldo=contrato,
            efisco=item.item.efisco
        ).exists()
        if not exists:
            SaldoAtivo.objects.create(
                contrato_saldo=contrato,
                efisco=item.item.efisco,
                quantidade_contrato=item.amount,
            )
            criados += 1
        else:
            ignorados += 1

    if criados:
        messages.success(request, f'{criados} item(s) gerado(s) no saldo ativo.')
    if ignorados:
        messages.warning(request, f'{ignorados} item(s) ignorado(s) por já existir no saldo deste contrato.')

    return redirect('dimms:contrato_detail', pk=contrato_pk)
