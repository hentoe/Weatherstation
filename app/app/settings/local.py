# flake8: noqa: E501
from .base import *  # noqa: F403
from .base import INSTALLED_APPS
from .base import MIDDLEWARE

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = True
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    default="vBeWaqC6ceCa7iBRtyfplXNQT2FbFApnHe8uabEiAYznEPdkosiNpoXiFZ3oAMVN",
)
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ["localhost", "0.0.0.0", "127.0.0.1"]  # noqa: S104
CORS_ALLOWED_ORIGINS = ["http://localhost:5173"]
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.console.EmailBackend",
    },
}

# django-silk
# ------------------------------------------------------------------------------
#
INSTALLED_APPS += ["silk"]
MIDDLEWARE += ["silk.middleware.SilkyMiddleware"]
