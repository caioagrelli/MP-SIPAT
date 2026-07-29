# Importações do código
from accounts.models import Profile
from .models import AtribuicaoBem, BensPermanentes

# =================================
# SERVICES DA DIMRCBP (BENS PERMANENTES)
# =================================


# Ids dos bens sob responsabilidade do usuário: atribuição individual (AtribuicaoBem)
# + bens das UAs em que ele é membro ("Membro de", Painel Gerencial)
def ids_bens_responsabilidade(user):
    ids_individuais = set(
        AtribuicaoBem.objects.filter(user=user, ativo=True).values_list('bem_id', flat=True)
    )

    profile = Profile.objects.filter(user=user).first()
    uas_membro = profile.uas.all() if profile else []

    ids_ua = set(
        BensPermanentes.objects.filter(
            history_tombo__current_ua__in=uas_membro
        ).values_list('id', flat=True)
    ) if uas_membro else set()

    return ids_individuais | ids_ua


def contar_bens_responsabilidade(user):
    return len(ids_bens_responsabilidade(user))
