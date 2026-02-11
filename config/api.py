from ninja import Redoc
from allauth.headless.contrib.ninja.security import XSessionTokenAuth
from ninja import NinjaAPI
from apps.behavior.api import router as behavior_router
from apps.chores.api import router as chores_router
from apps.users.api import router as users_router
from ninja.openapi.docs import DocsBase
# API Constants
API_TITLE = 'OwnIt API'
API_DESCRIPTION = 'API for the OwnIt app'
API_DOCS_TYPE = Redoc(settings={
    'disableDeepLinks': True,
    'hideTryItPanel': False,
    'showAccessModel': True,
})
# API_DOCS_TYPE = Swagger(
#     settings={
#         'deepLinking': True,
#         'displayOperationId': True,
#         'syntaxHighlight': {
#             'activated': True,
#             'theme': 'nord',
#         },
#         'tryItOutEnabled': True,
#         'requestSnippetsEnabled': True,
#         'persistAuthorization': True,
#     }
# )
### API v1

class XSessionAuth(XSessionTokenAuth):
    openapi_name = "X-Session-Token"
    openapi_description = "Authenticate using the X-Session-Token header provided by django-allauth's headless mode."


api_v1 = NinjaAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version='1.0.0',
    docs=API_DOCS_TYPE,
    auth=XSessionAuth()
)

api_v1.add_router('/behavior/', behavior_router)
api_v1.add_router('/chores/', chores_router)
api_v1.add_router('/users/', users_router)
