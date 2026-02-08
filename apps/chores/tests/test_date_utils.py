from datetime import date, datetime, timezone, time

from apps.chores import utils


def test_get_age_from_birth_date_today():
    today = date.today()
    assert utils.get_age_from_birth_date(today) == 0


def test_get_age_from_birth_date_birthday_passed():
    today = date.today()
    # Person born exactly 25 years ago today -> age 25
    bd = date(today.year - 25, today.month, today.day)
    assert utils.get_age_from_birth_date(bd) == 25


def test_get_age_from_birth_date_birthday_not_yet():
    today = date.today()
    # Construct a birthday that occurs later this year than today
    if today.day < 28:
        bd_day = today.day + 1
        bd_month = today.month
    else:
        bd_day = 1
        bd_month = (today.month % 12) + 1

    bd = date(today.year - 40, bd_month, bd_day)
    # Since birthday hasn't occurred yet this year, age should be 39
    assert utils.get_age_from_birth_date(bd) == 39


def test_get_end_of_day_datetime_properties():
    now = datetime.now(timezone.utc)
    eod = utils.get_end_of_day_datetime()

    assert isinstance(eod, datetime)
    # Should be timezone-aware UTC
    assert eod.tzinfo == timezone.utc
    # Should be for today's date (using UTC)
    assert eod.date() == now.date()
    # Time component should equal datetime.max.time()
    assert eod.time() == datetime.max.time()


def test_get_age_from_birth_date_feb29(monkeypatch):
    # Born on Feb 29, 1988. On a non-leap-year Feb 28 the age should be one less
    birth = date(1988, 2, 29)

    class FakeDate:
        @classmethod
        def today(cls):
            return date(2021, 2, 28)

    monkeypatch.setattr(utils, 'date', FakeDate)
    assert utils.get_age_from_birth_date(birth) == 32

    class FakeDateMar1:
        @classmethod
        def today(cls):
            return date(2021, 3, 1)

    monkeypatch.setattr(utils, 'date', FakeDateMar1)
    assert utils.get_age_from_birth_date(birth) == 33


def test_get_end_of_day_datetime_deterministic(monkeypatch):
    # Freeze "now" to a deterministic UTC datetime and verify end-of-day
    fixed_now = datetime(2026, 2, 8, 10, 15, 30, tzinfo=timezone.utc)

    # Create a FakeDatetime with the minimal interface used by utils
    class FakeDatetime:
        max = datetime.max

        @classmethod
        def now(cls, tz=None):
            return fixed_now

        @classmethod
        def combine(cls, d, t, tzinfo=None):
            return datetime.combine(d, t, tzinfo=tzinfo)

    monkeypatch.setattr(utils, 'datetime', FakeDatetime)

    eod = utils.get_end_of_day_datetime()
    expected = datetime.combine(fixed_now.date(), datetime.max.time(), tzinfo=timezone.utc)
    assert eod == expected


def test_get_due_date_from_time_due_none(monkeypatch):
    # Freeze now to a deterministic UTC datetime and verify that None -> end of day
    fixed_now = datetime(2026, 2, 8, 10, 15, 30, tzinfo=timezone.utc)

    class FakeDatetime:
        max = datetime.max

        @classmethod
        def now(cls, tz=None):
            return fixed_now

        @classmethod
        def combine(cls, d, t, tzinfo=None):
            return datetime.combine(d, t, tzinfo=tzinfo)

    monkeypatch.setattr(utils, 'datetime', FakeDatetime)

    due = utils.get_due_date_from_time_due(None)
    expected = datetime.combine(fixed_now.date(), datetime.max.time(), tzinfo=timezone.utc)
    assert due == expected


def test_get_due_date_from_time_due_with_time(monkeypatch):
    # Freeze now and verify combining today's date with provided time
    fixed_now = datetime(2026, 2, 8, 10, 15, 30, tzinfo=timezone.utc)

    class FakeDatetime:
        @classmethod
        def now(cls, tz=None):
            return fixed_now

        @classmethod
        def combine(cls, d, t, tzinfo=None):
            return datetime.combine(d, t, tzinfo=tzinfo)

    monkeypatch.setattr(utils, 'datetime', FakeDatetime)

    t = time(15, 30)
    due = utils.get_due_date_from_time_due(t)
    expected = datetime.combine(fixed_now.date(), t, tzinfo=timezone.utc)
    assert due == expected
    assert due.tzinfo == timezone.utc
