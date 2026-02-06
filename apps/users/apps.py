from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = 'apps.users'

    class Meta:
        default_auto_field = 'django.db.models.BigAutoField'
