import os
from celery import Celery
from celery.signals import setup_logging
from celery.schedules import crontab


# Set the default Django settings module for the 'celery' program.
# Note: we point to 'config.settings' which uses split-settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('ownit')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'close-days-chores': {'task': 'chores.tasks.close_days_chores', 'schedule': crontab(minute=0, hour=0)},
    'assign-chores': {'task': 'chores.tasks.assign_chores', 'schedule': crontab(minute=30, hour=0)},
}


@setup_logging.connect
def config_loggers(*args, **kwargs):
    from logging.config import dictConfig

    from django.conf import settings

    dictConfig(settings.LOGGING)


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
