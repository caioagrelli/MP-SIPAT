from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q

from demands.models import Demand, DemandType, DemandAttachment, DemandUpdate, Priority, Status


@login_required
def demands_list(request):
    user = request.user

    # Staff e superuser veem tudo; demais veem só o que criaram ou receberam
    if user.is_staff or user.is_superuser:
        demands = Demand.objects.select_related('demand_type', 'created_by').prefetch_related('assigned_to')
    else:
        demands = Demand.objects.filter(
            Q(assigned_to=user) | Q(created_by=user)
        ).distinct().select_related('demand_type', 'created_by').prefetch_related('assigned_to')

    # Filtros
    status_filter   = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    type_filter     = request.GET.get('type', '')
    mine_filter     = request.GET.get('mine', '')

    if status_filter:
        demands = demands.filter(status=status_filter)
    if priority_filter:
        demands = demands.filter(priority=priority_filter)
    if type_filter:
        demands = demands.filter(demand_type__id=type_filter)
    if mine_filter:
        demands = demands.filter(assigned_to=user)

    demands = list(demands)

    # Contagens para o summary strip
    total            = len(demands)
    open_count       = sum(1 for d in demands if d.status == Status.open)
    in_progress_count = sum(1 for d in demands if d.status == Status.in_progress)
    overdue_count    = sum(1 for d in demands if d.is_overdue)

    # Tipos que o usuário pode criar
    user_groups = user.groups.all()
    if user.is_staff or user.is_superuser:
        creatable_types = DemandType.objects.filter(is_active=True)
    else:
        creatable_types = DemandType.objects.filter(
            allowed_groups__in=user_groups, is_active=True
        ).distinct()

    return render(request, 'demands/list.html', {
        'demands':          demands,
        'demand_types':     DemandType.objects.filter(is_active=True),
        'creatable_types':  creatable_types,
        'status_filter':    status_filter,
        'priority_filter':  priority_filter,
        'type_filter':      type_filter,
        'mine_filter':      mine_filter,
        'priority_choices': Priority.choices,
        'status_choices':   Status.choices,
        'total':            total,
        'open_count':       open_count,
        'in_progress_count': in_progress_count,
        'overdue_count':    overdue_count,
    })


@login_required
def demand_create(request):
    user        = request.user
    user_groups = user.groups.all()

    # Tipos que o usuário pode criar
    if user.is_staff or user.is_superuser:
        available_types = DemandType.objects.filter(is_active=True)
    else:
        available_types = DemandType.objects.filter(
            allowed_groups__in=user_groups, is_active=True
        ).distinct()

    if not available_types.exists():
        messages.error(request, 'Você não tem permissão para criar nenhum tipo de demanda.')
        return redirect('demands:list')

    all_users = User.objects.filter(is_active=True).order_by('first_name', 'username')

    if request.method == 'POST':
        type_id      = request.POST.get('demand_type')
        title        = request.POST.get('title', '').strip()
        description  = request.POST.get('description', '').strip()
        priority     = request.POST.get('priority', Priority.medium)
        deadline     = request.POST.get('deadline') or None
        assigned_ids = request.POST.getlist('assigned_to')
        files        = request.FILES.getlist('attachments')

        errors = []
        demand_type = None

        if not type_id:
            errors.append('Selecione um tipo de demanda.')
        else:
            demand_type = DemandType.objects.filter(pk=type_id).first()
            if not demand_type:
                errors.append('Tipo de demanda inválido.')
            elif not (user.is_staff or user.is_superuser):
                if not demand_type.allowed_groups.filter(id__in=user_groups).exists():
                    errors.append('Você não tem permissão para criar esse tipo de demanda.')

        if not title:
            errors.append('O título é obrigatório.')
        if not description:
            errors.append('A descrição é obrigatória.')

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            demand = Demand.objects.create(
                demand_type=demand_type,
                title=title,
                description=description,
                priority=priority,
                deadline=deadline,
                created_by=user,
            )
            demand.assigned_to.set(User.objects.filter(id__in=assigned_ids))

            for f in files:
                DemandAttachment.objects.create(
                    demand=demand,
                    file=f,
                    uploaded_by=user,
                )

            messages.success(request, f'Demanda {demand.code} criada com sucesso.')
            return redirect('demands:detail', pk=demand.pk)

    return render(request, 'demands/create.html', {
        'available_types':  available_types,
        'all_users':        all_users,
        'priority_choices': Priority.choices,
        'form_data':        request.POST if request.method == 'POST' else {},
    })


@login_required
def demand_detail(request, pk):
    demand = get_object_or_404(
        Demand.objects.select_related('demand_type', 'created_by')
                      .prefetch_related('assigned_to', 'attachments', 'updates__author'),
        pk=pk
    )
    user = request.user

    # Verifica acesso
    can_view = (
        user.is_staff or user.is_superuser
        or demand.created_by == user
        or demand.assigned_to.filter(pk=user.pk).exists()
    )
    if not can_view:
        raise PermissionDenied

    # Pode mudar status e atribuições
    can_manage = user.is_staff or user.is_superuser or demand.created_by == user

    if request.method == 'POST':
        comment     = request.POST.get('comment', '').strip()
        new_status  = request.POST.get('new_status', '').strip()
        update_file = request.FILES.get('update_file')

        if not comment and not new_status and not update_file:
            messages.error(request, 'Adicione um comentário ou selecione uma ação.')
            return redirect('demands:detail', pk=pk)

        update = DemandUpdate(demand=demand, author=user, comment=comment)

        if update_file:
            update.file = update_file

        if new_status and can_manage and new_status in dict(Status.choices):
            update.status_change = new_status
            demand.status = new_status
            demand.save(update_fields=['status', 'updated_at'])

        update.save()
        messages.success(request, 'Atualização registrada.')
        return redirect('demands:detail', pk=pk)

    return render(request, 'demands/detail.html', {
        'demand':         demand,
        'updates':        demand.updates.all(),
        'attachments':    demand.attachments.select_related('uploaded_by').all(),
        'status_choices': Status.choices,
        'can_manage':     can_manage,
        'Status':         Status,
    })
