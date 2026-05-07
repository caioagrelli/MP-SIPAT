from django.db import migrations, models
import django.db.models.deletion
import dimrcbp.utils


class Migration(migrations.Migration):

    dependencies = [
        ('dimrcbp', '0008_add_justificativa_historico'),
    ]

    operations = [
        migrations.CreateModel(
            name='Catalogo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('efisco', models.CharField(max_length=20, unique=True, verbose_name='Código Efisco')),
                ('mark', models.CharField(blank=True, max_length=60, verbose_name='Marca / Fabricante')),
                ('model', models.CharField(blank=True, max_length=60, verbose_name='Modelo')),
                ('photo', models.ImageField(blank=True, null=True, upload_to=dimrcbp.utils.caminho_catalogo, verbose_name='Imagem do Catálogo')),
                ('value', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='Valor Unitário de Referência')),
                ('observacoes', models.TextField(blank=True, verbose_name='Observações')),
                ('description', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='catalogo_description', to='dimrcbp.description', verbose_name='Descrição')),
            ],
            options={
                'verbose_name': 'Catálogo',
                'verbose_name_plural': '10 - Catálogos',
                'ordering': ['description__type__gruop', 'description', 'mark'],
            },
        ),
    ]
