from django.urls import path
from . import views

app_name = 'dimms'

urlpatterns = [
    path('', views.homepage, name='homepage'),    
    path('detail/<int:pk>/', views.detail, name='detail'),
]

