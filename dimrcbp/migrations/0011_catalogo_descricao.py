from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dimrcbp', '0010_remove_catalogo_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='catalogo',
            name='descricao',
            field=models.TextField(blank=True, verbose_name='Descrição Livre'),
        ),
    ]
