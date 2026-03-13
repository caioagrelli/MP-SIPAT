from django.urls import path
from .views import *

app_name = 'dimms'

urlpatterns = [
    path('', homepage, name='homepage'),    
    path('overview/<int:pk>/', overview, name='overview'),
    path('overview/<int:pk>/qrcode/', qrcode_view, name='qrcode'),
    path('overview/<int:pk>/label/', label, name='label'),
    
    path('essential/', essential, name='essential'),
    path('low_stock/', low_stock, name='low_stock'),
    path('expiration_alert/', expiration_alert, name='expiration_alert'),
    
    path('processing/', processing, name='processing'),
    path('processing/<int:pk>/', details_processing, name='details_processing'),
    path('processing/<int:solicitacao_pk>/course/<int:tramitacao_pk>/', course, name='course'),
    path('processing/create_request/', create_request, name='create_request'), 
    path('processing/create_update/',create_update,name= 'create_update'),
    path('processing/<int:pk>/update_request/', update_request, name='update_request'),
    
    path('contracts/', contracts, name='contracts'),

    # path('active_balance/', active_balance, name='active_balance'), #inativa    
    ]

