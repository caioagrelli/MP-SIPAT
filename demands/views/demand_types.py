from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied

from demands.models import DemandType


def _has_type_permission(user):
    return (
        user.is_superuser
        or user.has_perm('demands.add_demandtype')
        or user.has_perm('demands.change_demandtype')
        or user.has_perm('demands.delete_demandtype')
    )

def _require_manager(user):
    if not _has_type_permission(user):
        raise PermissionDenied


@login_required
def demand_types_list(request):
    _require_manager(request.user)
    types = DemandType.objects.order_by('name')
    return render(request, 'demands_types.html', {'types': types})


@login_required
def demand_type_create(request):
    _require_manager(request.user)

    if request.method == 'POST':
        name        = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        color       = request.POST.get('color', '#1d4ed8').strip()
        icon        = request.POST.get('icon', '📋').strip()
        is_active   = 'is_active' in request.POST

        errors = []
        if not name:
            errors.append('O nome é obrigatório.')
        elif DemandType.objects.filter(name=name).exists():
            errors.append(f'Já existe um tipo com o nome "{name}".')

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            DemandType.objects.create(
                name=name,
                description=description,
                color=color,
                icon=icon,
                is_active=is_active,
            )
            messages.success(request, f'Tipo "{name}" criado com sucesso.')
            return redirect('demands:types_list')

    return render(request, 'demands_type_form.html', {
        'dt': None,
        'form_data': request.POST if request.method == 'POST' else {},
        'action': 'Criar',
    })


@login_required
def demand_type_edit(request, pk):
    _require_manager(request.user)
    dt = get_object_or_404(DemandType, pk=pk)

    if request.method == 'POST':
        name        = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        color       = request.POST.get('color', '#1d4ed8').strip()
        icon        = request.POST.get('icon', '📋').strip()
        is_active   = 'is_active' in request.POST

        errors = []
        if not name:
            errors.append('O nome é obrigatório.')
        elif DemandType.objects.filter(name=name).exclude(pk=pk).exists():
            errors.append(f'Já existe um tipo com o nome "{name}".')

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            dt.name        = name
            dt.description = description
            dt.color       = color
            dt.icon        = icon
            dt.is_active   = is_active
            dt.save()
            messages.success(request, f'Tipo "{name}" atualizado com sucesso.')
            return redirect('demands:types_list')

    return render(request, 'demands_type_form.html', {
        'dt': dt,
        'form_data': {},
        'action': 'Editar',
    })


@login_required
def demand_type_toggle(request, pk):
    """Ativa/desativa via POST simples."""
    _require_manager(request.user)
    dt = get_object_or_404(DemandType, pk=pk)
    if request.method == 'POST':
        dt.is_active = not dt.is_active
        dt.save(update_fields=['is_active'])
        estado = 'ativado' if dt.is_active else 'desativado'
        messages.success(request, f'Tipo "{dt.name}" {estado}.')
    return redirect('demands:types_list')
