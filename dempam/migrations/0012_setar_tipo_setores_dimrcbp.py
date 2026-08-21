from django.db import migrations


def marcar_setores_dimrcbp(apps, schema_editor):
    SetorDEMPAM = apps.get_model('dempam', 'SetorDEMPAM')
    SetorDEMPAM.objects.filter(setor__startswith='DIMRCBP').update(tipo='DIMRCBP')


def reverter(apps, schema_editor):
    SetorDEMPAM = apps.get_model('dempam', 'SetorDEMPAM')
    SetorDEMPAM.objects.filter(setor__startswith='DIMRCBP').update(tipo='DIMMS')


class Migration(migrations.Migration):

    dependencies = [
        ('dempam', '0011_setordempam_tipo'),
    ]

    operations = [
        migrations.RunPython(marcar_setores_dimrcbp, reverter),
    ]
