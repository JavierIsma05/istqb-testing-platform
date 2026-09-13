"""Configuracion pytest para evidencias automaticas en fallos Selenium."""

from __future__ import annotations

import pytest
from selenium.common.exceptions import WebDriverException


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Captura una evidencia si Selenium sigue disponible cuando falla una prueba."""
    outcome = yield
    report = outcome.get_result()

    if report.when != "call" or not report.failed:
        return

    instance = getattr(item, "instance", None)
    screenshot = getattr(instance, "take_screenshot", None)

    if not callable(screenshot):
        return

    try:
        screenshot(item.name)
    except WebDriverException:
        # La evidencia nunca debe convertir un fallo de prueba en un INTERNALERROR
        # cuando Chrome o la ventana ya fueron cerrados.
        return
