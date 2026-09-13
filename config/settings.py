"""
Django settings per CornHole League.

Principio: lo STESSO file di settings gira in locale, in Docker e sulla VM.
Ciò che cambia tra ambienti (segreti, debug, host, database) NON sta qui ma nelle
variabili d'ambiente, lette con os.environ. In sviluppo le variabili arrivano dal
file `.env` (caricato da python-dotenv); in produzione le passa il container.

Riferimento: https://docs.djangoproject.com/en/6.1/ref/settings/
"""

import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

# BASE_DIR = cartella root del repo (quella con manage.py). Usalo per costruire path: BASE_DIR / 'x'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Carica `.env` se esiste. Se una variabile è già nell'ambiente (es. in Docker) NON la sovrascrive.
load_dotenv(BASE_DIR / ".env")


# --- Sicurezza / ambiente ---------------------------------------------------------------------

# Nessun default: se manca in .env, Django si rifiuta di partire. Meglio un errore subito che
# una chiave "insecure" finita in produzione per sbaglio.
SECRET_KEY = os.environ["SECRET_KEY"]

# Le env var sono sempre stringhe: "False" è truthy in Python! Per questo confrontiamo il testo.
DEBUG = os.environ.get("DEBUG", "False").lower() in ("1", "true", "yes")

ALLOWED_HOSTS = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", "").split(",") if h.strip()]


# --- Applicazioni -----------------------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # app nostre
    "league",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
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
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# --- Database ---------------------------------------------------------------------------------
# Se DATABASE_URL è definita (Neon in produzione) la usiamo; altrimenti SQLite locale.
# dj_database_url.config() legge la variabile e la traduce nel dizionario che Django si aspetta.
# conn_max_age: riusa la connessione per 10 minuti invece di riaprirla a ogni richiesta (Neon è remoto).

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL, conn_health_checks=True, conn_max_age=600)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# --- Utenti -----------------------------------------------------------------------------------
# Modello utente personalizzato (league/models.py). Va dichiarato PRIMA della prima migrazione:
# cambiarlo dopo è doloroso perché tutte le FK verso auth.User andrebbero riscritte.

AUTH_USER_MODEL = "league.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# --- Localizzazione ---------------------------------------------------------------------------
# I datetime sono salvati in UTC nel DB (USE_TZ) e convertiti in Europe/Rome quando mostrati.

LANGUAGE_CODE = "it-it"
TIME_ZONE = "Europe/Rome"
USE_I18N = True
USE_TZ = True


# --- File statici -----------------------------------------------------------------------------
# In Fase 8 qui aggiungeremo la build di React (frontend/dist) e WhiteNoise.

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --- Email ------------------------------------------------------------------------------------
# Per ora le email (se mai ne manderemo) finiscono in console.

MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.console.EmailBackend",
    },
}
