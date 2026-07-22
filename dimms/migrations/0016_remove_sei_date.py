# Placeholder sem operações — existiu uma tentativa anterior de numerar essa migration como
# 0016, mas a remoção real do campo 'date' já é feita em 0015_remove_sei_date. Mantido vazio
# só pra não deixar um arquivo órfão no histórico.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dimms', '0015_remove_sei_date'),
    ]

    operations = []
