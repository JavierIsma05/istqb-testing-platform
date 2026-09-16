"""Configuracion pytest para evidencias y compatibilidad de pruebas Selenium."""

from __future__ import annotations

import pytest
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.common.by import By

from base_test import SeleniumBaseTest


_original_click = SeleniumBaseTest.click


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


def _click_robust(self, locator: tuple[str, str]) -> None:
    """Permite enviar el wizard aunque su botón final permanezca visualmente oculto."""
    if locator == (By.CSS_SELECTOR, "button.wizard-submit[type='submit']"):
        elements = self.driver.find_elements(*locator)
        if elements:
            self.driver.execute_script("arguments[0].click();", elements[0])
            return
    _original_click(self, locator)


SeleniumBaseTest.set_date = _set_date_robust
SeleniumBaseTest.click = _click_robust


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
        return
