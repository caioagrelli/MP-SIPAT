from django.urls import path
from .views import *

app_name = 'manutencao'

urlpatterns = [
    path('', homepage, name='homepage'),

    # Estoque
    path('estoque/', estoque_planilha, name='estoque_planilha'),
    path('estoque/entrada/', estoque_entrada, name='estoque_entrada'),
    path('estoque/saida/', registrar_saida, name='estoque_saida'),
    path('estoque/search/', estoque_search, name='estoque_search'),

    # Provisórios
    path('relatorios/', relatorios, name='relatorios'),
    path('localizacoes/', localizacoes, name='localizacoes'),
]
