import json

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q

from demands.models import Demand, DemandType, DemandAttachment, DemandUpdate, DemandAssignment, Priority, Status
from dempam.models import InfoUA


def _managed_ua_ids(user):
    """IDs das UAs que o usuário gerencia."""
    if user.is_staff or user.is_superuser:
        return InfoUA.objects.values_list('id', flat=True)
    return user.profile.managed_uas.values_list('id', flat=True)


def _can_view_demand(user, demand):
    if user.is_staff or user.is_superuser:
        return True
    if demand.assigned_to.filter(pk=user.pk).exists():
        return True
    if demand.created_by == user:
        return True
    if demand.ua_id and demand.ua_id in list(_managed_ua_ids(user)):
        return True
    return False


def _can_manage_demand(user, demand):
    """Pode mudar status, atribuições etc."""
    if user.is_staff or user.is_superuser:
        return True
    if demand.ua_id and demand.ua_id in list(_managed_ua_ids(user)):
        return True
    # Atribuído com permissão de alterar status
    return demand.assignments.filter(user=user, can_change_status=True).exists()


@login_required
def homepage(request):
    user = request.user

    if user.is_staff or user.is_superuser:
        demands = Demand.objects.select_related('demand_type', 'created_by', 'ua').prefetch_related('assigned_to')
    else:
        managed_ids = list(_managed_ua_ids(user))
        demands = Demand.objects.filter(
            Q(assigned_to=user) | Q(created_by=user) | Q(ua__in=managed_ids)
        ).distinct().select_related('demand_type', 'created_by', 'ua').prefetch_related('assigned_to')

    # Filtros
    status_filter   = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    type_filter     = request.GET.get('type', '')
    ua_filter       = request.GET.get('ua', '')
    mine_filter     = request.GET.get('mine', '')

    if status_filter:
        demands = demands.filter(status=status_filter)
    if priority_filter:
        demands = demands.filter(priority=priority_filter)
    if type_filter:
        demands = demands.filter(demand_type__id=type_filter)
    if ua_filter:
        demands = demands.filter(ua__id=ua_filter)
    if mine_filter:
        demands = demands.filter(assigned_to=user)

    demands = list(demands)

    total             = len(demands)
    open_count        = sum(1 for d in demands if d.status == Status.open)
    in_progress_count = sum(1 for d in demands if d.status == Status.in_progress)
    overdue_count     = sum(1 for d in demands if d.is_overdue)

    # UAs visíveis ao usuário (para filtro)
    if user.is_staff or user.is_superuser:
        visible_uas = InfoUA.objects.all()
    else:
        managed_ids = list(_managed_ua_ids(user))
        visible_uas = InfoUA.objects.filter(id__in=managed_ids)

    can_create = user.is_staff or user.is_superuser or user.profile.managed_uas.exists()

    return render(request, 'demands_list.html', {
        'demands':            demands,
        'demand_types':       DemandType.objects.filter(is_active=True),
        'visible_uas':        visible_uas,
        'status_filter':      status_filter,
        'priority_filter':    priority_filter,
        'type_filter':        type_filter,
        'ua_filter':          ua_filter,
        'mine_filter':        mine_filter,
        'priority_choices':   Priority.choices,
        'status_choices':     Status.choices,
        'total':              total,
        'open_count':         open_count,
        'in_progress_count':  in_progress_count,
        'overdue_count':      overdue_count,
        'can_create':         can_create,
    })


@login_required
def demand_create(request):
    user = request.user

    if user.is_staff or user.is_superuser:
        managed_uas = InfoUA.objects.all()
    else:
        managed_uas = user.profile.managed_uas.all()

    if not managed_uas.exists():
        messages.error(request, 'Você não tem permissão para criar demandas.')
        return redirect('demands:homepage')

    available_types = DemandType.objects.filter(is_active=True)

    # Monta dict {ua_id: [{id, name}, ...]} para o JS filtrar os assignees
    users_by_ua = {}
    for ua in managed_uas:
        members = ua.members.filter(user__is_active=True).select_related('user')
        users_by_ua[ua.pk] = [
            {'id': p.user.pk, 'name': p.user.get_full_name() or p.user.username}
            for p in members.order_by('user__first_name', 'user__username')
        ]

    if request.method == 'POST':
        ua_id        = request.POST.get('ua')
        type_id      = request.POST.get('demand_type')
        title        = request.POST.get('title', '').strip()
        description  = request.POST.get('description', '').strip()
        priority     = request.POST.get('priority', Priority.medium)
        deadline     = request.POST.get('deadline') or None
        assigned_ids      = request.POST.getlist('assigned_to')
        can_status_ids    = request.POST.getlist('can_change_status')
        files             = request.FILES.getlist('attachments')

        errors = []
        ua = demand_type = None

        if not ua_id:
            errors.append('Selecione a UA responsável.')
        else:
            ua = InfoUA.objects.filter(pk=ua_id).first()
            if not ua:
                errors.append('UA inválida.')
            elif not (user.is_staff or user.is_superuser):
                if not user.profile.managed_uas.filter(pk=ua.pk).exists():
                    errors.append('Você não gerencia essa UA.')

        if not type_id:
            errors.append('Selecione um tipo de demanda.')
        else:
            demand_type = DemandType.objects.filter(pk=type_id, is_active=True).first()
            if not demand_type:
                errors.append('Tipo de demanda inválido.')

        if not title:
            errors.append('O título é obrigatório.')
        if not description:
            errors.append('A descrição é obrigatória.')

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            demand = Demand.objects.create(
                ua=ua,
                demand_type=demand_type,
                title=title,
                description=description,
                priority=priority,
                deadline=deadline,
                created_by=user,
            )
            for uid in assigned_ids:
                DemandAssignment.objects.create(
                    demand=demand,
                    user_id=uid,
                    can_change_status=(uid in can_status_ids),
                )

            for f in files:
                DemandAttachment.objects.create(demand=demand, file=f, uploaded_by=user)

            messages.success(request, f'Demanda {demand.code} criada com sucesso.')
            return redirect('demands:detail', pk=demand.pk)

    return render(request, 'demands_create.html', {
        'managed_uas':      managed_uas,
        'available_types':  available_types,
        'priority_choices': Priority.choices,
        'users_by_ua_json': json.dumps(users_by_ua),
        'form_data':        request.POST if request.method == 'POST' else {},
    })


@login_required
def demand_detail(request, pk):
    demand = get_object_or_404(
        Demand.objects.select_related('demand_type', 'created_by', 'ua')
                      .prefetch_related(
                          'assigned_to__profile',
                          'attachments',
                          'updates__author__profile',
                      ),
        pk=pk
    )
    user = request.user

    if not _can_view_demand(user, demand):
        raise PermissionDenied

    can_manage = _can_manage_demand(user, demand)

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

    return render(request, 'demands_detail.html', {
        'demand':         demand,
        'updates':        demand.updates.all(),
        'attachments':    demand.attachments.select_related('uploaded_by').all(),
        'assignments':    demand.assignments.select_related('user__profile').all(),
        'status_choices': Status.choices,
        'can_manage':     can_manage,
        'Status':         Status,
    })
