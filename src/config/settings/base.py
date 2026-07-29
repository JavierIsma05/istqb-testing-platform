from pathlib import Path
from decouple import config
import os

os.environ.setdefault(
    'PGCLIENTENCODING',
    config('PGCLIENTENCODING', default='UTF8')
)

# =========================
# BASE DIRECTORY
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# =========================
# SECURITY
# =========================
SECRET_KEY = config('SECRET_KEY')

DEBUG = False

ALLOWED_HOSTS = []

# =========================
# JAZZMIN (debe ir ANTES que django.contrib.admin)
# =========================
JAZZMIN_APP = [
    'jazzmin',
]

# =========================
# DJANGO APPS
# =========================
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

# =========================
# LOCAL APPS
# =========================
LOCAL_APPS = [
    'apps.core',
    'apps.authentication',
    'apps.users',
    'apps.dashboard',
    'apps.projects',
    'apps.requirements',
    'apps.testplans',
    'apps.testcases',
    'apps.executions',
    'apps.defects',
    'apps.incidents',
    'apps.traceability',
    'apps.reports',
    'apps.notifications',
    'apps.audit',
    'apps.phases',
]

# =========================
# THIRD PARTY APPS
# =========================
THIRD_PARTY_APPS = [
]

# =========================
# INSTALLED APPS
# =========================
INSTALLED_APPS = JAZZMIN_APP + DJANGO_APPS + LOCAL_APPS + THIRD_PARTY_APPS

# =========================
# MIDDLEWARE
# =========================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# =========================
# ROOT URLS
# =========================
ROOT_URLCONF = 'config.urls'

# =========================
# TEMPLATES
# =========================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',

        'DIRS': [
            BASE_DIR / 'templates',
        ],

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

# =========================
# WSGI
# =========================
WSGI_APPLICATION = 'config.wsgi.application'

# =========================
# DATABASE
# =========================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='istqb_db'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default='postgres'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}
# AUTH USER MODEL
AUTH_USER_MODEL = 'users.User'
# =========== LOGIN ==============
LOGIN_URL = 'login'

LOGIN_REDIRECT_URL = 'dashboard'

LOGOUT_REDIRECT_URL = 'login'

CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = 'DENY'

AUTOMATION_ALLOWED_HOSTS = tuple(
    host.strip()
    for host in config(
        'AUTOMATION_ALLOWED_HOSTS',
        default='localhost,127.0.0.1,::1',
    ).split(',')
    if host.strip()
)

# =========================
# PASSWORD VALIDATORS
# =========================
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

# =========================
# LANGUAGE
# =========================
LANGUAGE_CODE = 'es-ec'

TIME_ZONE = 'America/Guayaquil'

USE_I18N = True

USE_TZ = True

# =========================
# STATIC FILES
# =========================
STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

STATIC_ROOT = BASE_DIR / 'staticfiles'

# =========================
# MEDIA FILES
# =========================
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# =========================
# DEFAULT PRIMARY KEY
# =========================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==============================================================================
# JAZZMIN - Personalización del panel de administración Django
# ==============================================================================
# Documentación: https://django-jazzmin.readthedocs.io/
#
# Se personaliza únicamente el /admin/ sin modificar modelos, vistas ni URLs.
# Paleta profesional: azul (#0d6efd) principal, blanco fondos, gris paneles,
# verde acciones positivas, rojo solo para errores/defectos.
# ==============================================================================

