from config.settings.components.base import env

# Storages
# Default to local if AWS keys are not set
AWS_ACCESS_KEY_ID = env.str('AWS_ACCESS_KEY_ID', default=None)
AWS_SECRET_ACCESS_KEY = env.str('AWS_SECRET_ACCESS_KEY', default=None)
AWS_STORAGE_BUCKET_NAME = env.str('AWS_STORAGE_BUCKET_NAME', default=None)
AWS_S3_REGION_NAME = env.str('AWS_S3_REGION_NAME', default=None)
AWS_S3_ENDPOINT_URL = env.str('AWS_S3_ENDPOINT_URL', default=None)

if AWS_ACCESS_KEY_ID and AWS_STORAGE_BUCKET_NAME:
    STORAGES = {
        'default': {
            'BACKEND': 'storages.backends.s3.S3Storage',
            'OPTIONS': {
                'endpoint_url': AWS_S3_ENDPOINT_URL,
            },
        },
        'staticfiles': {
            'BACKEND': 'storages.backends.s3.S3Storage',
            'OPTIONS': {
                'endpoint_url': AWS_S3_ENDPOINT_URL,
            },
        },
    }
else:
    # Keep default local storages
    STORAGES = {
        'default': {
            'BACKEND': 'django.core.files.storage.FileSystemStorage',
        },
        'staticfiles': {
            'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
        },
    }
