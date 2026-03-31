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
    

    # Url's de Solicitações
    path('processing/', processing, name='processing'),
    path('processing/<int:pk>/', details_processing, name='details_processing'),
    path('processing/create_request/', create_request, name='create_request'), 
    path('processing/create_update/',create_update,name= 'create_update'),
    path('processing/<int:pk>/update_request/', update_request, name='update_request'),
    path('processing/<int:pk>/update_request/qrcode/', qrcode_update, name='qrcode_update'),
    path('processing/<int:pk>/update_request/label/', label_update, name='label_update'),
    path('processing/<int:solicitacao_pk>/course/<int:tramitacao_pk>/', course, name='course'),
    
    
    # Url's dos Artefatos e das Propostas
    path('artifacts/', artifacts, name='artifacts'),
    path('artifacts/<int:pk>/', artifacts_details, name='artifacts_details'),
    path('artifacts/<int:pk>/edit', artifacts_edit, name='artifacts_edit'),
    path('artifacts/<int:pk>/new/', artifacts_add, name='artifacts_add'),
    path('artifacts/<int:pk>/documents/', artifacts_documents, name='artifacts_documents'),
    path('artifacts/new/', artifacts_create, name='artifacts_create'),
    path('proposals/<int:pk>/', proposal_details, name='proposal_details'),
    path('proposal/<int:pk>/status/', proposal_status, name='proposal_item_update_status'),


    # Url's das Ações no estoque 
    path('stock_add/', stock_add, name='stock_add'),
    path('bensconsumo/', bensconsumo, name='bensconsumo'),
    path('bensconsumo/add/', bensconsumo_add, name='bensconsumo_add'),
    path('bensconsumo/<int:pk>/edit/', bensconsumo_edit, name='bensconsumo_edit'),
    path('bensconsumo/<int:pk>/delete/', bensconsumo_delete, name='bensconsumo_delete'),
      
    ]

