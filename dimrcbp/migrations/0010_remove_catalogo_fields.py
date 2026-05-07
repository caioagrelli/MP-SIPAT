from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dimrcbp', '0009_catalogo'),
    ]

    operations = [
        migrations.RemoveField(model_name='catalogo', name='mark'),
        migrations.RemoveField(model_name='catalogo', name='model'),
        migrations.RemoveField(model_name='catalogo', name='observacoes'),
    ]
