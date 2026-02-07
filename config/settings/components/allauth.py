from config.settings.components.base import DEBUG

# django-allauth config
ACCOUNT_LOGIN_METHODS = {'email', 'username'}
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_SIGNUP_FIELDS = [
    'email*',
    'username*',
    'password1*',
]
# Note: * denotes required field
LOGIN_REDIRECT_URL = '/'

HEADLESS_ONLY = False
HEADLESS_SERVE_SPECIFICATION = DEBUG

# django-allauth headless adapter
HEADLESS_ADAPTER = 'apps.users.headless_adapter.GroupAwareHeadlessAdapter'
