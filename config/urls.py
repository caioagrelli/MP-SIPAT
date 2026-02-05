# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # Esta linha agora é a única responsável por todas as páginas do seu site
    path('', include('itens.urls')),
]

# Isso continua, para que as fotos dos itens funcionem
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)