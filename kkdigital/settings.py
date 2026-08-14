import os
import dj_database_url
from pathlib import Path
from decouple import config

"""
Django settings for kkdigital project.
Configured for Hostinger Shared Hosting (Passenger WSGI) Production Deployment.
"""

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config("SECRET_KEY", default="django-insecure-90#6nbusl%x&!ebwo08@%g9(!e*j&ld(2)4-=8!yi(ggbqpa8#")

# SECURITY WARNING: don't run with debug turned on in production!
IS_VERCEL = bool(os.environ.get("VERCEL"))
DEBUG = config("DEBUG", default=not IS_VERCEL, cast=bool)

# Allowed Hosts Configuration
ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="kkdigitalgrowth.com,www.kkdigitalgrowth.com,localhost,127.0.0.1,.vercel.app",
    cast=lambda v: [s.strip() for s in v.split(",") if s.strip()]
)

# Dynamically handle VERCEL_URL environment variable if provided by Vercel
VERCEL_URL = config("VERCEL_URL", default=None) or os.environ.get("VERCEL_URL")
if VERCEL_URL:
    vercel_host = VERCEL_URL.replace("https://", "").replace("http://", "").split("/")[0].strip()
    if vercel_host and vercel_host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(vercel_host)

# CSRF Trusted Origins Configuration
CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    default="https://kkdigitalgrowth.com,https://www.kkdigitalgrowth.com,https://*.vercel.app",
    cast=lambda v: [s.strip() for s in v.split(",") if s.strip()]
)

if VERCEL_URL:
    vercel_host = VERCEL_URL.replace("https://", "").replace("http://", "").split("/")[0].strip()
    if vercel_host:
        vercel_origin = f"https://{vercel_host}"
        if vercel_origin not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(vercel_origin)

SITE_DOMAIN = config("SITE_DOMAIN", default="https://kkdigitalgrowth.com")

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'website',
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = 'kkdigital.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'kkdigital.wsgi.application'

# Database Configuration (Hostinger Remote MySQL Database)
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass

DB_HOST = config("DB_HOST", default="srv788.hstgr.io")
DB_PORT = config("DB_PORT", cast=int, default=3306)
DB_NAME = config("DB_NAME", default="u394319514_kkdigital_db")
DB_USER = config("DB_USER", default="u394319514_kkdigital_user")
DB_PASSWORD = config("DB_PASSWORD", default="Kkdigitalgrowth@2026")

if config("USE_LOCAL_DB", default=False, cast=bool):
    print("\n[DATABASE NOTICE] Using local SQLite database (db.sqlite3) via USE_LOCAL_DB flag.\n")
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": DB_NAME,
            "USER": DB_USER,
            "PASSWORD": DB_PASSWORD,
            "HOST": DB_HOST,
            "PORT": DB_PORT,
            "OPTIONS": {
                "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
                "connect_timeout": 15,
            },
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images) handled by WhiteNoise
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Blog images. MEDIA_URL matches the /uploads/ path used by Hostinger's
# public_html/uploads/, so a stored image URL is identical whichever of the two
# actually holds the file.
MEDIA_URL = "/uploads/"
MEDIA_ROOT = BASE_DIR / "media" / "uploads"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Hostinger Remote Upload Configuration
#
# HOSTINGER_UPLOAD_URL   : the upload.php endpoint, which must resolve to the
#                          Hostinger server that owns /public_html/uploads/.
# HOSTINGER_MEDIA_DOMAIN : the public host browsers load stored images from.
#                          It must resolve to the same Hostinger server, so
#                          /uploads/<file> is served by Hostinger and never
#                          reaches Django.
#
# Both are environment-overridable: point them at a hostname served by
# Hostinger without touching any code.
HOSTINGER_UPLOAD_URL = config("HOSTINGER_UPLOAD_URL", default="https://cdn.kkdigitalgrowth.com/upload.php")

# When upload.php cannot be reached or fails, store the image with Django under
# MEDIA_ROOT instead of rejecting the upload. The URL written to blogs.image is
# the same either way: HOSTINGER_MEDIA_DOMAIN + /uploads/<filename>.
BLOG_IMAGE_LOCAL_FALLBACK = config("BLOG_IMAGE_LOCAL_FALLBACK", default=True, cast=bool)

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

EMAIL_HOST = "smtp.hostinger.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False

EMAIL_HOST_USER = config(
    "EMAIL_HOST_USER",
    default="admin@kkdigitalgrowth.com"
)

EMAIL_HOST_PASSWORD = config(
    "EMAIL_HOST_PASSWORD",
    default=""
)

DEFAULT_FROM_EMAIL = config(
    "DEFAULT_FROM_EMAIL",
    default="admin@kkdigitalgrowth.com"
)

CONTACT_NOTIFICATION_EMAIL = config(
    "CONTACT_NOTIFICATION_EMAIL",
    default="admin@kkdigitalgrowth.com"
)
HOSTINGER_MEDIA_DOMAIN = config("HOSTINGER_MEDIA_DOMAIN", default="https://www.kkdigitalgrowth.com")
HOSTINGER_UPLOAD_MAX_BYTES = config("HOSTINGER_UPLOAD_MAX_BYTES", default=5 * 1024 * 1024, cast=int)