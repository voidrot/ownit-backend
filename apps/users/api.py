from django.http import HttpRequest
from datetime import date
from pprint import pprint
from apps.users.models import User
from apps.core.utils import is_child
from apps.core.utils import is_parent
from apps.core.api_schema import AuthErrorSchema
from ninja import Router, Schema

router = Router(tags=["Users"])

class GetChildrenSchema(Schema):
    id: int
    first_name: str
    last_name: str
    email: str
    birth_date: date


@router.get('/children', response={200: list[GetChildrenSchema], 403: AuthErrorSchema})
def get_children(request):
    """Get all children."""
    user: User = request.auth
    if not is_parent(user):
        return 403, {"message": "Unauthorized"}
    children = User.objects.filter(groups__name="child", is_active=True)
    return [GetChildrenSchema.from_orm(child) for child in children]
