"""
Management command: init_superuser

Cria o superusuário inicial de forma idempotente.
Seguro para rodar em todo deploy — não faz nada se o usuário já existir.

Sem nenhuma configuração necessária: se a senha não for fornecida via env var,
uma senha segura é gerada automaticamente e exibida uma única vez no output.

Env vars opcionais:
  DJANGO_SUPERUSER_USERNAME  (padrão: admin)
  DJANGO_SUPERUSER_EMAIL     (padrão: admin@sipat.mppe.mp.br)
  DJANGO_SUPERUSER_PASSWORD  (padrão: gerado automaticamente)

Uso:
  python manage.py init_superuser
"""

import os
import secrets
import string

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


_PASSWORD_CHARS = string.ascii_letters + string.digits + "!@#%&*"
_PASSWORD_LENGTH = 18


def _generate_password() -> str:
    # Garante ao menos 1 maiúscula, 1 minúscula, 1 dígito e 1 símbolo
    required = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
        secrets.choice("!@#%&*"),
    ]
    rest = [secrets.choice(_PASSWORD_CHARS) for _ in range(_PASSWORD_LENGTH - len(required))]
    pool = required + rest
    secrets.SystemRandom().shuffle(pool)
    return "".join(pool)


class Command(BaseCommand):
    help = "Cria o superusuário inicial (idempotente). Gera senha automaticamente se não configurada."

    def handle(self, *args, **options):
        User = get_user_model()

        username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin").strip()
        email    = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@sipat.mppe.mp.br").strip()
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "").strip()

        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f"Superusuário '{username}' já existe — nenhuma ação realizada.")
            )
            return

        auto_generated = not password
        if auto_generated:
            password = _generate_password()

        User.objects.create_superuser(username=username, email=email, password=password)

        self.stdout.write(self.style.SUCCESS(f"Superusuário '{username}' criado."))

        if auto_generated:
            border = "═" * 52
            self.stdout.write(self.style.WARNING(
                f"\n  ╔{border}╗\n"
                f"  ║  CREDENCIAIS GERADAS AUTOMATICAMENTE{' ' * 14}║\n"
                f"  ╠{border}╣\n"
                f"  ║  Usuário : {username:<40}║\n"
                f"  ║  Senha   : {password:<40}║\n"
                f"  ╠{border}╣\n"
                f"  ║  Acesse /login/ e troque a senha após o 1º login.  ║\n"
                f"  ║  Esta mensagem não será exibida novamente.          ║\n"
                f"  ╚{border}╝\n"
            ))
