from django.contrib.auth.models import User, Permission

from dempam.models import InfoUA, CircunscricaoPredio
from dimms.models import CatalogoConsumo, SolicitacaoCatalogoConsumo


def make_user(username='usuario', password='senha123', perms=None):
    u = User.objects.create_user(username=username, password=password)
    if perms:
        for codename in perms:
            u.user_permissions.add(Permission.objects.get(codename=codename))
    return u


def make_ua(nome='UA Teste'):
    predio = CircunscricaoPredio.objects.create(local='Prédio Teste')
    return InfoUA.objects.create(ua=nome, circunscricao_predio=predio)


def make_catalogo(description='Papel A4', grupo='PAPEIS_EXPEDIENTE', ativo=True):
    return CatalogoConsumo.objects.create(
        description=description,
        grupo_consumo=grupo,
        medida='UNIDADE',
        ativo=ativo,
    )


def make_solicitacao(user, ua, status='PENDENTE'):
    return SolicitacaoCatalogoConsumo.objects.create(
        solicitante=user,
        ua_destino=ua,
        status=status,
    )
