from django.contrib import admin
from django.urls import path, include

handler403 = 'accounts.views.errors.permission_denied'
from django.contrib.auth.views import LoginView
from django.conf import settings
from django.conf.urls.static import static
from dempam.views import root, home
from accounts.views import password_reset

# Garante que o admin sempre use o login por formulário,
# independente do LOGIN_URL definido nas settings (ex: OIDC em produção).
admin.site.login_url = '/login/'

urlpatterns = [
    # url's essencials
    path('admin/', admin.site.urls), # url de admin
    path('', root, name='root'), # url de direcionamento
    path('accounts/', include('django.contrib.auth.urls')),
    
    #url de login
    path('login/', LoginView.as_view(
        template_name="registration/login.html",
        extra_context={'oidc_enabled': bool(getattr(settings, 'OIDC_OP_AUTHORIZATION_ENDPOINT', ''))},
    ), name="login"),  # url de login
    path("oidc/", include("mozilla_django_oidc.urls")),
    
    path("password-reset/", password_reset.password_reset_request, name="password_reset"),
    path("password-reset/done/", password_reset.password_reset_done, name="password_reset_done"),
    
    # url da homepage
    path('home/', home, name='home'),

    # url's apps
    path('dempam/', include(('dempam.urls', 'dempam'), namespace='dempam')),
    path('dimms/', include(('dimms.urls', 'dimms'), namespace='dimms')),
    path('dimrcbp/', include(('dimrcbp.urls', 'dimrcbp'), namespace='dimrcbp')),
    path('access/', include(('accounts.urls', 'accounts'), namespace='accounts')),
    path('demands/', include(('demands.urls', 'demands'), namespace='demands')),
    path('manutencao/', include(('manutencao.urls', 'manutencao'), namespace='manutencao')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
