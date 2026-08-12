import secrets
import string

from django.conf import settings
from django.core.mail import send_mail

_SIPAT_URL = getattr(settings, 'SIPAT_URL', 'http://sipat.local')


def generate_temp_password() -> str:
    """Gera senha no formato Sipat@NNNNX — fácil de digitar e comunicar manualmente."""
    numero = ''.join(secrets.choice(string.digits) for _ in range(4))
    sufixo = secrets.choice(string.ascii_uppercase)
    return f'Sipat@{numero}{sufixo}'


def send_welcome_email(user, password: str) -> None:
    if not user.email:
        return
    subject = 'Seu acesso ao SIPAT'
    body = (
        f'Olá, {user.first_name or user.username}!\n\n'
        f'Seu acesso ao SIPAT foi criado. Utilize as credenciais abaixo para entrar no sistema:\n\n'
        f'  Login : {user.username}\n'
        f'  Senha : {password}\n\n'
        f'Acesse o sistema em: {_SIPAT_URL}\n\n'
        f'Por segurança, você será solicitado(a) a definir uma nova senha no seu primeiro acesso.\n\n'
        f'Em caso de dúvidas, entre em contato com a equipe de TI.\n\n'
        f'Atenciosamente,\n'
        f'Equipe SIPAT — MPPE\n'
    )
    send_mail(
        subject=subject,
        message=body,
        from_email=None,
        recipient_list=[user.email],
        fail_silently=True,
    )


def send_password_reset_email(user, password: str) -> None:
    if not user.email:
        return
    subject = 'Sua senha no SIPAT foi redefinida'
    body = (
        f'Olá, {user.first_name or user.username}!\n\n'
        f'Sua senha de acesso ao SIPAT foi redefinida por um administrador. Utilize as credenciais abaixo para entrar no sistema:\n\n'
        f'  Login : {user.username}\n'
        f'  Senha : {password}\n\n'
        f'Acesse o sistema em: {_SIPAT_URL}\n\n'
        f'Por segurança, você será solicitado(a) a definir uma nova senha no seu próximo acesso.\n\n'
        f'Se você não solicitou essa alteração, entre em contato com a equipe de TI.\n\n'
        f'Atenciosamente,\n'
        f'Equipe SIPAT — MPPE\n'
    )
    send_mail(
        subject=subject,
        message=body,
        from_email=None,
        recipient_list=[user.email],
        fail_silently=True,
    )
