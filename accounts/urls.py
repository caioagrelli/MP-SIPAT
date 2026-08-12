from django.urls import path
from accounts.views import users, groups, profile, feedback

urlpatterns = [
    path('usuarios/', users.users_list, name='users_list'),
    path('usuarios/novo/', users.user_create, name='user_create'),
    path('usuarios/<int:pk>/editar/', users.user_edit, name='user_edit'),
    path('usuarios/<int:pk>/redefinir-senha/', users.user_reset_password, name='user_reset_password'),
    path('grupos/', groups.groups_list, name='groups_list'),
    path('grupos/criar/', groups.group_create, name='group_create'),
    path('grupos/<int:pk>/editar/', groups.group_edit, name='group_edit'),
    path('grupos/<int:pk>/deletar/', groups.group_delete, name='group_delete'),
    path('grupos/<int:pk>/permissoes/', groups.group_permissions, name='group_permissions'),
    path('perfil/', profile.profile_view, name='profile'),
    path('trocar-senha/', profile.first_login_password_change, name='first_login_password_change'),
    path('feedback/', feedback.reportar, name='reportar_feedback'),
    path('feedback/lista/', feedback.lista_feedback, name='lista_feedback'),
    path('feedback/<int:pk>/status/', feedback.atualizar_status, name='atualizar_status_feedback'),
]
