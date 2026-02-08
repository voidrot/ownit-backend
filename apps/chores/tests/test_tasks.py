import pytest
from datetime import datetime, timezone, timedelta, time as dt_time, date
from unittest.mock import patch

from django.contrib.auth.models import Group

from apps.chores.models import Chore, Assignment
import apps.chores.tasks as tasks
from apps.chores.utils import get_due_date_from_time_due
from apps.users.models import User
from django.db import IntegrityError

pytestmark = pytest.mark.django_db


@pytest.fixture()
def child_group(db):
    grp, _ = Group.objects.get_or_create(name="child")
    return grp


@pytest.fixture()
def create_child(child_group):
    def _create(username: str, birth_date: date = None) -> User:
        user = User.objects.create_user(username=username, password="pass")
        if birth_date:
            user.birth_date = birth_date
            user.save()
        user.groups.add(child_group)
        return user

    return _create


def test_assign_to_all_skips_duplicate_same_day(child_group, create_child):
    child = create_child("c1")

    chore = Chore.objects.create(name="all-chore", assign_to_all=True, disabled=False, is_recurring=False)
    due_date = get_due_date_from_time_due(chore.time_due)

    # Create an existing assignment for today
    Assignment.objects.create(chore=chore, assigned_to=child, due_date=due_date)

    # Run the task synchronously
    tasks.assign_chores.run()

    # Check that we still only have one assignment for this chore+child on that UTC day
    day_start = datetime(due_date.year, due_date.month, due_date.day, tzinfo=timezone.utc)
    day_end = day_start + timedelta(days=1)
    count = (
        Assignment.objects.filter(
            chore=chore, assigned_to=child, due_date__gte=day_start, due_date__lt=day_end
        ).count()
    )
    assert count == 1


def test_previous_day_completed_counts_influence_weights(create_child):
    child1 = create_child("child1")
    child2 = create_child("child2")

    # Build prev day range consistent with task implementation
    today = datetime.now(timezone.utc).date()
    prev_day = today - timedelta(days=1)
    prev_start = datetime(prev_day.year, prev_day.month, prev_day.day, tzinfo=timezone.utc)
    # Place completed_at safely within previous UTC day range
    completed_at = prev_start + timedelta(hours=2)

    # Create an assignment completed yesterday for child1
    Assignment.objects.create(
        chore=Chore.objects.create(name="prev-chore", disabled=False, is_recurring=False),
        assigned_to=child1,
        due_date=prev_start,
        is_completed=True,
        completed_at=completed_at,
    )

    # Create a new chore that should be assigned today (non-recurring)
    new_chore = Chore.objects.create(name="new-chore", assign_to_all=False, disabled=False, is_recurring=False)

    # Use monkeypatch-style replacement of random.choices via patch context
    def fake_choices(candidates, weights, k):
        # Expect two candidates and weight for child1 < weight for child2
        assert len(candidates) == 2
        assert weights[0] < weights[1]
        return [candidates[1]]

    with patch("apps.chores.tasks.random.choices", side_effect=fake_choices):
        tasks.assign_chores.run()

    # Verify an assignment was created for new_chore and assigned to child2
    due_date = get_due_date_from_time_due(new_chore.time_due)
    day_start = datetime(due_date.year, due_date.month, due_date.day, tzinfo=timezone.utc)
    day_end = day_start + timedelta(days=1)
    assigned = Assignment.objects.filter(chore=new_chore, due_date__gte=day_start, due_date__lt=day_end)
    assert assigned.count() == 1
    assert assigned.first().assigned_to.id == child2.id


def test_assign_to_all_assigns_to_every_child(child_group, create_child):
    u1 = create_child("child1")
    u2 = create_child("child2")

    chore = Chore.objects.create(name="all-chore", assign_to_all=True, disabled=False, is_recurring=False)

    # run the task
    tasks.assign_chores.run()

    assigns = Assignment.objects.filter(chore=chore)
    assert assigns.count() == 2
    assignees = {a.assigned_to.username for a in assigns}
    assert assignees == {"child1", "child2"}


