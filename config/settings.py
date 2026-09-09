"""
Django settings for the CCL/CCDL Support Ticketing System.

Kept intentionally simple for this phase: no Celery/Redis, no external
Odoo integration. Notifications are sent synchronously (see
apps.notifications.services) and SLA breach checks run via a management
command intended to be scheduled with cron.
"""
from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "django_filters",
    "corsheaders",
    # Local apps
    "apps.accounts",
    "apps.tickets",
    "apps.notifications",
    "apps.analytics",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST", default="localhost"),
        "PORT": env("DB_PORT", default="5432"),
    }
}

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Dhaka"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Ticket attachments (images, PDF, Excel)
TICKET_ATTACHMENT_MAX_BYTES = env.int("TICKET_ATTACHMENT_MAX_BYTES", default=10 * 1024 * 1024)
TICKET_ATTACHMENT_MAX_FILES = env.int("TICKET_ATTACHMENT_MAX_FILES", default=5)
TICKET_ATTACHMENT_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".pdf",
    ".xls",
    ".xlsx",
}
# Back-compat aliases used by older upload helpers
TICKET_IMAGE_MAX_BYTES = TICKET_ATTACHMENT_MAX_BYTES
TICKET_IMAGE_MAX_FILES = TICKET_ATTACHMENT_MAX_FILES
TICKET_IMAGE_EXTENSIONS = TICKET_ATTACHMENT_EXTENSIONS

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- REST framework ---------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=8),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
}

# --- CORS ---------------------------------------------------------------
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])

# --- Email (synchronous sending, no Celery/Redis in this phase) --------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
SUPPORT_TEAM_EMAIL = env("SUPPORT_TEAM_EMAIL", default="")

# --- SLA defaults (minutes), overridden per-policy in the DB -----------
DEFAULT_FIRST_RESPONSE_MINUTES = 60
DEFAULT_RESOLUTION_MINUTES = 24 * 60

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}

# --- LDAP (cg-bd.com) — aligned with working ERP/LDAP env schema ----------
# Prefer LDAP_URI (other projects); LDAP_SERVER_URI kept as alias.
LDAP_ENABLED = env.bool("LDAP_ENABLED", default=False)
LDAP_ALLOW_LOCAL_FALLBACK = env.bool("LDAP_ALLOW_LOCAL_FALLBACK", default=True)
LDAP_LOGGING = env.bool("LDAP_LOGGING", default=False)

_ldap_uri = env("LDAP_URI", default="") or env("LDAP_SERVER_URI", default="") or env("LDAP_SERVER", default="")
LDAP_SERVER_URI = _ldap_uri.strip().strip('"')
LDAP_URI = LDAP_SERVER_URI

LDAP_USE_SSL = env.bool(
    "LDAP_USE_SSL",
    default=LDAP_SERVER_URI.lower().startswith("ldaps://"),
)
LDAP_USE_STARTTLS = env.bool("LDAP_USE_STARTTLS", default=False) or env.bool(
    "LDAP_START_TLS", default=False
)
LDAP_START_TLS = LDAP_USE_STARTTLS

LDAP_BIND_DN = env("LDAP_BIND_DN", default="").strip().strip('"')
LDAP_BIND_PASSWORD = env("LDAP_BIND_PASSWORD", default="").strip().strip('"')
LDAP_REQUIRE_SERVICE_BIND = env.bool("LDAP_REQUIRE_SERVICE_BIND", default=False)

# Search base: LDAP_BASE_DN (other projects) or LDAP_USER_SEARCH_BASE
LDAP_USER_SEARCH_BASE = (
    env("LDAP_BASE_DN", default="") or env("LDAP_USER_SEARCH_BASE", default="")
).strip().strip('"')
LDAP_BASE_DN = LDAP_USER_SEARCH_BASE

LDAP_USER_SEARCH_FILTER = env(
    "LDAP_USER_SEARCH_FILTER",
    default="(|(sAMAccountName={username})(userPrincipalName={username})(uid={username})(cn={username}))",
)
# DN template: support both {username} and legacy %(user)s
_dn_tmpl = env("LDAP_USER_DN_TEMPLATE", default="").strip().strip('"')
LDAP_USER_DN_TEMPLATE = _dn_tmpl.replace("%(user)s", "{username}") if _dn_tmpl else ""

# upn | dn | search  (working ERP project uses upn: user@cg-bd.com)
LDAP_BIND_FORMAT = env("LDAP_BIND_FORMAT", default="upn").strip().lower()
LDAP_UPN_SUFFIX = env("LDAP_UPN_SUFFIX", default="cg-bd.com").strip()
LDAP_EMAIL_DOMAIN = env("LDAP_EMAIL_DOMAIN", default=LDAP_UPN_SUFFIX or "cg-bd.com")

LDAP_CONNECT_TIMEOUT = env.int("LDAP_TIMEOUT", default=env.int("LDAP_CONNECT_TIMEOUT", default=8))
LDAP_TLS_REQUIRE_CERT = env("LDAP_TLS_REQUIRE_CERT", default="demand").strip().lower()

LDAP_ATTRS = [
    "mail",
    "userPrincipalName",
    "givenName",
    "sn",
    "telephoneNumber",
    "mobile",
    "memberOf",
    "cn",
    "uid",
    "sAMAccountName",
]

_raw_group_map = env("LDAP_COMPANY_GROUP_MAP", default="")
LDAP_COMPANY_GROUP_MAP = {}
if _raw_group_map:
    for part in _raw_group_map.split(";"):
        part = part.strip()
        if not part or ":" not in part:
            continue
        group, code = part.rsplit(":", 1)
        LDAP_COMPANY_GROUP_MAP[group.strip()] = code.strip().lower()

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]
