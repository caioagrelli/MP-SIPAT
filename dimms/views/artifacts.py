# BIBLIOTECAS PADRÃO PYTHON
import os
import urllib.request
from io import BytesIO

# DJANGO
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.contrib import messages
from django.http import HttpResponse
from django.urls import reverse
from datetime import datetime
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles import finders

# BIBLIOTECAS EXTERNAS
import qrcode
from qrcode.constants import ERROR_CORRECT_M

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import mm
from reportlab.lib.utils import ImageReader

# MODELOS DO PROJETO
from ..models import *
from ..utils import *
from ..forms import *

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

    context = {
        'artifacts': artifacts_list,
        'query': query,
        'state_selected': state_selected,
        'state_choices': Artifacts._meta.get_field('state').choices,
        'total_artifacts': Artifacts.objects.count(),
    }

    return render(request, 'dimms/artifacts/artifacts.html', context)

@login_required
def artifacts_details(request, pk):
    artifact = get_object_or_404(Artifacts, pk=pk)
    itens_artifact = ItensArtifacts.objects.filter(artifacts=artifact).select_related('efisco')

    context = {
        'artifact': artifact,
        'itens_artifact': itens_artifact,
    }
    return render(request, 'dimms/artifacts/artifacts_details.html', context)


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