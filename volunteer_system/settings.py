import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-change-me-to-a-secure-one")

DEBUG = os.environ.get("DEBUG", "True").lower() == "true"

ALLOWED_HOSTS = os.environ.get(
    "ALLOWED_HOSTS",
    "localhost,127.0.0.1,.ngrok-free.app"
).split(",")

# ------------------------
# CSRF & SECURITY SETTINGS
# ------------------------
# CSRF_TRUSTED_ORIGINS: รองรับทั้ง localhost และ ngrok domains
# หมายเหตุ: Django ไม่รองรับ wildcard ใน CSRF_TRUSTED_ORIGINS
# สำหรับ ngrok: ต้องระบุ domain เต็มๆ เช่น https://372e8fe832c8.ngrok-free.app
# หรือตั้งค่าใน environment variable CSRF_TRUSTED_ORIGINS
# ตัวอย่าง: CSRF_TRUSTED_ORIGINS=https://372e8fe832c8.ngrok-free.app,http://localhost:8000
default_csrf_origins = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
# เพิ่ม ngrok domain จาก environment variable ถ้ามี
csrf_origins_env = os.environ.get("CSRF_TRUSTED_ORIGINS", "")
if csrf_origins_env:
    default_csrf_origins.extend([origin.strip() for origin in csrf_origins_env.split(",") if origin.strip()])
CSRF_TRUSTED_ORIGINS = default_csrf_origins

# Cookie settings สำหรับรองรับทั้ง localhost และ ngrok
# หมายเหตุ: SameSite=None ต้องใช้กับ Secure=True เสมอ (HTTPS เท่านั้น)
# สำหรับ ngrok (HTTPS): ตั้งค่า SESSION_COOKIE_SAMESITE=None, CSRF_COOKIE_SAMESITE=None, และ Secure=True
# สำหรับ localhost (HTTP): ตั้งค่า SESSION_COOKIE_SAMESITE=Lax, CSRF_COOKIE_SAMESITE=Lax, และ Secure=False
# 
# วิธีใช้: ตั้งค่า environment variable
# - สำหรับ ngrok: SESSION_COOKIE_SAMESITE=None, CSRF_COOKIE_SAMESITE=None, SESSION_COOKIE_SECURE=True, CSRF_COOKIE_SECURE=True
# - สำหรับ localhost: ใช้ค่า default (Lax, Secure=False)

# SameSite settings
SESSION_COOKIE_SAMESITE = os.environ.get("SESSION_COOKIE_SAMESITE", "Lax")
CSRF_COOKIE_SAMESITE = os.environ.get("CSRF_COOKIE_SAMESITE", "Lax")

# Secure settings (ต้องเป็น True เมื่อใช้ HTTPS/ngrok)
CSRF_COOKIE_SECURE = os.environ.get("CSRF_COOKIE_SECURE", "False").lower() == "true"
SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "False").lower() == "true"

# ตั้งค่า HttpOnly=False เพื่อให้ JavaScript อ่าน CSRF cookie ได้ (จำเป็นสำหรับ fetch API)
CSRF_COOKIE_HTTPONLY = False

# สำหรับ ngrok: ต้องตั้งค่า SECURE_PROXY_SSL_HEADER เพื่อให้ Django รู้ว่า request มาจาก HTTPS
# ngrok จะส่ง header X-Forwarded-Proto: https
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Secret for signing QR tokens (can be overridden via env)
QR_SECRET = os.environ.get("QR_SECRET", SECRET_KEY)


# ------------------------
# INSTALLED APPS
# ------------------------
INSTALLED_APPS = [
    # Django default apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Your apps
    "volunteer_app",

    # Third-party apps
    "widget_tweaks",
    "tailwind",
    "django_browser_reload",

    # Tailwind theme app
    "theme",
]

# ------------------------
# Tailwind Settings
# ------------------------
TAILWIND_APP_NAME = "theme"  # ชื่อแอปที่ใช้เก็บไฟล์ tailwind

INTERNAL_IPS = [
    "127.0.0.1",
]  # ให้ django_browser_reload ใช้งานได้

# ------------------------
# MIDDLEWARE
# ------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_browser_reload.middleware.BrowserReloadMiddleware",  # ✅ เพิ่ม
]

# ------------------------
# URL / WSGI
# ------------------------
ROOT_URLCONF = "volunteer_system.urls"

WSGI_APPLICATION = "volunteer_system.wsgi.application"


# ------------------------
# TEMPLATES
# ------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "volunteer_app" / "templates"],  # templates ของ app
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # Add unread notifications count for templates
                "volunteer_app.context_processors.unread_notifications",
            ],
        },
    },
]


# ------------------------
# DATABASE
# ------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# ------------------------
# PASSWORD VALIDATION
# ------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# ------------------------
# LANGUAGE / TIMEZONE
# ------------------------
LANGUAGE_CODE = "th"
TIME_ZONE = "Asia/Bangkok"
USE_I18N = True
USE_TZ = True


# ------------------------
# STATIC & MEDIA FILES
# ------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "volunteer_app" / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
NPM_BIN_PATH = "C:/Program Files/nodejs/npm.cmd"

STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# ------------------------
# USER & LOGIN SETTINGS
# ------------------------
AUTH_USER_MODEL = "volunteer_app.User"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"


# ------------------------
# DEFAULT PRIMARY KEY FIELD
# ------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ------------------------
# EMAIL CONFIGURATION
# ------------------------
EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND", 
    "django.core.mail.backends.console.EmailBackend"  # Console backend for development
)
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True").lower() == "true"
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@ubu.ac.th")


# ------------------------
# LOGGING CONFIGURATION
# ------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "filters": {
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "file": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "logs" / "django.log",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": os.environ.get("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        "volunteer_app": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# Create logs directory if it doesn't exist
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)
