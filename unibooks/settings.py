import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# Security: read SECRET_KEY from environment in production. Keep a dev fallback for local work.
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'replace-me-in-development')

# DEBUG should be False in production. Override in production settings.
DEBUG = os.environ.get('DJANGO_DEBUG', '1') == '1'

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '').split() if os.environ.get('DJANGO_ALLOWED_HOSTS') else []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'library',
    'widget_tweaks',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise middleware for serving static files in production
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'library.middleware.ForcePasswordChangeMiddleware',
    'library.middleware.SubscriptionMiddleware',
]

ROOT_URLCONF = 'unibooks.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # Inject unread notifications count into every template
                'library.context_processors.unread_notifications',
            ],
        },
    },
]

WSGI_APPLICATION = 'unibooks.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Allow configuring the database via the DATABASE_URL environment variable (Render/Postgres)
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
]

LANGUAGE_CODE = 'fr-fr'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Where `collectstatic` will collect static files for production
STATIC_ROOT = BASE_DIR / 'staticfiles'
# Use WhiteNoise compressed manifest storage in production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Optional: configure S3 storage for MEDIA files if AWS credentials are provided.
# This allows using S3 (or compatible storage) for uploaded files in production.
if os.environ.get('AWS_STORAGE_BUCKET_NAME'):
    # These packages are optional and must be added to requirements if used
    # django-storages and boto3
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', None)
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_S3_CUSTOM_DOMAIN = os.environ.get('AWS_S3_CUSTOM_DOMAIN')
    # Optional: set this to False to avoid signed URLs for public buckets
    AWS_QUERYSTRING_AUTH = False

# Media files (uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'library.User'

# Use the actual routes included at project root. Previously these pointed to
# '/student/...', which caused redirects to 404 since student urls are mounted
# at root (e.g. '/login/', '/dashboard/'). Updated to match the current URL config.
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'

# Allow authentication by username/email/matricule
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'library.auth_backends.MatriculeEmailBackend',
]

# Email (development)
EMAIL_BACKEND = os.environ.get('DJANGO_EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
DEFAULT_FROM_EMAIL = os.environ.get('DJANGO_DEFAULT_FROM_EMAIL', 'noreply@unibooks.local')

# Production notes: replace EMAIL_BACKEND with SMTP/SendGrid and set credentials via env vars.

# Security-related defaults (safe to override in production settings)
SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', '0') == '1'
CSRF_COOKIE_SECURE = os.environ.get('CSRF_COOKIE_SECURE', '0') == '1'
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', '0') == '1'
SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', '0'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get('SECURE_HSTS_INCLUDE_SUBDOMAINS', '0') == '1'
SECURE_HSTS_PRELOAD = os.environ.get('SECURE_HSTS_PRELOAD', '0') == '1'
SECURE_CONTENT_TYPE_NOSNIFF = os.environ.get('SECURE_CONTENT_TYPE_NOSNIFF', '1') == '1'
SECURE_BROWSER_XSS_FILTER = os.environ.get('SECURE_BROWSER_XSS_FILTER', '1') == '1'
X_FRAME_OPTIONS = os.environ.get('X_FRAME_OPTIONS', 'DENY')

