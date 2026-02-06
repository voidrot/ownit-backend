from os import environ
from split_settings.tools import include, optional

ENV = environ.get('DJANGO_ENV', 'development')

base_settings = [
    'components/*.py',
    f'envs/{ENV}.py',
    optional('envs/local.py'),
]

include(*base_settings)