def test_chore_age_restricted_requires_minimum_age():
    # The model enforces that if age_restricted is True then minimum_age must be set.
    with pytest.raises(IntegrityError):
        Chore.objects.create(
            name="bad-restricted", age_restricted=True, minimum_age=None, disabled=False, is_recurring=False
        )


def test_age_restricted_assigns_only_eligible_and_sets_due_date(create_child):
    older = create_child("older", birth_date=date(2005, 1, 1))
    younger = create_child("younger", birth_date=date(2018, 1, 1))

    # chore restricted to >=16
    chore = Chore.objects.create(
        name="age-chore", age_restricted=True, minimum_age=16, disabled=False, time_due=dt_time(15, 30), is_recurring=False
    )

    tasks.assign_chores.run()

    assigns = Assignment.objects.filter(chore=chore)
    # Only the older child should be eligible and receive the assignment
    assert assigns.count() == 1
    a = assigns.first()
    assert a.assigned_to.username == "older"
    # due_date should have the chore's time component (timezone-aware)
    assert a.due_date.time() == dt_time(15, 30)
    assert a.due_date.tzinfo == timezone.utc


def test_weekly_and_monthly_recurrence_filters(create_child):
    child = create_child("wchild")

    today = datetime.now(timezone.utc).date()
    tomorrow = today + timedelta(days=1)
    tomorrow_weekday = tomorrow.strftime('%A')

    # Weekly chore scheduled for tomorrow should NOT be assigned today
    weekly_chore = Chore.objects.create(
        name='weekly-chore', recurrence=Chore.WEEKLY, recurrence_day_of_week=tomorrow_weekday, assign_to_all=True, disabled=False, is_recurring=True
    )

    tasks.assign_chores.run()
    assigns = Assignment.objects.filter(chore=weekly_chore)
    assert assigns.count() == 0

    # Monthly chore scheduled for a different day should NOT be assigned
    wrong_day = (today.day % 28) + 1  # a different day within month
    monthly_chore = Chore.objects.create(
        name='monthly-chore', recurrence=Chore.MONTHLY, recurrence_day_of_month=str(wrong_day), assign_to_all=True, disabled=False, is_recurring=True
    )
    tasks.assign_chores.run()
    assigns = Assignment.objects.filter(chore=monthly_chore)
    assert assigns.count() == 0

    # Monthly chore scheduled for today SHOULD be assigned
    monthly_chore_ok = Chore.objects.create(
        name='monthly-ok', recurrence=Chore.MONTHLY, recurrence_day_of_month=str(today.day), assign_to_all=True, disabled=False, is_recurring=True
    )
    tasks.assign_chores.run()
    assigns = Assignment.objects.filter(chore=monthly_chore_ok)
    assert assigns.count() == 1


def test_previous_day_completed_boundary_behavior(create_child):
    c1 = create_child('edge1')
    c2 = create_child('edge2')

    today = datetime.now(timezone.utc).date()
    prev_day = today - timedelta(days=1)
    prev_start = datetime(prev_day.year, prev_day.month, prev_day.day, tzinfo=timezone.utc)
    prev_end = prev_start + timedelta(days=1)

    # completed_at just before prev_end should be counted
    completed_just_before = prev_end - timedelta(seconds=1)
    Assignment.objects.create(
        chore=Chore.objects.create(name='edge-prev', disabled=False, is_recurring=False),
        assigned_to=c1,
        due_date=prev_start,
        is_completed=True,
        completed_at=completed_just_before,
    )

    # Verify DB range query includes the just-before timestamp
    counted_before = Assignment.objects.filter(
        is_completed=True, completed_at__gte=prev_start, completed_at__lt=prev_end, assigned_to=c1
    ).count()
    assert counted_before == 1

    # Now create a completion exactly at prev_end (start of today) which should NOT be counted
    Assignment.objects.create(
        chore=Chore.objects.create(name='edge-prev2', disabled=False, is_recurring=False),
        assigned_to=c1,
        due_date=prev_start,
        is_completed=True,
        completed_at=prev_end,  # exactly at boundary -> should be excluded
    )

    counted_after = Assignment.objects.filter(
        is_completed=True, completed_at__gte=prev_start, completed_at__lt=prev_end, assigned_to=c1
    ).count()
    assert counted_after == 1
