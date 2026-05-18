"""
Management command: init_superuser

Creates the initial superuser from environment variables (idempotent).
Safe to run on every deploy — skips silently if the user already exists.

Required env var:
  DJANGO_SUPERUSER_PASSWORD

Optional env vars (with defaults):
  DJANGO_SUPERUSER_USERNAME  (default: admin)
  DJANGO_SUPERUSER_EMAIL     (default: admin@sipat.mppe.mp.br)

Usage:
  python manage.py init_superuser
"""

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create the initial superuser from environment variables (idempotent)."

    def handle(self, *args, **options):
        User = get_user_model()

        username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin").strip()
        email    = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@sipat.mppe.mp.br").strip()
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "").strip()

        if not password:
            raise CommandError(
                "A variável de ambiente DJANGO_SUPERUSER_PASSWORD é obrigatória."
            )

        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f"Superusuário '{username}' já existe — nenhuma ação realizada.")
            )
            return

        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(
            self.style.SUCCESS(f"Superusuário '{username}' criado com sucesso.")
        )
