from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('demands', '0002_demand_ua'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # 1. Remove o M2M antigo (dropa a tabela implícita demands_demand_assigned_to)
        migrations.RemoveField(
            model_name='demand',
            name='assigned_to',
        ),

        # 2. Cria o through model
        migrations.CreateModel(
            name='DemandAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('can_change_status', models.BooleanField(default=False, verbose_name='Pode alterar status')),
                ('demand', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='assignments',
                    to='demands.demand',
                    verbose_name='Demanda',
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='demand_assignments',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Usuário',
                )),
            ],
            options={
                'verbose_name': 'Atribuição',
                'verbose_name_plural': 'Atribuições',
                'unique_together': {('demand', 'user')},
            },
        ),

        # 3. Re-adiciona o M2M apontando para o through model
        migrations.AddField(
            model_name='demand',
            name='assigned_to',
            field=models.ManyToManyField(
                blank=True,
                related_name='demands_assigned',
                through='demands.DemandAssignment',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Atribuído a',
            ),
        ),
    ]
