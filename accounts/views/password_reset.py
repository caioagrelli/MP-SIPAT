from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages

from accounts.models import Profile
from accounts.utils import generate_temp_password, send_password_reset_email


def password_reset_request(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        user = User.objects.filter(username=username, is_active=True).first()

        if user and user.email:
            temp_password = generate_temp_password()
            user.set_password(temp_password)
            user.save(update_fields=['password'])

            profile, _ = Profile.objects.get_or_create(user=user)
            profile.must_change_password = True
            profile.save(update_fields=['must_change_password'])

            send_password_reset_email(user, temp_password)

        elif user and not user.email:
            messages.warning(
                request,
                'Não foi possível enviar a senha temporária: não há e-mail cadastrado '
                'para esse usuário. Entre em contato com o DEMPAM para redefinir sua senha.'
            )

        # Se o usuário não existir, nenhuma mensagem específica é adicionada —
        # a tela de confirmação segue com o texto genérico, pra não confirmar
        # pra quem pede se aquele nome de usuário existe no sistema.
        return redirect('password_reset_done')

    return render(request, 'registration/password_reset.html')


def password_reset_done(request):
    return render(request, 'registration/password_reset_done.html')
