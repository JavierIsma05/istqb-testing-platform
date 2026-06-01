from .base import *

DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'testserver']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'test_db.sqlite3',
    }
}
