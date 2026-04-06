from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LoginView
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from dempam.views import root, home

urlpatterns = [
    # url's essencials
    path('admin/', admin.site.urls), # url de admin
    path('', root, name='root'), # url de direcionamento
    path('accounts/', include('django.contrib.auth.urls')),
    
    #url de login
    path('login/', LoginView.as_view(template_name="registration/login.html"), name="login"),  # url de login
    path("oidc/", include("mozilla_django_oidc.urls")),
    
    path("password-reset/", auth_views.PasswordResetView.as_view(template_name="registration/password_reset.html"), name="password_reset"),
    path("password-reset/done/", auth_views.PasswordResetDoneView.as_view(template_name="registration/password_reset_done.html"), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(template_name="registration/password_reset_confirm.html"), name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(template_name="registration/password_reset_complete.html"), name="password_reset_complete"),    
    
    # url da homepage
    path('home/', home, name='home'),

    # url's apps
    path('dempam/', include(('dempam.urls', 'dempam'), namespace='dempam')),
    path('dimms/', include(('dimms.urls', 'dimms'), namespace='dimms')),
    path('dimrcbp/', include(('dimrcbp.urls', 'dimrcbp'), namespace='dimrcbp')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
