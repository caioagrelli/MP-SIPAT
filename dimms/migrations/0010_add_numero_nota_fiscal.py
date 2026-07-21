from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dimms', '0009_merge_0008'),
    ]

    operations = [
        migrations.AddField(
            model_name='solicitacoessaldoativo',
            name='numero_nota_fiscal',
            field=models.CharField(blank=True, max_length=60, verbose_name='N° Nota Fiscal'),
        ),
    ]
