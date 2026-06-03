"""Configuracion pytest para evidencias automaticas en fallos Selenium."""

from __future__ import annotations

import pytest


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Captura screenshot automatico cuando una prueba falla."""
    outcome = yield
    report = outcome.get_result()

    if report.when != "call" or not report.failed:
        return

    instance = getattr(item, "instance", None)
    if instance and hasattr(instance, "take_screenshot"):
        instance.take_screenshot(item.name)
