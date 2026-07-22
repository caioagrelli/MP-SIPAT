# Remove o campo 'date' (Data de Abertura) do model Sei — o acompanhamento passou a usar
# 'created_at' (Criado em) como referência de data em vez de um campo digitado manualmente.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dimms', '0015_alter_sei_id_alter_seiupdate_id_alter_subject_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sei',
            name='date',
        ),
    ]
