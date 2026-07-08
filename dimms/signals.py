from django.db.models.signals import pre_delete
from django.dispatch import receiver


@receiver(pre_delete, sender='dimms.ItensSolicitados')
def restaurar_saldo_ao_remover_item(sender, instance, **kwargs):
    """Quando um item é removido da solicitação, devolve a quantidade ao saldo ativo."""
    bem = instance.bem
    if bem and instance.quantidade:
        bem.saldo_disponivel = (bem.saldo_disponivel or 0) + instance.quantidade
        bem.save(update_fields=['saldo_disponivel'])
