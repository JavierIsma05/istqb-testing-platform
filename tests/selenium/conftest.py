"""Configuracion pytest para evidencias y compatibilidad de pruebas Selenium."""

from __future__ import annotations

import pytest
from selenium.common.exceptions import WebDriverException, TimeoutException

from base_test import SeleniumBaseTest


def _set_date_robust(self, locator: tuple[str, str], value: str) -> None:
    """Asigna fechas aunque el campo pertenezca a un panel oculto del wizard."""
    elements = self.driver.find_elements(*locator)
    if not elements:
        raise TimeoutException(f"No se encontro el campo de fecha: {locator}")
    element = elements[0]
    self.driver.execute_script(
        "arguments[0].value = arguments[1]; "
        "arguments[0].dispatchEvent(new Event('input', {bubbles: true})); "
        "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
        element,
        value,
    )


SeleniumBaseTest.set_date = _set_date_robust


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
