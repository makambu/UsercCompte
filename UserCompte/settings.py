from pathlib import Path
import os
from decouple import config
from dotenv import load_dotenv

load_dotenv()

# OpenAI
import openai
openai.api_key = config("OPENAI_API_KEY")

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIRS = os.path.join(BASE_DIR, 'templates')

SECRET_KEY = 'django-insecure-k08ogl=of0o93xfq!v5fglp$5x(ij*8yv525d(xoc+&a5kf32f'

# Sécurité
SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=lambda v: v.split(","))

# Applications
INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'channels',
    'app_usercompte',
    'widget_tweaks',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'app_usercompte.middleware.UpdateLastConnectionMiddleware'
]

ROOT_URLCONF = 'UserCompte.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATES_DIRS],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'app_usercompte.context_processors.nouvelles_videos',
                'app_usercompte.context_processors.base_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'UserCompte.wsgi.application'
ASGI_APPLICATION = "UserCompte.asgi.application"

# Channels (local ou Redis si Render Redis utilisé)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}

# Base de données (MySQL pour Render)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config("DB_NAME"),
        'USER': config("DB_USER"),
        'PASSWORD': config("DB_PASSWORD"),
        'HOST': config("DB_HOST"),
        'PORT': config("DB_PORT", default=3306, cast=int),
    }
}

# Validation des mots de passe
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Logging (facultatif mais utile sur Render)
LOGGING = {
    "version": 1,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

# Langue & fuseau
LANGUAGE_CODE = 'fr'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Statique & Média
STATIC_URL = 'static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, "app_usercompte/static")]
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Autres
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800

# --------------------
# 🎨 Apparence & branding
# --------------------
JAZZMIN_SETTINGS = {
    "site_title": "CGM Admin",
    "site_header": "Administration CGM",
    "site_brand": "CGM Plateforme",
    "site_logo": "images/logo_cgm.png",  # 📌 Mets ce fichier dans static/images/
    "login_logo": "images/logo_cgm.png",
    "login_logo_dark": "images/logo_cgm.png",

    "welcome_sign": "Bienvenue sur le panneau d'administration de CGM",
    "copyright": "© 2025 CGM",
    "show_sidebar": True,
    "navigation_expanded": True,

    "search_model": "app_usercompte.Profil",
    "hide_apps": [],
    "hide_models": [],
    "order_with_respect_to": ["auth", "Profil", "Blog", "VideoPublier"],

    "icons": {
        "auth": "fas fa-users-cog",
        "Profil": "fas fa-user",
        "Blog": "fas fa-blog",
        "VideoPublier": "fas fa-video",
        "Notification": "fas fa-bell",
        "InvitationAmi": "fas fa-user-plus",
        "RelationAmi": "fas fa-user-friends",
    },

    "topmenu_links": [
        {"name": "Accueil Site", "url": "/", "permissions": ["auth.view_user"], "new_window": True},
        {"model": "auth.User"},
        {"app": "auth"},
    ],

    "usermenu_links": [
        {"name": "Retour au site", "url": "/", "new_window": True},
    ],

    "show_ui_builder": False,  # Cache l’éditeur d’interface
    "changeform_format": "horizontal_tabs",  # Affichage par onglets dans admin
}

# --------------------
# 🌙 Thème visuel
# --------------------
JAZZMIN_UI_TWEAKS = {
    "theme": "darkly",  # Thème sombre
    "dark_mode_theme": "darkly",

    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,

    "brand_small_text": False,
    "brand_colour": "navbar-dark bg-dark",

    "accent": "accent-primary",
    "navbar": "navbar-dark bg-dark",
    "no_navbar_border": True,

    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": True,

    "theme_switcher": False,
    "actions_sticky_top": True,
}





