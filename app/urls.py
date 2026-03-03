from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LoginView
from django.conf import settings
from django.conf.urls.static import static
from dempam.views import root, home

urlpatterns = [
    # url's essencials
    path('admin/', admin.site.urls), # url de admin
    path('', root, name='root'), # url de direcionamento
    path('login/', LoginView.as_view(template_name="registration/login.html"), name="login"), # url de login
    path('accounts/', include('django.contrib.auth.urls')),
    
    # url da homepage
    path('home/', home, name='home'),

    # url's apps
    path('dempam/', include(('dempam.urls', 'dempam'), namespace='dempam')),
    path('dimms/', include(('dimms.urls', 'dimms'), namespace='dimms')),
    path('dimrcbp/', include(('dimrcbp.urls', 'dimrcbp'), namespace='dimrcbp')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
