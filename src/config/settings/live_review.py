from .testing import *

# Temporary settings used only for the local manual review session / preview.
DEBUG = True
ALLOWED_HOSTS = ['*']

# The sandbox preview is shown inside a cross-origin iframe/proxy. Django's
# clickjacking middleware sends X-Frame-Options: DENY, which renders that
# preview completely blank. It is removed ONLY for this review environment;
# production keeps the hardened defaults.
MIDDLEWARE = [m for m in MIDDLEWARE if m != 'django.middleware.clickjacking.XFrameOptionsMiddleware']
SECURE_CROSS_ORIGIN_OPENER_POLICY = None

# If the preview is embedded in a cross-origin iframe the browser treats our
# cookies as third-party; SameSite=Lax would silently drop the session and the
# user could never get past the login screen. Allow cross-site usage ONLY in
# this review environment (the preview is served over HTTPS).
SESSION_COOKIE_SAMESITE = 'None'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = 'None'
CSRF_COOKIE_SECURE = True

# Show the demo accounts on the login screen so the platform can be tried
# immediately (see apps.core.context_processors.project_context).
DEMO_ACCOUNTS = [
    {'role': 'Estudiante', 'email': 'estudiante@review.local', 'password': 'Rev1ewStudent!2026'},
    {'role': 'Docente', 'email': 'docente@review.local', 'password': 'Rev1ewTeacher!2026'},
    {'role': 'Administrador', 'email': 'admin@review.local', 'password': 'Rev1ewAdmin!2026'},
]
