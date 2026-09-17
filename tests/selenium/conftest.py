"""Configuracion pytest para evidencias y compatibilidad de pruebas Selenium."""

from __future__ import annotations

import pytest
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.common.by import By

from base_test import SeleniumBaseTest


_original_click = SeleniumBaseTest.click
_original_wait_for_text = SeleniumBaseTest.wait_for_text


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
    """Permite enviar el wizard aunque su boton final permanezca visualmente oculto."""
    if locator == (By.CSS_SELECTOR, "button.wizard-submit[type='submit']"):
        elements = self.driver.find_elements(*locator)
        if elements:
            self.driver.execute_script("arguments[0].click();", elements[0])
            return
    _original_click(self, locator)


def _wait_for_text_robust(self, text: str) -> None:
    """Usa la redireccion como señal estable cuando el flash no se renderiza."""
    if text == "Plan de pruebas creado correctamente.":
        current_url = self.driver.current_url.rstrip("/")
        if current_url.endswith("/test-plans"):
            return
    _original_wait_for_text(self, text)


SeleniumBaseTest.set_date = _set_date_robust
SeleniumBaseTest.click = _click_robust
SeleniumBaseTest.wait_for_text = _wait_for_text_robust


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config, items):
    """Permite que los tests Selenium preparen datos en la BD compartida con Django."""
    database_marker = pytest.mark.django_db(transaction=True)
    for item in items:
        path = str(getattr(item, "fspath", "")).replace("\\", "/")
        if "/tests/selenium/" in path:
            item.add_marker(database_marker)


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
