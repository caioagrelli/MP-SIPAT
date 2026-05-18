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
    path('historico/<int:pk>/relatorio/',               relatorio_mudanca,    name='relatorio_mudanca'),
    path('meus-bens/',                                  meus_bens,            name='meus_bens'),
    path('meus-bens/<str:tombo>/',                      detalhe_bem,          name='detalhe_bem'),
    path('meus-bens/<str:tombo>/atualizar-foto/',       atualizar_foto,       name='atualizar_foto'),
    path('meus-bens/<str:tombo>/inventario/',           registrar_inventario, name='registrar_inventario'),

    # Controle de Prazos
    path('controle-prazos/',                            controle_prazos,      name='controle_prazos'),

    # Inventário
    path('inventario/painel/',                          painel_inventario,    name='painel_inventario'),
    path('inventario/abrir/',                           abrir_inventario,     name='abrir_inventario'),

    # Movimentação
    path('movimentacao/',                               lista_solicitacoes,      name='lista_solicitacoes'),
    path('movimentacao/nova/',                          criar_solicitacao,       name='criar_solicitacao'),
    path('movimentacao/solicitacao/<int:pk>/',          analisar_solicitacao,    name='analisar_solicitacao'),
    path('movimentacao/transferir/<str:tombo>/',        transferir_bem,          name='transferir_bem'),
    path('movimentacao/<int:pk>/termo/',                termo_transferencia,     name='termo_transferencia'),
    path('movimentacao/historico/<str:tombo>/',         historico_movimentacoes, name='historico_movimentacoes'),

    # Catálogo — Marketplace
    path('catalogo/',                                   catalogo_lista,                    name='catalogo_lista'),
    path('catalogo/pdf/',                               catalogo_pdf,                      name='catalogo_pdf'),
    path('catalogo/novo/',                              catalogo_criar,                    name='catalogo_criar'),
    path('catalogo/<int:pk>/',                          catalogo_detalhe,                  name='catalogo_detalhe'),
    path('catalogo/<int:pk>/editar/',                   catalogo_editar,                   name='catalogo_editar'),
    path('catalogo/<int:pk>/excluir/',                  catalogo_excluir,                  name='catalogo_excluir'),

    # Catálogo — Carrinho  (tipo: perm | cons)
    path('catalogo/carrinho/add/<str:tipo>/<int:pk>/',    catalogo_cart_add,               name='catalogo_cart_add'),
    path('catalogo/carrinho/remove/<str:tipo>/<int:pk>/', catalogo_cart_remove,            name='catalogo_cart_remove'),
    path('catalogo/carrinho/update/<str:tipo>/<int:pk>/', catalogo_cart_update,            name='catalogo_cart_update'),
    path('catalogo/carrinho/limpar/',                     catalogo_cart_clear,               name='catalogo_cart_clear'),
    path('catalogo/checkout/',                            catalogo_checkout,                 name='catalogo_checkout'),

    # Catálogo — Solicitações
    path('catalogo/minhas-solicitacoes/',               minhas_solicitacoes,               name='minhas_solicitacoes'),
    path('catalogo/minhas-solicitacoes/permanentes/',   minhas_solicitacoes_catalogo,      name='minhas_solicitacoes_catalogo'),
    path('catalogo/aprovacao/',                         painel_solicitacoes_catalogo,      name='painel_solicitacoes_catalogo'),
    path('catalogo/aprovacao/<int:pk>/',                aprovar_solicitacao_catalogo,      name='aprovar_solicitacao_catalogo'),
]
