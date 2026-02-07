from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from ninja import NinjaAPI
from apps.behavior.api import router as behavior_router
from apps.chores.api import router as chores_router
from allauth.headless.contrib.ninja.security import x_session_token_auth

api = NinjaAPI()

api.add_router('/behavior/', behavior_router, auth=x_session_token_auth)
api.add_router('/chores/', chores_router, auth=x_session_token_auth)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('_allauth/', include('allauth.headless.urls')),
    path('', include('apps.pages.urls')),
    path('portal/', include('apps.core.urls')),
    path('api/', api.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    import debug_toolbar

    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
