from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LoginView
from sipat.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", root, name="root"), #verifica se eu já estou logado e me manda para a página principal
    path("login/", LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("accounts/", include("django.contrib.auth.urls")),
]
