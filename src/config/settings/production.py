from decouple import Csv, config

from .base import *  # noqa: F403,F401

DEBUG = config('DEBUG', default=False, cast=bool)
SECRET_KEY = config('SECRET_KEY')
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='', cast=Csv())
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='', cast=Csv())

SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=True, cast=bool)
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True, cast=bool)
SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=True, cast=bool)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# TLS terminates at the reverse proxy in the production topology.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_REDIRECT_EXEMPT = [r'^health/$']

STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_ROOT = BASE_DIR / 'media'
