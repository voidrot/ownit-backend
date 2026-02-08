from django.db.models import Q
from config.celery import app
from datetime import datetime, timezone
from apps.chores.models import Assignment
import logging

logger = logging.getLogger(__name__)


@app.task
def close_days_chores() -> None:
    """Close all open, incomplete assignments.

    Marks assignments with closed=False and closed_at=None as closed and sets
    closed_at to the current UTC time.
    """
    logger.info('Closing incomplete chores (excluding assignments with future due_date)...')
    now = datetime.now(timezone.utc)
    # Only close assignments that are open and either have no due_date or whose
    # due_date is in the past or now. This prevents closing chores scheduled
    # for future dates accidentally.
    open_chores = (
        Assignment.objects.filter(closed=False, closed_at=None)
        .filter(Q(due_date__lte=now) | Q(due_date__isnull=True))
        .update(closed=True, closed_at=now)
    )
    # TODO: We probably want to create a report of which chores were closed each time this runs, and log it somewhere.
    logger.info(f'Closed {open_chores} chores.')
