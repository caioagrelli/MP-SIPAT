from .base import *

DEBUG = True

# Força o uso das páginas de erro customizadas mesmo em desenvolvimento
DEBUG_PROPAGATE_EXCEPTIONS = False

ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


