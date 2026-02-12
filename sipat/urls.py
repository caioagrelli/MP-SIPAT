from django.urls import path
from .views import *

urlpatterns = [
    path('home/', homepage, name='homepage'),
    path('bensconsumo/', bensconsumo, name='bensconsumo'),
    path('benspermanentes/', benspermanentes, name='benspermanentes'),
    path('setores/', setores, name='setores')
]
