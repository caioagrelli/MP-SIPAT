from django.urls import path
from .views import *

app_name = 'dimrcbp'

urlpatterns = [
    path('', homepage, name='homepage'),    
]