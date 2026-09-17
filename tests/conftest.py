"""Aislamiento de datos para las pruebas Selenium que usan un servidor HTTP separado."""

from __future__ import annotations

import pytest
from django.db import transaction

from tests.selenium.base_test import SeleniumBaseTest


_original_bootstrap_executable_case = SeleniumBaseTest._bootstrap_executable_case


def _bootstrap_and_commit(self):
    """Publica el fixture E2E antes de que Selenium consulte desde otra conexión."""
    case_id = _original_bootstrap_executable_case(self)
    transaction.commit()
    return case_id


SeleniumBaseTest._bootstrap_executable_case = _bootstrap_and_commit


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config, items):
    """Mantiene las pruebas Selenium en modo transaccional para permitir commits."""
    database_marker = pytest.mark.django_db(transaction=True)
    for item in items:
        path = str(getattr(item, "fspath", "")).replace("\\", "/")
        if "/tests/selenium/" in path:
            item.add_marker(database_marker)
