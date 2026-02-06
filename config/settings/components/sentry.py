from config.settings.components.base import env
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=env.str('SENTRY_DSN', default=None),
    # Add data like request headers and IP for users;
    # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
    send_default_pii=True,
    integrations=[
        DjangoIntegration(
            transaction_style='function_name',
            middleware_spans=True,
            signals_spans=True,
            signals_denylist=[],
            cache_spans=True,
            http_methods_to_capture=(
                'CONNECT',
                'DELETE',
                'GET',
                'PATCH',
                'POST',
                'PUT',
                'TRACE',
            ),
        ),
    ],
)
