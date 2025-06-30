from pathlib import Path
import os
import openai
from dotenv import load_dotenv

load_dotenv()  
openai.api_key = os.getenv("OPENAI_API_KEY")


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIRS = os.path.join(BASE_DIR, 'templates')


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-k08ogl=of0o93xfq!v5fglp$5x(ij*8yv525d(xoc+&a5kf32f'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'channels',
    'App_UserCompte',
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
    'App_UserCompte.middleware.UpdateLastConnectionMiddleware'
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
                'App_UserCompte.context_processors.nouvelles_videos',
                'App_UserCompte.context_processors.base_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'UserCompte.wsgi.application'
ASGI_APPLICATION = "UserCompte.asgi.application"


# Pour mémoire Redis ou in-memory (test local)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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



# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'fr'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "App_UserCompte/static"),
]
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50 Mo
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

    "search_model": "App_UserCompte.Profil",
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





