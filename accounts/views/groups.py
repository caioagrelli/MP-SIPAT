from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count

from accounts.views import management_required

# Apps do projeto que terão permissões gerenciadas
PROJECT_APPS = ['dimms', 'dimrcbp', 'dempam', 'accounts', 'demands']

APP_DISPLAY_NAMES = {
    'dimms':    'DIMMS — Bens de Consumo',
    'dimrcbp':  'DIMRCBP — Bens Permanentes',
    'dempam':   'DEMPAM',
    'accounts': 'Controle de Acesso',
    'demands':  'Demandas',
}

ACTIONS = ['view', 'add', 'change', 'delete']

ACTION_LABELS = {
    'view':   'Ver',
    'add':    'Adicionar',
    'change': 'Editar',
    'delete': 'Deletar',
}


@management_required
def groups_list(request):
    groups = Group.objects.annotate(user_count=Count('user')).order_by('name')

    return render(request, 'access/groups.html', {
        'groups': groups,
        'total_groups': groups.count(),
    })


@management_required
def group_create(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()

        if not name:
            messages.error(request, 'O nome do grupo não pode ser vazio.')
        elif Group.objects.filter(name=name).exists():
            messages.error(request, f'Já existe um grupo com o nome "{name}".')
        else:
            Group.objects.create(name=name)
            messages.success(request, f'Grupo "{name}" criado com sucesso.')
            return redirect('accounts:groups_list')

    return render(request, 'access/group_form.html', {
        'action': 'Criar',
        'group': None,
    })


@management_required
def group_edit(request, pk):
    group = get_object_or_404(Group, pk=pk)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()

        if not name:
            messages.error(request, 'O nome do grupo não pode ser vazio.')
        elif Group.objects.filter(name=name).exclude(pk=pk).exists():
            messages.error(request, f'Já existe um grupo com o nome "{name}".')
        else:
            group.name = name
            group.save()
            messages.success(request, f'Grupo renomeado para "{name}".')
            return redirect('accounts:groups_list')

    return render(request, 'access/group_form.html', {
        'action': 'Editar',
        'group': group,
    })


@management_required
def group_delete(request, pk):
    group = get_object_or_404(Group, pk=pk)

    if request.method == 'POST':
        name = group.name
        group.delete()
        messages.success(request, f'Grupo "{name}" removido.')

    return redirect('accounts:groups_list')


@management_required
def group_permissions(request, pk):
    group = get_object_or_404(Group, pk=pk)

    # IDs das permissões que o grupo já tem
    group_perm_ids = set(group.permissions.values_list('id', flat=True))

    # Monta estrutura: { app_label: { display_name, models: [ { verbose_name, perms: {action: Permission|None} } ] } }
    content_types = (
        ContentType.objects
        .filter(app_label__in=PROJECT_APPS)
        .order_by('app_label', 'model')
    )

    apps_data = {}
    for ct in content_types:
        model_class = ct.model_class()
        if model_class is None:
            continue

        verbose_name = model_class._meta.verbose_name.title()

        # Busca as 4 permissões padrão do model
        perms_by_action = {}
        for action in ACTIONS:
            perms_by_action[action] = Permission.objects.filter(
                content_type=ct,
                codename=f'{action}_{ct.model}'
            ).first()

        # Ignora models que não têm nenhuma permissão criada ainda
        if not any(perms_by_action.values()):
            continue

        if ct.app_label not in apps_data:
            apps_data[ct.app_label] = {
                'display_name': APP_DISPLAY_NAMES.get(ct.app_label, ct.app_label.upper()),
                'models': [],
            }

        apps_data[ct.app_label]['models'].append({
            'verbose_name': verbose_name,
            'perms': perms_by_action,
        })

    if request.method == 'POST':
        selected_ids = request.POST.getlist('permissions')
        group.permissions.set(Permission.objects.filter(id__in=selected_ids))
        messages.success(request, f'Permissões do grupo "{group.name}" atualizadas com sucesso.')
        return redirect('accounts:groups_list')

    return render(request, 'access/group_permissions.html', {
        'group': group,
        'apps_data': apps_data,
        'group_perm_ids': group_perm_ids,
        'actions': ACTIONS,
        'action_labels': ACTION_LABELS,
    })
