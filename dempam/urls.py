from django.urls import path
from .views import *

app_name = 'dempam'

urlpatterns = [
    path('', homepage, name='homepage'),
    
]

