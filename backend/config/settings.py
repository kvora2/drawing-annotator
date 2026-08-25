from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Dev only. Not to ship this key or DEBUG=True to production.
SECRET_KEY = "this-is-a-placeholder-key-do-not-use-in-production"
DEBUG = True

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "annotations",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Local dev: let the Vite dev server talk to the API without CORS friction.
CORS_ALLOW_ALL_ORIGINS = True

STATIC_URL = "static/"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    # No auth for the take-home. A real deployment would add auth + per-user scoping.
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
}

# DPI used when rasterizing pages for on-screen display.
DISPLAY_DPI = 144
# Higher DPI used only for the OCR crop, so recognition quality is better than the display.
OCR_DPI = 300
