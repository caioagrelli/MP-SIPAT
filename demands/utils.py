from django.db import transaction, IntegrityError
from django.utils import timezone


# Gera o próximo código sequencial do ano (ex.: DEM-2026-0001) pra um campo único de um model.
# Baseado no MAIOR número já usado no ano — não em count() — pra não colidir quando algum
# código no meio da sequência foi apagado (deixando "buracos" que fariam count()+1 repetir
# um número que já existe).
def gerar_proximo_codigo(model, campo, prefixo, digitos=4):
    ano = timezone.now().year
    prefixo_ano = f'{prefixo}-{ano}-'
    ultimo_codigo = (
        model.objects
        .filter(**{f'{campo}__startswith': prefixo_ano})
        .order_by(f'-{campo}')
        .values_list(campo, flat=True)
        .first()
    )
    ultimo_numero = int(ultimo_codigo.rsplit('-', 1)[-1]) if ultimo_codigo else 0
    return f'{prefixo_ano}{ultimo_numero + 1:0{digitos}d}'


# Gera o código (via gerar_proximo_codigo) e chama save_callable dentro de uma transação,
# tentando de novo com o próximo número se colidir por causa de uma corrida entre requisições
# simultâneas. Só engole o IntegrityError se ele for mesmo sobre esse campo — qualquer outro
# erro (ex.: FK obrigatória faltando) sobe na hora, sem mascarar a causa real.
def salvar_com_codigo_sequencial(instance, campo, prefixo, save_callable, *args, digitos=4, tentativas=5, **kwargs):
    model = type(instance)
    for _ in range(tentativas):
        setattr(instance, campo, gerar_proximo_codigo(model, campo, prefixo, digitos))
        try:
            with transaction.atomic():
                save_callable(*args, **kwargs)
            return
        except IntegrityError as e:
            if campo not in str(e):
                raise
            setattr(instance, campo, '')
    raise IntegrityError(f'Não foi possível gerar um código único ({prefixo}) após {tentativas} tentativas.')
