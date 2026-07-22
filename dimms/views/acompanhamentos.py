# Importações do Django
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST

# Importações do código
from ..models import Subject, Sei, SeiUpdate
from ..forms import SubjectForm, SeiForm, SeiUpdateForm
from ..utils import StatusAcompanhamentoSei

# ====================================================
# VIEWS DE ACOMPANHAMENTOS SEI (mapa geral, temas etc.)
# ====================================================

''' Busca de temas via AJAX (autocomplete no formulário de SEI) '''
@login_required
def temas_search(request):
    q = request.GET.get('q', '').strip()
    qs = Subject.objects.all().order_by('name')
    if q:
        qs = qs.filter(name__icontains=q)
    resultados = list(qs.values('id', 'name', 'color')[:20])
    return JsonResponse(resultados, safe=False)


''' Mapa geral — lista com filtros e busca '''
@login_required
@permission_required('dimms.view_sei', raise_exception=True)
def acompanhamentos_mapa(request):
    query = request.GET.get('q', '').strip()
    subject_id = request.GET.get('tema', '').strip()
    status_selected = request.GET.get('status', '').strip()

    seis = Sei.objects.select_related('subject', 'user')

    if query:
        seis = seis.filter(
            Q(sei_number__icontains=query) |
            Q(description__icontains=query) |
            Q(subject__name__icontains=query)
        )

    if subject_id:
        seis = seis.filter(subject_id=subject_id)

    if status_selected:
        seis = seis.filter(status=status_selected)

    seis = seis.order_by('-updated_at')

    context = {
        'seis': seis,
        'subjects': Subject.objects.all().order_by('name'),
        'query': query,
        'subject_selected': subject_id,
        'status_selected': status_selected,
        'status_choices': StatusAcompanhamentoSei.choices,
        'total_seis': Sei.objects.count(),
        'total_em_andamento': Sei.objects.filter(status=StatusAcompanhamentoSei.em_andamento).count(),
        'pode_criar_sei': request.user.has_perm('dimms.add_sei'),
        'pode_gerenciar_temas': request.user.has_perm('dimms.view_subject'),
    }
    return render(request, 'dimms/acompanhamentos/mapa_geral.html', context)


''' Detalhe de um acompanhamento + linha do tempo de updates '''
@login_required
@permission_required('dimms.view_sei', raise_exception=True)
def acompanhamento_detail(request, pk):
    sei = get_object_or_404(Sei.objects.select_related('subject', 'user'), pk=pk)
    updates = sei.updates.select_related('user').all()

    pode_atualizar = request.user.has_perm('dimms.add_seiupdate')
    form = SeiUpdateForm() if pode_atualizar else None

    if request.method == 'POST' and pode_atualizar:
        form = SeiUpdateForm(request.POST)
        if form.is_valid():
            update = form.save(commit=False)
            update.sei = sei
            update.user = request.user
            update.save()
            messages.success(request, 'Atualização registrada com sucesso.')
            return redirect('dimms:acompanhamento_detail', pk=sei.pk)

    context = {
        'sei': sei,
        'updates': updates,
        'form': form,
        'pode_editar': request.user.has_perm('dimms.change_sei'),
        'pode_excluir': request.user.has_perm('dimms.delete_sei'),
        'pode_excluir_update': request.user.has_perm('dimms.delete_seiupdate'),
    }
    return render(request, 'dimms/acompanhamentos/sei_detail.html', context)


''' Criar novo acompanhamento de SEI '''
@login_required
@permission_required('dimms.add_sei', raise_exception=True)
def acompanhamento_create(request):
    if request.method == 'POST':
        form = SeiForm(request.POST)
        if form.is_valid():
            sei = form.save(commit=False)
            sei.user = request.user
            sei.save()
            messages.success(request, f'Acompanhamento do SEI {sei.sei_number} criado com sucesso.')
            return redirect('dimms:acompanhamento_detail', pk=sei.pk)
    else:
        form = SeiForm()

    return render(request, 'dimms/acompanhamentos/sei_form.html', {
        'form': form,
        'action': 'Novo',
    })


''' Editar acompanhamento '''
@login_required
@permission_required('dimms.change_sei', raise_exception=True)
def acompanhamento_edit(request, pk):
    sei = get_object_or_404(Sei, pk=pk)

    if request.method == 'POST':
        form = SeiForm(request.POST, instance=sei)
        if form.is_valid():
            form.save()
            messages.success(request, 'Acompanhamento atualizado com sucesso.')
            return redirect('dimms:acompanhamento_detail', pk=sei.pk)
    else:
        form = SeiForm(instance=sei)

    return render(request, 'dimms/acompanhamentos/sei_form.html', {
        'form': form,
        'action': 'Editar',
        'sei': sei,
    })


''' Excluir acompanhamento '''
@login_required
@permission_required('dimms.delete_sei', raise_exception=True)
@require_POST
def acompanhamento_delete(request, pk):
    sei = get_object_or_404(Sei, pk=pk)
    numero = sei.sei_number
    sei.delete()
    messages.success(request, f'Acompanhamento do SEI {numero} excluído.')
    return redirect('dimms:acompanhamentos_mapa')


''' Excluir uma atualização específica '''
@login_required
@permission_required('dimms.delete_seiupdate', raise_exception=True)
@require_POST
def acompanhamento_update_delete(request, pk):
    update = get_object_or_404(SeiUpdate, pk=pk)
    sei_pk = update.sei_id
    update.delete()
    messages.success(request, 'Atualização removida.')
    return redirect('dimms:acompanhamento_detail', pk=sei_pk)


''' Temas — listagem + criação rápida '''
@login_required
@permission_required('dimms.view_subject', raise_exception=True)
def temas_lista(request):
    subjects = Subject.objects.annotate(total_seis=Count('seis')).order_by('name')

    pode_criar = request.user.has_perm('dimms.add_subject')
    form = SubjectForm() if pode_criar else None

    if request.method == 'POST' and pode_criar:
        form = SubjectForm(request.POST)
        if form.is_valid():
            tema = form.save(commit=False)
            tema.created_by = request.user
            tema.save()
            messages.success(request, f'Tema "{tema.name}" criado com sucesso.')
            return redirect('dimms:temas_lista')

    return render(request, 'dimms/acompanhamentos/subjects.html', {
        'subjects': subjects,
        'form': form,
        'pode_editar': request.user.has_perm('dimms.change_subject'),
        'pode_excluir': request.user.has_perm('dimms.delete_subject'),
    })


''' Editar tema '''
@login_required
@permission_required('dimms.change_subject', raise_exception=True)
def tema_edit(request, pk):
    tema = get_object_or_404(Subject, pk=pk)

    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=tema)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tema atualizado com sucesso.')
            return redirect('dimms:temas_lista')
    else:
        form = SubjectForm(instance=tema)

    return render(request, 'dimms/acompanhamentos/subject_form.html', {
        'form': form,
        'tema': tema,
    })


''' Excluir tema (só se não tiver SEIs vinculados) '''
@login_required
@permission_required('dimms.delete_subject', raise_exception=True)
@require_POST
def tema_delete(request, pk):
    tema = get_object_or_404(Subject, pk=pk)

    if tema.seis.exists():
        messages.error(request, 'Não é possível excluir: existem acompanhamentos vinculados a este tema.')
        return redirect('dimms:temas_lista')

    nome = tema.name
    tema.delete()
    messages.success(request, f'Tema "{nome}" removido.')
    return redirect('dimms:temas_lista')
