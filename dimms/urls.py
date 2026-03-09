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
    
    path('active_balance/', active_balance, name='active_balance'), #inativa
    path('register_movement/', register_movement, name='register_movement'), #inativa
    
    
]

