import os

# Allow synchronous Django DB operations even if an async loop is running
# This is often needed when combining pytest-django and pytest-playwright
os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'
