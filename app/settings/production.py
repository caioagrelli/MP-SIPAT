from .base import *
from os import environ

DEBUG = False

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")

DATABASES = {
    "default": {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': environ.get("DB_NAME", "db_name"),
        'USER': environ.get("DB_USER", "db_user"),
        'PASSWORD': environ.get("DB_PASSWORD", "db_user_password"),
        'HOST': environ.get("DB_HOST", "db_host"),
        'PORT': environ.get("DB_PORT", "db_port_number"),
    }
}

# Security settings
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

STATIC_ROOT = "/app/data/static"
MEDIA_ROOT = "/app/data/media"
