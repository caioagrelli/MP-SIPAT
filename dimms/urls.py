from django.urls import path
from . import views

app_name = 'dimms'

urlpatterns = [
    path('', views.homepage, name='homepage'),    
]

