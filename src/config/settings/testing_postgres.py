"""Configuración de pruebas contra PostgreSQL, equivalente al entorno productivo."""

from decouple import config

from .base import *  # noqa: F403,F401

DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'testserver']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('TEST_DB_NAME', default=config('DB_NAME', default='istqb_test')),
        'USER': config('TEST_DB_USER', default=config('DB_USER', default='postgres')),
        'PASSWORD': config('TEST_DB_PASSWORD', default=config('DB_PASSWORD', default='postgres')),
        'HOST': config('TEST_DB_HOST', default=config('DB_HOST', default='localhost')),
        'PORT': config('TEST_DB_PORT', default=config('DB_PORT', default='5432')),
        'TEST': {
            'NAME': config('TEST_DB_NAME', default='istqb_test'),
        },
    }
}
