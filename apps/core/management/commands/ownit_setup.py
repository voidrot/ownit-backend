from django.core.management.base import BaseCommand
from environs import env


def _infer_content_type_target(perm_codename: str) -> tuple[str, str]:
    """
    Infer the content type app label and model for a permission codename.
    """
    if perm_codename.endswith('_user'):
        return ('users', 'user')
    if 'chore' in perm_codename:
        return ('chores', 'chore')
    if 'behavior' in perm_codename:
        return ('behavior', 'behavior')
    return ('users', 'user')


def _permission_name(perm_codename: str) -> str:
    """
    Return a readable permission name for a codename.
    """
    return f'Can {perm_codename.replace("_", " ")}'


class Command(BaseCommand):
    help = 'Configures the OwnIt application with necessary initial data, such as groups and permissions.'

    def add_arguments(self, parser):
        # No additional arguments needed for this command
        pass

    def handle(self, *args, **options) -> None:
        """
        Create initial users, groups, and permissions for OwnIt.
        """
        from django.contrib.auth.models import Group
        from apps.users.models import User

        # Create initial superuser
        if not User.objects.filter(username=env.str('INITIAL_SUPERUSER_USERNAME', default='admin')).exists():
            User.objects.create_superuser(
                username=env.str('INITIAL_SUPERUSER_USERNAME', default='admin'),
                email=env.str('INITIAL_SUPERUSER_EMAIL', default='admin@example.com'),
                password=env.str('INITIAL_SUPERUSER_PASSWORD', default='password'),
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created initial superuser '{env.str('INITIAL_SUPERUSER_USERNAME', default='admin')}'"
                )
            )

        groups = ['parent', 'child']

        for group_name in groups:
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created group '{group_name}'"))
            else:
                self.stdout.write(self.style.WARNING(f"Group '{group_name}' already exists"))

        self.stdout.write(self.style.SUCCESS('OwnIt setup completed successfully.'))
