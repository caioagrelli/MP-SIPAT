from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from dempam.models import InfoUA


@receiver(pre_save, sender=InfoUA)
def _captura_gestor_anterior(sender, instance, **kwargs):
    """Guarda o gestor antigo antes de salvar para comparação no post_save."""
    if not instance.pk:
        return
    try:
        instance._gestor_anterior_id = InfoUA.objects.values_list('gestor_id', flat=True).get(pk=instance.pk)
    except InfoUA.DoesNotExist:
        instance._gestor_anterior_id = None


@receiver(post_save, sender=InfoUA)
def _ressincroniza_bens_ao_mudar_gestor(sender, instance, created, **kwargs):
    """Quando o gestor da UA muda, ressincroniza AtribuicaoBem de todos os bens nessa UA."""
    if created:
        return

    anterior = getattr(instance, '_gestor_anterior_id', None)
    if anterior == instance.gestor_id:
        return

    # Importação local para evitar circular import no nível de módulo
    from dimrcbp.models import HistoryUas, sincronizar_atribuicao

    bens_na_ua = (
        HistoryUas.objects
        .filter(current_ua=instance)
        .select_related('tombo')
    )
    for hist in bens_na_ua:
        sincronizar_atribuicao(hist.tombo, instance)
