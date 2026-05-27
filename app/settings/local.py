from .base import *
from os import environ

DEBUG = True

ALLOWED_HOSTS = ['*']

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": environ.get("DB_NAME", "sipat"),
        "USER": environ.get("DB_USER", "sipat"),
        "PASSWORD": environ.get("DB_PASSWORD", "sipat"),
        "HOST": environ.get("DB_HOST", "db"),
        "PORT": environ.get("DB_PORT", "5432"),
    }
}

STATIC_ROOT = BASE_DIR / "staticfiles"
