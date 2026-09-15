import pytest
from django.conf import settings


@pytest.mark.django_db
def test_browser_security_baseline_is_enabled():
    assert settings.CSRF_COOKIE_HTTPONLY is True
    assert settings.CSRF_COOKIE_SAMESITE == 'Lax'
    assert settings.SESSION_COOKIE_HTTPONLY is True
    assert settings.SESSION_COOKIE_SAMESITE == 'Lax'
    assert settings.X_FRAME_OPTIONS == 'DENY'
    assert settings.SECURE_CONTENT_TYPE_NOSNIFF is True
    assert settings.SECURE_REFERRER_POLICY == 'strict-origin-when-cross-origin'
    assert settings.SECURE_CROSS_ORIGIN_OPENER_POLICY == 'same-origin'


@pytest.mark.django_db
def test_upload_limits_are_bounded():
    assert settings.DATA_UPLOAD_MAX_MEMORY_SIZE == 12 * 1024 * 1024
    assert settings.FILE_UPLOAD_MAX_MEMORY_SIZE == 12 * 1024 * 1024
