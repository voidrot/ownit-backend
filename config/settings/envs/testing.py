from config.settings.components.base import *  # noqa: F403

# Testing should be fast and deterministic
DEBUG = False

# Use fast password hasher
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

# Use in-memory email backend
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Store media in memory or temp directory
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
    },
}

# Disable unnecessary apps/middleware if present in base (though typically added in dev)
# We ensure they are NOT added here. Since we import * from base, we only have what base has.
# Dev tools like debug_toolbar and zeal are added in development.py, so they won't be here.

# Add any test-specific apps if needed
# INSTALLED_APPS += ["tests"]

# Use SQLite for testing to avoid postgres dependency issues in CI/Test envs
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Ensure logout page renders for testing
ACCOUNT_LOGOUT_ON_GET = False
