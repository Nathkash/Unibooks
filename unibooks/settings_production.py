import os
from .settings import *  # noqa: F401,F403

import dj_database_url

# Require a SECRET_KEY from env in production
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']  # KeyError if not set

# Force DEBUG off in production
DEBUG = False

# ALLOWED_HOSTS should be set explicitly in the environment (space separated)
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '').split()

# Database: prefer DATABASE_URL (Railway). Fallback to POSTGRES_* if needed.
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': os.environ.get('POSTGRES_DB', 'unibooks'),
            'USER': os.environ.get('POSTGRES_USER', 'unibooks'),
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD', ''),
            'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
            'PORT': os.environ.get('POSTGRES_PORT', '5432'),
        }
    }

# Static files: insist on whitenoise manifest storage in production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Respect proxy headers
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Security hardening
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', '1') == '1'
SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', '31536000'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get('SECURE_HSTS_INCLUDE_SUBDOMAINS', '1') == '1'
SECURE_HSTS_PRELOAD = os.environ.get('SECURE_HSTS_PRELOAD', '1') == '1'

# Email (production)
EMAIL_BACKEND = os.environ.get('DJANGO_EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
DEFAULT_FROM_EMAIL = os.environ.get('DJANGO_DEFAULT_FROM_EMAIL', 'noreply@yourdomain')

# Logging: output to console so the PaaS can capture it
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'root': {
        'handlers': ['console'],
        'level': os.environ.get('DJANGO_LOG_LEVEL', 'WARNING'),
    },
}
