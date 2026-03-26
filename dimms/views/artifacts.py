# Importações do Django     - D(Artocarpus heterophyllus)o
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

# Importações do Projeto
from ..models import Artifacts, Proposal, ItensArtifacts, ItensProposal
from ..forms import ItensArtifactsForm, ArtifactDocumentsForm, ArtifactsCreateForm

# ==============================================================
# CAMPOS DESTINADOS PARA GERENCIAR OS ARTEFATOS E AS PROPOSTAS
# ==============================================================


''' Artefatos '''
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

# Adicionar novos Itens para os artefatos
@login_required
def artifacts_add(request, pk):
    artifact = get_object_or_404(Artifacts, pk=pk)

    if request.method == 'POST':
        form = ItensArtifactsForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.artifacts = artifact
            item.save()

            messages.success(request, 'Novo item adicionado ao artefato com sucesso.')
            return redirect('dimms:artifacts_details', pk=artifact.pk)
    else:
        form = ItensArtifactsForm()

    context = {
        'form': form,
        'artifact': artifact,
    }
    return render(request, 'dimms/artifacts/artifacts_add.html', context)

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
        if form.is_valid():
            artifact = form.save()
            messages.success(request, 'Artefato criado com sucesso.')
            return redirect('dimms:artifacts_details', pk=artifact.pk)
    else:
        form = ArtifactsCreateForm()

    context = {
        'form': form,
    }
    return render(request, 'dimms/artifacts/artifacts_create.html', context)


''' Propostas '''
# ver os detalhes de cada proposta (página individual)
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
