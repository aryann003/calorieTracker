"""
Django settings for mysite project.
Production-ready for Render deployment and local SQLite development.
"""

from pathlib import Path
import os
import dj_database_url


BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(key, default=False):
    value = os.getenv(key)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(key, default=None):
    raw = os.getenv(key, "")
    values = [item.strip() for item in raw.split(",") if item.strip()]
    if values:
        return values
    return default or []


def load_env_file(path):
    """
    Simple local .env loader.
    Useful for local development only.
    Render will use its own environment variables.
    """
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


load_env_file(BASE_DIR / "mysite" / ".env")


# SECURITY

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "django-insecure-local-development-key-change-in-production"
)

DEBUG = env_bool("DEBUG", default=True)

ALLOWED_HOSTS = env_list(
    "ALLOWED_HOSTS",
    default=["localhost", "127.0.0.1"]
)

CSRF_TRUSTED_ORIGINS = env_list(
    "CSRF_TRUSTED_ORIGINS",
    default=[]
)


# APPLICATIONS

INSTALLED_APPS = [
    "myapp",

    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]


# MIDDLEWARE

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


ROOT_URLCONF = "mysite.urls"


# TEMPLATES

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


WSGI_APPLICATION = "mysite.wsgi.application"


# DATABASE
# Local development: SQLite
# Render production: PostgreSQL using DATABASE_URL

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# PASSWORD VALIDATION

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# INTERNATIONALIZATION

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# STATIC FILES

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"
WHITENOISE_USE_FINDERS = True


# AUTH REDIRECTS

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/"


# DEFAULT PRIMARY KEY FIELD TYPE

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"