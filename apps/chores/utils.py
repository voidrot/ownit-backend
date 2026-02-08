from datetime import time
from datetime import timezone
from datetime import datetime
from datetime import date
from django.db.models import Q
from apps.chores.models import Chore


def get_age_from_birth_date(birth_date) -> int:
    """Return age in years for the given birth date."""
    today = date.today()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return age


def get_end_of_day_datetime() -> datetime:
    """Return today's end-of-day datetime in UTC."""
    now = datetime.now(timezone.utc)
    end_of_day = datetime.combine(now.date(), datetime.max.time(), tzinfo=timezone.utc)
    return end_of_day


def get_due_date_from_time_due(time_due: time | None) -> datetime:
    """Return today's due datetime in UTC for the given time or end-of-day if None."""
    if time_due is None:
        # If no time_due is provided, default to end of day
        return get_end_of_day_datetime()
    now = datetime.now(timezone.utc)
    due_date = datetime.combine(now.date(), time_due, tzinfo=timezone.utc)
    return due_date


def chore_runs_today_q(today: date | None = None) -> Q:
    """Return a Django Q object selecting chores that should run on `today`.

    This centralizes the recurrence logic so callers can re-use a single
    implementation when filtering QuerySets.
    """
    if today is None:
        today = datetime.now(timezone.utc).date()
    weekday = today.strftime("%A")
    day_of_month = str(today.day)

    return (
        Q(is_recurring=False)
        | Q(recurrence=Chore.DAILY)
        | (Q(recurrence=Chore.WEEKLY) & Q(recurrence_day_of_week__iexact=weekday))
        | (Q(recurrence=Chore.MONTHLY) & Q(recurrence_day_of_month=day_of_month))
    )


def chore_runs_today(chore: Chore, today: date | None = None) -> bool:
    """Return True if the provided `chore` should run on `today`.

    This is a pure-Python helper useful for unit tests and programmatic checks
    without hitting the database.
    """
    if today is None:
        today = datetime.now(timezone.utc).date()
    if not chore.is_recurring:
        return True
    if chore.recurrence == Chore.DAILY:
        return True
    if chore.recurrence == Chore.WEEKLY:
        return (chore.recurrence_day_of_week or '').strip().lower() == today.strftime('%A').lower()
    if chore.recurrence == Chore.MONTHLY:
        return (chore.recurrence_day_of_month or '').strip() == str(today.day)
    return False
