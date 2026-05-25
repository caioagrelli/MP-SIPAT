from .base import *
from os import environ

DEBUG = False

# OIDC como método de login em produção
AUTHENTICATION_BACKENDS = [
    "mozilla_django_oidc.auth.OIDCAuthenticationBackend",
    "django.contrib.auth.backends.ModelBackend",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "mozilla_django_oidc.middleware.SessionRefresh",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

LOGIN_URL = "/oidc/authenticate/"

ALLOWED_HOSTS = environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": environ.get("DB_NAME", "db_name"),
        "USER": environ.get("DB_USER", "db_user"),
        "PASSWORD": environ.get("DB_PASSWORD", "db_user_password"),
        "HOST": environ.get("DB_HOST", "db_host"),
        "PORT": environ.get("DB_PORT", "db_port_number"),
    }
}

# Security settings
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

STATIC_ROOT = BASE_DIR / "staticfiles"

# OIDC settings
OIDC_RP_CLIENT_ID = environ.get("OIDC_RP_CLIENT_ID", "")
OIDC_RP_CLIENT_SECRET = environ.get("OIDC_RP_CLIENT_SECRET", "")

OIDC_OP_AUTHORIZATION_ENDPOINT = environ.get("OIDC_OP_AUTHORIZATION_ENDPOINT", "")
OIDC_OP_TOKEN_ENDPOINT = environ.get("OIDC_OP_TOKEN_ENDPOINT", "")
OIDC_OP_USER_ENDPOINT = environ.get("OIDC_OP_USER_ENDPOINT", "")
OIDC_OP_JWKS_ENDPOINT = environ.get("OIDC_OP_JWKS_ENDPOINT", "")
OIDC_RP_SIGN_ALGO = environ.get("OIDC_RP_SIGN_ALGO", "RS256")
