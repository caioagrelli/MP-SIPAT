from django.urls import path, include
from .views import *

app_name = 'dempam'

urlpatterns = [
    # Url's da Homepage 
    path('', homepage, name='homepage'),

    # Url's das UAs (Unidades Administrativas)
    path("uas/", ua_homepage, name="ua_homepage"),
    path("uas/add/", ua_add, name="ua_add"),
    #path("uas/<int:pk>/update/", ua_update, name="ua_update"),

    # Url's dos Prédios e Circunscrição
    path("locate/", locate_homepage, name="locate_homepage"),
    path("locate/add/", locate_add, name="locate_add"),
    #path("locate/", locate_homepage, name="locate_homepage"),
    
]

