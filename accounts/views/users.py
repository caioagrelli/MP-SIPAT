from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.db.models import Q, Count
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from accounts.views import management_required
from accounts.models import Profile


@management_required
def users_list(request):
    query = request.GET.get('q', '').strip()
    group_filter = request.GET.get('group', '')

    users = User.objects.prefetch_related('groups').order_by('username')

    if query:
        users = users.filter(
            Q(username__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
        )

    if group_filter:
        users = users.filter(groups__id=group_filter)

    groups = Group.objects.annotate(user_count=Count('user')).order_by('name')

    # Garante que todos os usuários têm perfil (cobre usuários criados antes do signal)
    users_without_profile = users.filter(profile__isnull=True)
    for u in users_without_profile:
        Profile.objects.get_or_create(user=u)

    # Recarrega com profile junto para evitar N+1 queries
    users = users.select_related('profile')

    # Contagens para o summary strip
    total_users = User.objects.count()
    users_with_groups = User.objects.filter(groups__isnull=False).distinct().count()
    users_without_groups = total_users - users_with_groups

    return render(request, 'access/users.html', {
        'users': users,
        'groups': groups,
        'query': query,
        'group_filter': group_filter,
        'total_users': total_users,
        'users_with_groups': users_with_groups,
        'users_without_groups': users_without_groups,
        'total_groups': groups.count(),
    })


@management_required
def user_edit(request, pk):
    edited_user = get_object_or_404(User, pk=pk)
    profile, _  = Profile.objects.get_or_create(user=edited_user)
    all_groups  = Group.objects.order_by('name')

    if request.method == 'POST':
        # Dados pessoais
        edited_user.first_name = request.POST.get('first_name', '').strip()
        edited_user.last_name  = request.POST.get('last_name', '').strip()
        edited_user.email      = request.POST.get('email', '').strip()
        edited_user.is_active  = 'is_active' in request.POST
        edited_user.save(update_fields=['first_name', 'last_name', 'email', 'is_active'])

        # Grupos
        selected_ids = request.POST.getlist('groups')
        edited_user.groups.set(Group.objects.filter(id__in=selected_ids))

        # Foto — remove se solicitado, troca se enviada
        if request.POST.get('remove_photo') == '1' and profile.photo:
            profile.photo.delete(save=False)
            profile.photo = None
        elif 'photo' in request.FILES:
            if profile.photo:
                profile.photo.delete(save=False)
            profile.photo = request.FILES['photo']

        profile.phone = request.POST.get('phone', '').strip()
        profile.save()

        messages.success(request, f'Usuário "{edited_user.username}" atualizado com sucesso.')
        return redirect('accounts:users_list')

    user_group_ids = set(edited_user.groups.values_list('id', flat=True))

    return render(request, 'access/user_edit.html', {
        'edited_user': edited_user,
        'profile': profile,
        'all_groups': all_groups,
        'user_group_ids': user_group_ids,
    })


@management_required
def user_create(request):
    all_groups = Group.objects.order_by('name')

    if request.method == 'POST':
        username   = request.POST.get('username', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name', '').strip()
        email      = request.POST.get('email', '').strip()
        password1  = request.POST.get('password1', '')
        password2  = request.POST.get('password2', '')
        is_active  = 'is_active' in request.POST
        group_ids  = request.POST.getlist('groups')

        # Validações
        errors = []

        if not username:
            errors.append('O nome de usuário é obrigatório.')
        elif User.objects.filter(username=username).exists():
            errors.append(f'O usuário "{username}" já existe.')

        if not password1:
            errors.append('A senha é obrigatória.')
        elif password1 != password2:
            errors.append('As senhas não coincidem.')
        else:
            try:
                validate_password(password1)
            except ValidationError as e:
                errors.extend(e.messages)

        if errors:
            for error in errors:
                messages.error(request, error)
            # Devolve o formulário com os dados preenchidos
            return render(request, 'access/user_create.html', {
                'all_groups': all_groups,
                'form_data': request.POST,
            })

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name,
            is_active=is_active,
        )
        user.groups.set(Group.objects.filter(id__in=group_ids))

        messages.success(request, f'Usuário "{username}" criado com sucesso.')
        return redirect('accounts:users_list')

    return render(request, 'access/user_create.html', {
        'all_groups': all_groups,
        'form_data': {},
    })
