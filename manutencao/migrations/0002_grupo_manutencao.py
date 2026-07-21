from django.apps import apps as global_apps
from django.contrib.auth.management import create_permissions
from django.db import migrations


def create_group(apps, schema_editor):
    # As permissões padrão só são criadas pelo sinal post_migrate, que dispara
    # ao final do comando `migrate` — como esta migração roda antes disso,
    # criamos a permissão explicitamente aqui.
    create_permissions(global_apps.get_app_config('manutencao'), apps=global_apps, verbosity=0)

    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    ct = ContentType.objects.get(app_label='manutencao', model='manutencaoacesso')
    perm, _ = Permission.objects.get_or_create(
        codename='access_manutencao',
        content_type=ct,
        defaults={'name': 'Pode acessar o módulo de Manutenção'},
    )
    group, _ = Group.objects.get_or_create(name='Manutenção')
    group.permissions.add(perm)


def remove_group(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name='Manutenção').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('manutencao', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_group, remove_group),
    ]
