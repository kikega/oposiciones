"""
Django settings for oposiciones project.

Configuration for development environment.
"""

from .base import *

# Base
DEBUG = True

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# django-extensions
INSTALLED_APPS += [
    'django_extensions',
    'debug_toolbar',
]

# Configuración del Debug toolbar
MIDDLEWARE += [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]
INTERNAL_IPS = [
    '127.0.0.1',
]
