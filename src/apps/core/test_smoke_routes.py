import pytest
from django.urls import reverse


PUBLIC_ROUTES = (
    ('landing', '/'),
    ('health', '/health/'),
)

AUTHENTICATED_ROUTES = (
    ('dashboard', '/dashboard/'),
    ('projects', '/projects/'),
    ('requirements', '/requirements/'),
    ('testplans', '/test-plans/'),
    ('testcases', '/test-cases/'),
    ('executions', '/executions/'),
    ('defects', '/defects/'),
    ('incidents', '/incidents/'),
    ('traceability', '/traceability/'),
    ('reports', '/reports/'),
    ('notifications', '/notifications/'),
    ('audit', '/audit/'),
    ('phases', '/phases/'),
    ('users', '/profile/'),
)


@pytest.mark.django_db
def test_public_routes_render_without_server_error(client):
    for name, path in PUBLIC_ROUTES:
        response = client.get(path)
        assert response.status_code == 200, f'{name} returned {response.status_code}'


@pytest.mark.django_db
def test_protected_module_routes_require_authentication(client):
    for name, path in AUTHENTICATED_ROUTES:
        response = client.get(path)
        assert response.status_code == 302, f'{name} returned {response.status_code}'
        assert reverse('login') in response['Location'], f'{name} did not redirect to login'
