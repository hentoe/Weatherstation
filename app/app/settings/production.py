"""Production settings and validation for the deployed application."""

import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403


def _environment_flag(name):
    return os.environ.get(name, "false").lower() in {"1", "true", "yes"}


REQUIRED_ENVIRONMENT_VARIABLES = (
    "DJANGO_SECRET_KEY",
    "DJANGO_ALLOWED_HOSTS",
    "PUBLIC_HTTPS",
    "VUE_FRONTEND_ORIGINS",
    "DB_HOST",
    "DB_NAME",
    "DB_USER",
    "DB_PASS",
    "EMAIL_HOST",
    "EMAIL_HOST_USER",
    "EMAIL_HOST_PASSWORD",
    "DEFAULT_FROM_EMAIL",
    "SERVER_EMAIL",
)
missing = [
    name for name in REQUIRED_ENVIRONMENT_VARIABLES if not os.environ.get(name)
]
if missing:
    raise ImproperlyConfigured(
        "Missing required production environment variables: "
        + ", ".join(missing)
    )

if not all(  # noqa: F405
    origin.startswith(("http://", "https://")) for origin in FRONTEND_ORIGINS
):
    raise ImproperlyConfigured(
        "VUE_FRONTEND_ORIGINS entries must include http:// or https://."
    )

if any("://" in host or "/" in host for host in ALLOWED_HOSTS):  # noqa: F405
    raise ImproperlyConfigured(
        "DJANGO_ALLOWED_HOSTS entries must be hostnames without a scheme "
        "or path."
    )

if _environment_flag("EMAIL_USE_TLS") and _environment_flag("EMAIL_USE_SSL"):
    raise ImproperlyConfigured(
        "EMAIL_USE_TLS and EMAIL_USE_SSL cannot both be enabled."
    )

DEBUG = False
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

if _environment_flag("PUBLIC_HTTPS"):
    CSRF_TRUSTED_ORIGINS = list(  # noqa: F405
        dict.fromkeys(
            [
                *CSRF_TRUSTED_ORIGINS,  # noqa: F405
                *[
                    f"https://{host}"
                    for host in ALLOWED_HOSTS  # noqa: F405
                    if host != "*"
                ],
            ]
        )
    )
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