JAZZMIN_SETTINGS = {
    # ------------------------------------------------------------------
    # TEXTOS DEL ADMINISTRADOR (Requerimiento 3)
    # ------------------------------------------------------------------
    'site_title': 'Panel Administrativo',
    'site_header': 'Sistema de Gestión del Ciclo de Vida de Pruebas',
    'site_brand': 'ISTQB Platform',
    'welcome_sign': 'Bienvenido al Sistema de Gestión del Ciclo de Vida de Pruebas',
    'copyright': '© Universidad Nacional de Loja — Carrera de Computación',

    # ------------------------------------------------------------------
    # LOGO (Requerimiento 8) - Placeholder para reemplazar posteriormente
    # ------------------------------------------------------------------
    'site_logo': 'admin/img/logo.svg',
    'login_logo': 'admin/img/logo-login.svg',
    'login_logo_dark': 'admin/img/logo-login.svg',

    # ------------------------------------------------------------------
    # BÚSQUEDA
    # ------------------------------------------------------------------
    'search_model': ['users.User', 'projects.Project', 'requirements.Requirement'],

    # ------------------------------------------------------------------
    # ENLACES SUPERIORES (topmenu_links)
    # ------------------------------------------------------------------
    'topmenu_links': [
        {'name': 'Dashboard', 'url': 'admin:index', 'permissions': ['auth.view_user'], 'icon': 'fas fa-tachometer-alt'},
        {'app': 'projects'},
        {'app': 'requirements'},
        {'app': 'testplans'},
        {'app': 'testcases'},
    ],

    # ------------------------------------------------------------------
    # ORGANIZACIÓN DEL MENÚ LATERAL (Requerimiento 6)
    # Orden lógico del proceso ISTQB
    # ------------------------------------------------------------------
    'order_with_respect_to': [
        'projects',
        'requirements',
        'testplans',
        'testcases',
        'executions',
        'defects',
        'incidents',
        'traceability',
        'reports',
        'notifications',
        'audit',
        'phases',
        'users',
        'auth',
    ],

    # ------------------------------------------------------------------
    # ICONOS POR APLICACIÓN (Requerimiento 5)
    # Utilizando Font Awesome v6+
    # ------------------------------------------------------------------
    'icons': {
        # Usuarios y Autenticación
        'auth': 'fas fa-shield-alt',
        'auth.Group': 'fas fa-users',
        'users': 'fas fa-user-circle',
        'users.User': 'fas fa-user',
        'users.Profile': 'fas fa-address-card',

        # Proyectos
        'projects': 'fas fa-folder',
        'projects.Project': 'fas fa-folder-open',

        # Requisitos
        'requirements': 'fas fa-list-check',
        'requirements.Requirement': 'fas fa-clipboard-list',

        # Planes de Prueba
        'testplans': 'fas fa-clipboard',
        'testplans.TestPlan': 'fas fa-file-alt',

        # Casos de Prueba
        'testcases': 'fas fa-vial',
        'testcases.TestCase': 'fas fa-flask',

        # Ejecuciones
        'executions': 'fas fa-play-circle',
        'executions.TestExecution': 'fas fa-play',
        'executions.TestStepExecution': 'fas fa-list-ol',
        'executions.AutomatedValidationRule': 'fas fa-robot',
        'executions.AutomatedExecutionResult': 'fas fa-check-double',

        # Defectos
        'defects': 'fas fa-bug',
        'defects.Defect': 'fas fa-exclamation-circle',

        # Incidentes
        'incidents': 'fas fa-exclamation-triangle',
        'incidents.Incident': 'fas fa-radiation',

        # Trazabilidad
        'traceability': 'fas fa-link',
        'traceability.TraceabilityLink': 'fas fa-project-diagram',

        # Reportes
        'reports': 'fas fa-chart-line',
        'reports.Report': 'fas fa-file-invoice',

        # Notificaciones
        'notifications': 'fas fa-bell',
        'notifications.Notification': 'fas fa-envelope-open-text',

        # Auditoría
        'audit': 'fas fa-history',
        'audit.AuditLog': 'fas fa-clipboard-check',

        # Fases
        'phases': 'fas fa-layer-group',
        'phases.TestingPhase': 'fas fa-sitemap',
    },

    # ------------------------------------------------------------------
    # CONFIGURACIÓN VISUAL DEL MENÚ
    # ------------------------------------------------------------------
    'default_icon_parents': 'fas fa-folder-open',
    'default_icon_children': 'fas fa-circle',
    'show_sidebar': True,
    'navigation_expanded': True,
    'hide_apps': [],
    'hide_models': [],

    # ------------------------------------------------------------------
    # MODALES Y FORMULARIOS
    # ------------------------------------------------------------------
    'related_modal_active': True,
    'changeform_format': 'horizontal_tabs',
    'changeform_format_overrides': {
        'auth.user': 'collapsible',
        'auth.group': 'vertical_tabs',
    },

    # ------------------------------------------------------------------
    # CSS / JS PERSONALIZADO (Requerimiento 12)
    # ------------------------------------------------------------------
    'custom_css': 'admin/custom_admin.css',
    'custom_js': None,

    # ------------------------------------------------------------------
    # CONSTRUCTOR UI
    # ------------------------------------------------------------------
    'show_ui_builder': False,

    # ------------------------------------------------------------------
    # PÁGINA DE INICIO DEL ADMIN
    # ------------------------------------------------------------------
    'index_title': 'Administración de la Plataforma',

    # ------------------------------------------------------------------
    # BOTONES DE ACCIONES MASIVAS
    # ------------------------------------------------------------------
    'actions_as_buttons': True,
}

# ==============================================================================
# JAZZMIN UI TWEAKS - Personalización visual avanzada (Requerimiento 4 y 7)
# ==============================================================================

JAZZMIN_UI_TWEAKS = {
    # --- TAMAÑO DE TEXTO ---
    'navbar_small_text': False,
    'footer_small_text': False,
    'body_small_text': False,
    'brand_small_text': False,
    'sidebar_nav_small_text': False,

    # --- BARRA SUPERIOR (NAVBAR) ---
    'brand_colour': 'navbar-white navbar-light',
    'accent': 'accent-primary',
    'navbar': 'navbar-white navbar-light',
    'no_navbar_border': False,
    'navbar_fixed': True,

    # --- LAYOUT ---
    'layout_boxed': False,
    'footer_fixed': False,
    'sidebar_fixed': True,

    # --- BARRA LATERAL (SIDEBAR) ---
    'sidebar': 'sidebar-dark-primary',
    'sidebar_disable_expand': False,
    'sidebar_child_indent': True,
    'sidebar_nav_compact_style': False,
    'sidebar_nav_legacy_style': False,
    'sidebar_nav_flat_style': False,

    # --- TEMAS (Requerimiento 7: modo oscuro habilitado) ---
    'theme': 'cosmo',
    'dark_mode_theme': 'darkly',

    # --- COLORES DE BOTONES (Requerimiento 4) ---
    # Profesional: azul principal, blanco fondos, gris paneles,
    # verde acciones positivas, rojo solo para errores/defectos
    'button_classes': {
        'primary': 'btn-primary',          # Azul (#0d6efd) - acciones principales
        'secondary': 'btn-secondary',       # Gris - acciones secundarias
        'info': 'btn-info',                # Celeste - información
        'warning': 'btn-warning',          # Amarillo - advertencias
        'danger': 'btn-danger',            # Rojo - solo errores/defectos
        'success': 'btn-success',          # Verde - acciones positivas
    },
}
