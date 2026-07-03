"""
Management command: importar_usuarios_xlsx

Importa usuários a partir da planilha de respostas do formulário de login do SIPAT.

Colunas esperadas (0-indexed):
  0 = timestamp
  1 = email do formulário
  2 = nome completo
  3 = email MPPE (preferido)
  4 = telefone
  5 = divisão
  6 = ocupação
  7 = login (username)

Uso:
  python manage.py importar_usuarios_xlsx
  python manage.py importar_usuarios_xlsx --arquivo docs/outro.xlsx
  python manage.py importar_usuarios_xlsx --dry-run
  python manage.py importar_usuarios_xlsx --sobrescrever
"""

import os
import secrets
import string

import openpyxl

from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.core.management.base import BaseCommand

from accounts.models import Profile


_SYMBOLS = '!@#$%'
_PASSWORD_CHARS = string.ascii_uppercase + string.ascii_lowercase + string.digits + _SYMBOLS
_PASSWORD_LENGTH = 12

_DEFAULT_ARQUIVO = 'docs/Formulário de login SIPAT (respostas).xlsx'
_SIPAT_URL = os.environ.get('SIPAT_URL', 'http://sipat.mppe.mp.br')


def _generate_password() -> str:
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


def _cell_str(cell) -> str:
    return str(cell if cell is not None else '').strip()


def _parse_name(nome: str):
    parts = nome.split()
    if len(parts) == 1:
        return parts[0], ''
    return ' '.join(parts[:-1]), parts[-1]


def _send_welcome_email(email: str, first_name: str, username: str, password: str, dry_run: bool) -> None:
    subject = 'Seu acesso ao SIPAT'
    body = (
        f'Olá, {first_name}!\n\n'
        f'Seu acesso ao SIPAT foi criado. Utilize as credenciais abaixo para entrar no sistema:\n\n'
        f'  Login : {username}\n'
        f'  Senha : {password}\n\n'
        f'Acesse o sistema em: {_SIPAT_URL}\n\n'
        f'Por segurança, você será solicitado(a) a definir uma nova senha no seu primeiro acesso.\n\n'
        f'Em caso de dúvidas, entre em contato com a equipe de TI.\n\n'
        f'Atenciosamente,\n'
        f'Equipe SIPAT — MPPE\n'
    )
    if not dry_run:
        send_mail(
            subject=subject,
            message=body,
            from_email=None,  # usa DEFAULT_FROM_EMAIL
            recipient_list=[email],
            fail_silently=False,
        )


class Command(BaseCommand):
    help = 'Importa usuários a partir da planilha de formulário de login do SIPAT.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--arquivo',
            default=_DEFAULT_ARQUIVO,
            help=f'Caminho para o arquivo .xlsx (padrão: {_DEFAULT_ARQUIVO})',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=False,
            help='Simula a importação sem criar usuários nem enviar e-mails.',
        )
        parser.add_argument(
            '--sobrescrever',
            action='store_true',
            default=False,
            help='Atualiza dados de usuários já existentes.',
        )

    def handle(self, *args, **options):
        arquivo    = options['arquivo']
        dry_run    = options['dry_run']
        sobrescrever = options['sobrescrever']

        User = get_user_model()

        if not os.path.exists(arquivo):
            self.stderr.write(self.style.ERROR(f'Arquivo não encontrado: {arquivo}'))
            return

        wb = openpyxl.load_workbook(arquivo, data_only=True)
        ws = wb.active

        criados    = 0
        atualizados = 0
        ignorados  = 0
        erros      = 0

        rows = list(ws.iter_rows(values_only=True))
        # Pula a primeira linha (cabeçalho)
        data_rows = rows[1:]

        if dry_run:
            self.stdout.write(self.style.WARNING('[DRY-RUN] Nenhuma alteração será salva.\n'))

        for i, row in enumerate(data_rows, start=2):
            # Proteção contra linhas completamente vazias
            if not any(row):
                continue

            try:
                # Leitura das colunas
                email_form  = _cell_str(row[1] if len(row) > 1 else '')
                nome        = _cell_str(row[2] if len(row) > 2 else '')
                email_mppe  = _cell_str(row[3] if len(row) > 3 else '')
                phone_raw   = row[4] if len(row) > 4 else None
                username    = _cell_str(row[7] if len(row) > 7 else '')

                if not username:
                    self.stdout.write(self.style.WARNING(f'  Linha {i}: username vazio — ignorada.'))
                    ignorados += 1
                    continue

                email = email_mppe or email_form

                # Trata o telefone: pode vir como float do Excel (ex.: 81999998888.0)
                if phone_raw is not None and str(phone_raw).strip():
                    try:
                        phone = str(int(float(str(phone_raw).strip())))
                    except (ValueError, TypeError):
                        phone = _cell_str(phone_raw)
                else:
                    phone = ''

                first_name, last_name = _parse_name(nome)

                # Verifica se o usuário já existe
                existing = User.objects.filter(username=username).first()

                if existing and not sobrescrever:
                    self.stdout.write(f'  Linha {i}: usuário "{username}" já existe — ignorado.')
                    ignorados += 1
                    continue

                password = _generate_password()

                if existing and sobrescrever:
                    # Atualiza dados do usuário
                    if not dry_run:
                        existing.first_name = first_name
                        existing.last_name  = last_name
                        existing.email      = email
                        existing.set_password(password)
                        existing.save()

                        profile, _ = Profile.objects.get_or_create(user=existing)
                        profile.phone = phone
                        profile.must_change_password = True
                        profile.save(update_fields=['phone', 'must_change_password'])

                        _send_welcome_email(email, first_name, username, password, dry_run)

                    self.stdout.write(
                        self.style.SUCCESS(f'  Linha {i}: usuário "{username}" atualizado{"  [dry-run]" if dry_run else ""}.')
                    )
                    atualizados += 1

                else:
                    # Cria novo usuário
                    if not dry_run:
                        user = User.objects.create_user(
                            username=username,
                            email=email,
                            password=password,
                            first_name=first_name,
                            last_name=last_name,
                        )

                        profile, _ = Profile.objects.get_or_create(user=user)
                        profile.phone = phone
                        profile.must_change_password = True
                        profile.save(update_fields=['phone', 'must_change_password'])

                        _send_welcome_email(email, first_name, username, password, dry_run)

                    self.stdout.write(
                        self.style.SUCCESS(f'  Linha {i}: usuário "{username}" criado{"  [dry-run]" if dry_run else ""}.')
                    )
                    criados += 1

            except Exception as exc:
                self.stderr.write(self.style.ERROR(f'  Linha {i}: erro — {exc}'))
                erros += 1

        # Resumo
        self.stdout.write('\n' + '-' * 48)
        self.stdout.write(self.style.SUCCESS(f'  Criados    : {criados}'))
        if sobrescrever:
            self.stdout.write(self.style.SUCCESS(f'  Atualizados: {atualizados}'))
        self.stdout.write(self.style.WARNING(f'  Ignorados  : {ignorados}'))
        if erros:
            self.stdout.write(self.style.ERROR(f'  Erros      : {erros}'))
        self.stdout.write('-' * 48)
        if dry_run:
            self.stdout.write(self.style.WARNING('[DRY-RUN] Nenhuma alteração foi salva.'))
