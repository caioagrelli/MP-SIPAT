from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render


@login_required
@permission_required('manutencao.access_manutencao', raise_exception=True)
def em_construcao(request, titulo, icone='🚧'):
    return render(request, 'manutencao/em_construcao.html', {
        'titulo': titulo,
        'icone': icone,
    })


def registrar_saida(request):
    return em_construcao(request, 'Registrar Saída', '📤')


def relatorios(request):
    return em_construcao(request, 'Relatórios', '📋')


def localizacoes(request):
    return em_construcao(request, 'Localizações', '📍')
