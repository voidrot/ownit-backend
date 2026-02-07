import pytest
from django.contrib.auth.models import Group


@pytest.mark.django_db
def test_headless_session_includes_groups(client, django_user_model) -> None:
    """
    Ensure the headless session response includes group names in user payload.
    """
    # Create a user and group, then authenticate for the browser session.
    group = Group.objects.create(name='parent')
    user = django_user_model.objects.create_user(username='groupuser', password='password')
    user.groups.add(group)
    client.force_login(user)

    response = client.get('/_allauth/browser/v1/auth/session')
    assert response.status_code == 200

    payload = response.json()
    user_data = payload['data']['user']
    assert 'groups' in user_data
    assert 'parent' in user_data['groups']
