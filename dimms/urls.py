# Importações do Django
from django.urls import path

# Importações do códigp
from .views import *

# =================================
# URL'S DA DIMMS (BENS DE CONSUMO)
# =================================



app_name = 'dimms'

urlpatterns = [
    # Url's da Homepage e Páginas de Aviso
    path('', homepage, name='homepage'),
    path('essential/', essential, name='essential'),
    path('low_stock/', low_stock, name='low_stock'),
    path('expiration_alert/', expiration_alert, name='expiration_alert'),
    
    
    # Url's do detalhamento de cada bem
    path('overview/<int:pk>/', overview, name='overview'),
    path('overview/<int:pk>/qrcode/', qrcode_view, name='qrcode'),
    path('overview/<int:pk>/label/', label, name='label'),
    path('overview/<int:pk>/edit/', overview_edit, name='overview_edit'),
    

    # Url's de Solicitações
    path('processing/', processing, name='processing'),
    path('processing/<int:pk>/', details_processing, name='details_processing'),
    path('processing/create_request/', create_request, name='create_request'), 
    path('processing/create_update/',create_update,name= 'create_update'),
    path('processing/<int:pk>/update_request/', update_request, name='update_request'),
    path('processing/<int:pk>/update_request/qrcode/', qrcode_update, name='qrcode_update'),
    path('processing/<int:pk>/update_request/label/', label_update, name='label_update'),
    path('processing/<int:solicitacao_pk>/course/<int:tramitacao_pk>/', course, name='course'),
    
    
    # Busca de E-Fisco (autocomplete)
    path('efisco/search/', efisco_search, name='efisco_search'),

    # Url's dos Artefatos e das Propostas
    path('artifacts/', artifacts, name='artifacts'),
    path('artifacts/<int:pk>/', artifacts_details, name='artifacts_details'),
    path('artifacts/<int:pk>/edit', artifacts_edit, name='artifacts_edit'),
    path('artifacts/<int:pk>/new/', artifacts_add, name='artifacts_add'),
    path('artifacts/<int:pk>/documents/', artifacts_documents, name='artifacts_documents'),
    path('artifacts/new/', artifacts_create, name='artifacts_create'),
    path('proposals/<int:pk>/', proposal_details, name='proposal_details'),
    path('proposal/<int:pk>/status/', proposal_status, name='proposal_item_update_status'),
    path('artifacts/<int:pk>/proposal/create/', proposal_create, name='proposal_create'),
    path('proposals/<int:pk>/item/add/', proposal_item_add, name='proposal_item_add'),
    path('proposals/item/<int:pk>/delete/', proposal_item_delete, name='proposal_item_delete'),
    path('proposals/<int:pk>/contrato/', contrato_create, name='contrato_create'),
    path('contrato/<int:pk>/', contrato_detail, name='contrato_detail'),
    path('contrato/<int:contrato_pk>/saldo/gerar/<int:proposal_pk>/', contrato_gerar_saldo, name='contrato_gerar_saldo'),


    # Url's do Saldo Ativo
    path('saldo-ativo/', saldo_ativo_homepage, name='saldo_ativo_homepage'),
    path('saldo-ativo/solicitacoes/', saldo_ativo_solicitacoes, name='saldo_ativo_solicitacoes'),
    path('saldo-ativo/solicitacao/criar/', saldo_ativo_solicitacao_create, name='saldo_ativo_solicitacao_create'),
    path('saldo-ativo/solicitacao/<int:pk>/', saldo_ativo_solicitacao_detail, name='saldo_ativo_solicitacao_detail'),
    path('saldo-ativo/envio/<int:item_pk>/', saldo_ativo_confirmar_envio, name='saldo_ativo_confirmar_envio'),


    # Url's das Ações no estoque
    path('stock_add/', stock_add, name='stock_add'),
    path('stock_up/', stock_up, name='stock_up'),
    path('bensconsumo/', bensconsumo, name='bensconsumo'),
    path('bensconsumo/add/', bensconsumo_add, name='bensconsumo_add'),
    path('bensconsumo/<int:pk>/edit/', bensconsumo_edit, name='bensconsumo_edit'),
    path('bensconsumo/<int:pk>/delete/', bensconsumo_delete, name='bensconsumo_delete'),      
    ]

