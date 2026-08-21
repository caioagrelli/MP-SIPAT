from django.urls import path, include
from .views import *

app_name = 'dempam'

urlpatterns = [
    # Url's da Homepage
    path('', homepage, name='homepage'),
    path('municipios/<str:codigo_ibge>/resumo/', municipio_resumo, name='municipio_resumo'),
    path('circunscricoes/<str:circunscricao>/resumo/', circunscricao_resumo, name='circunscricao_resumo'),
    path('ranking-gastos/', ranking_gastos, name='ranking_gastos'),

    # Mural de Avisos
    path('avisos/', aviso_lista, name='aviso_lista'),
    path('avisos/novo/', aviso_criar, name='aviso_criar'),
    path('avisos/<int:pk>/editar/', aviso_editar, name='aviso_editar'),
    path('avisos/<int:pk>/excluir/', aviso_excluir, name='aviso_excluir'),

    # Painel de TV (gestão à vista)
    path('tv/', painel_tv, name='painel_tv'),
    path('tv/config/', painel_tv_config, name='painel_tv_config'),

    # Busca de UA (autocomplete)
    path("uas/search/", ua_search, name="ua_search"),

    # Url's das UAs (Unidades Administrativas)
    path("uas/", ua_homepage, name="ua_homepage"),
    path("uas/exportar/", ua_export_xlsx, name="ua_export_xlsx"),
    path("uas/add/", ua_add, name="ua_add"),
    path("uas/<int:pk>/", ua_detail, name="ua_detail"),
    path("uas/<int:pk>/update/", ua_update, name="ua_update"),

    # Url's dos Prédios e Circunscrição
    path("locate/", locate_homepage, name="locate_homepage"),
    path("locate/add/", locate_add, name="locate_add"),
    path("locate/<int:pk>/", predio_detail, name="predio_detail"),

    # Url's das Salas e Setores
    path("sector/", sector_homepage, name="sector_homepage"),
    path("sector/add/", sector_add, name="sector_add"),
    path("sector/<int:pk>/", sector_detail, name="sector_detail"),
    path("sector/<int:pk>/edit/", sector_edit, name="sector_edit"),
    path("sector/<int:pk>/itens/buscar/", sector_item_search, name="sector_item_search"),
    path("sector/<int:pk>/delete/", sector_delete, name="sector_delete"),
    path("sector/<int:pk>/corredores/imprimir/", imprimir_corredores, name="imprimir_corredores"),
    path("sector/<int:pk>/corredor/<str:corredor>/", corredor_detail, name="corredor_detail"),
    path("sector/locate/add/", sector_locate_add, name="sector_locate_add"),
    path("sector/locate/<int:pk>/", locate_detail, name="locate_detail"),
    path("sector/locate/<int:pk>/edit/", locate_edit, name="locate_edit"),
    path("sector/locate/<int:pk>/delete/", locate_delete, name="locate_delete"),

]

