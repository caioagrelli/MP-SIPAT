from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.contrib import messages
from django.core.exceptions import ValidationError

from accounts.models import Profile


@login_required
def profile_view(request):
    # Garante que o perfil existe mesmo pra usuários antigos (criados antes do signal)
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_info':
            _update_info(request, profile)

        elif action == 'change_password':
            _change_password(request)

    return render(request, 'access/profile.html', {
        'profile': profile,
    })


def _update_info(request, profile):
    user = request.user

    user.first_name = request.POST.get('first_name', '').strip()
    user.last_name  = request.POST.get('last_name', '').strip()
    user.email      = request.POST.get('email', '').strip()
    user.save(update_fields=['first_name', 'last_name', 'email'])

    profile.phone = request.POST.get('phone', '').strip()
    profile.bio   = request.POST.get('bio', '').strip()

    # Atualiza foto só se um arquivo foi enviado
    if 'photo' in request.FILES:
        # Remove a foto antiga antes de salvar a nova
        if profile.photo:
            profile.photo.delete(save=False)
        profile.photo = request.FILES['photo']

    # Remove a foto se o usuário clicou em "remover"
    elif request.POST.get('remove_photo') == '1' and profile.photo:
        profile.photo.delete(save=False)
        profile.photo = None

    profile.save()
    messages.success(request, 'Perfil atualizado com sucesso.')


def _change_password(request):
    user      = request.user
    current   = request.POST.get('current_password', '')
    new_pass  = request.POST.get('new_password1', '')
    confirm   = request.POST.get('new_password2', '')

    if not user.check_password(current):
        messages.error(request, 'Senha atual incorreta.')
        return

    if new_pass != confirm:
        messages.error(request, 'As novas senhas não coincidem.')
        return

    try:
        validate_password(new_pass, user)
    except ValidationError as e:
        for msg in e.messages:
            messages.error(request, msg)
        return

    user.set_password(new_pass)
    user.save()
    messages.success(request, 'Senha alterada com sucesso. Faça login novamente.')
