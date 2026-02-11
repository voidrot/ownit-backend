import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from apps.core import utils


User = get_user_model()


@pytest.mark.django_db
def test_is_member_true():
    user = User.objects.create_user(username="u1", password="pass")
    group = Group.objects.create(name="testgroup")
    user.groups.add(group)

    assert utils.is_member(user, "testgroup") is True


@pytest.mark.django_db
def test_is_member_false():
    user = User.objects.create_user(username="u2", password="pass")
    assert utils.is_member(user, "no-such-group") is False


@pytest.mark.django_db
def test_is_parent_and_is_child_helpers():
    parent = User.objects.create_user(username="parent_user", password="pass")
    child = User.objects.create_user(username="child_user", password="pass")

    parent_group = Group.objects.create(name="parent")
    child_group = Group.objects.create(name="child")

    parent.groups.add(parent_group)
    child.groups.add(child_group)

    assert utils.is_parent(parent) is True
    assert utils.is_parent(child) is False

    assert utils.is_child(child) is True
    assert utils.is_child(parent) is False
