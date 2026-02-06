import pytest


def test_smoke():
    assert 1 + 1 == 2


@pytest.mark.django_db
def test_admin_url(client):
    response = client.get('/admin/login/')
    assert response.status_code == 200
