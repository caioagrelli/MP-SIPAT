import secrets
import string

from django.conf import settings
from django.core.mail import send_mail

_SYMBOLS = '!@#$%'
_PASSWORD_CHARS = string.ascii_uppercase + string.ascii_lowercase + string.digits + _SYMBOLS
_PASSWORD_LENGTH = 12
_SIPAT_URL = getattr(settings, 'SIPAT_URL', 'http://sipat.local')


def generate_temp_password() -> str:
    required = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
        secrets.choice(_SYMBOLS),
    ]
    rest = [secrets.choice(_PASSWORD_CHARS) for _ in range(_PASSWORD_LENGTH - len(required))]
    pool = required + rest
    secrets.SystemRandom().shuffle(pool)
    return ''.join(pool)


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
