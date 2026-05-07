from django.urls import path
from .views import *

app_name = 'dimrcbp'

urlpatterns = [
    path('',                                            homepage,             name='homepage'),
    path('cadastro-bem/',                               cadastro_bem,         name='cadastro_bem'),
    path('consultas/filtros-operacionais/',             filtros_operacionais, name='filtros_operacionais'),
    path('consultas/bem/<str:tombo>/',                  bem_detalhe_admin,    name='bem_detalhe_admin'),
    path('consultas/bem/<str:tombo>/qrcode/',           qrcode_bem,           name='qrcode_bem'),
    path('consultas/bem/<str:tombo>/etiqueta/',         etiqueta_bem,         name='etiqueta_bem'),
    path('consultas/bem/<str:tombo>/editar/',           editar_bem,              name='editar_bem'),
    path('consultas/bem/<str:tombo>/foto/',             atualizar_foto_admin,    name='atualizar_foto_admin'),
    path('historico/<int:pk>/relatorio/',              relatorio_mudanca,    name='relatorio_mudanca'),
    path('meus-bens/',                                  meus_bens,            name='meus_bens'),
    path('meus-bens/<str:tombo>/',                      detalhe_bem,          name='detalhe_bem'),
    path('meus-bens/<str:tombo>/atualizar-foto/',       atualizar_foto,       name='atualizar_foto'),

    # Controle de Prazos
    path('controle-prazos/',                            controle_prazos,      name='controle_prazos'),

    # Catálogo
    path('catalogo/',                                   catalogo_lista,       name='catalogo_lista'),
    path('catalogo/pdf/',                               catalogo_pdf,         name='catalogo_pdf'),
    path('catalogo/novo/',                              catalogo_criar,       name='catalogo_criar'),
    path('catalogo/<int:pk>/',                          catalogo_detalhe,     name='catalogo_detalhe'),
    path('catalogo/<int:pk>/editar/',                   catalogo_editar,      name='catalogo_editar'),
    path('catalogo/<int:pk>/excluir/',                  catalogo_excluir,     name='catalogo_excluir'),
]
