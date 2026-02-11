"""Lightweight middleware wrappers to defer heavy third-party imports.

Modules referenced directly from `MIDDLEWARE` should avoid importing
their heavy dependencies at import time because Django's checks and the
autoreloader may import them on multiple threads and trigger import locks.

This module provides a lazy shim for the `allauth` AccountMiddleware that
only imports the real middleware implementation when the middleware is
actually instantiated/called.
"""

from typing import Callable


class LazyAccountMiddleware:
    """Proxy middleware that lazily imports `allauth.account.middleware.AccountMiddleware`.

    The shim is safe to import at startup and therefore can be referenced
    from `MIDDLEWARE` in Django settings without causing `allauth` to be
    imported during checks or by the autoreloader threads.
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response
        self._real = None

    def _load_real(self):
        if self._real is None:
            from allauth.account.middleware import AccountMiddleware as Real

            # Instantiate the real middleware with the same get_response
            self._real = Real(self.get_response)

    def __call__(self, request):
        self._load_real()
        return self._real(request)

    # Provide process_* hooks proxies in case the real middleware implements them
    def __getattr__(self, name):
        # Ensure real middleware is loaded then delegate attribute access
        self._load_real()
        return getattr(self._real, name)
