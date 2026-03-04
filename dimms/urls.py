from django.urls import path
from . import views

app_name = 'dimms'

urlpatterns = [
    path('', views.homepage, name='homepage'),    
    path('overview/<int:pk>/', views.overview, name='overview'),
    path('overview/<int:pk>/qrcode/', views.qrcode_view, name='qrcode'),
    path("overview/<int:pk>/label/", views.label, name="label"),   
]

