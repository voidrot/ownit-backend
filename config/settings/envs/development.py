from config.settings.components.base import *  # noqa: F403
from config.settings.components.base import MIDDLEWARE, INSTALLED_APPS

DEBUG = True

INSTALLED_APPS += [
    'zeal',
    'debug_toolbar',
]
MIDDLEWARE += [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'zeal.middleware.zeal_middleware',
]


# Debug Toolbar
def show_toolbar(request):
    from django.conf import settings

    return settings.DEBUG


DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': show_toolbar,
}

ALLOWED_HOSTS = ['*']

# Print emails to console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Disable manifest storage in development to avoid running collectstatic
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
    },
}
