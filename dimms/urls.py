from django.urls import path
from .views import *

app_name = 'dimms'

urlpatterns = [
    path('', homepage, name='homepage'),    
]

