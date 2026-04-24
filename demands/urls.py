from django.urls import path
from .views import *

app_name = 'demands'

urlpatterns = [
    # Demandas
    path('',              homepage,       name='homepage'),
    path('criar/',        demand_create,  name='create'),
    path('<int:pk>/',     demand_detail,  name='detail'),

    # Tipos de demanda
    path('tipos/',                    demand_types_list,   name='types_list'),
    path('tipos/criar/',              demand_type_create,  name='type_create'),
    path('tipos/<int:pk>/editar/',    demand_type_edit,    name='type_edit'),
    path('tipos/<int:pk>/toggle/',    demand_type_toggle,  name='type_toggle'),
]
