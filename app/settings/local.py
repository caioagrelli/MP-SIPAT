from .base import *
from os import environ

DEBUG = True

ALLOWED_HOSTS = ['*']

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "accounts.middleware.ForcePasswordChangeMiddleware",
]

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

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
