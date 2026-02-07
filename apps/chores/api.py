from ninja import Router
from apps.chores.models import Location

router = Router()


@router.get('/location')
def get_location(request):
    """Get all chore locations."""

    locations = Location.objects.all()
    return [location.name for location in locations]
