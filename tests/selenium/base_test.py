"""
Base reutilizable para pruebas funcionales automatizadas con Selenium 4.

Este modulo centraliza la inicializacion del navegador, las esperas explicitas,
las acciones comunes y la captura de screenshots. La separacion permite que los
casos de prueba sigan el enfoque ISTQB: precondiciones, pasos, resultado
esperado y evidencias.
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Iterable

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


BASE_URL = os.getenv("SELENIUM_BASE_URL", "http://127.0.0.1:8000/")
DEFAULT_TIMEOUT = int(os.getenv("SELENIUM_TIMEOUT", "10"))
SCREENSHOTS_DIR = Path(__file__).resolve().parent / "screenshots"


class SeleniumBaseTest:
    """Clase base para evitar duplicacion en las pruebas funcionales."""

    driver: WebDriver
    wait: WebDriverWait

    def setup_method(self) -> None:
        """Inicializa Chrome antes de cada prueba."""
        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")

        if os.getenv("SELENIUM_HEADLESS", "false").lower() == "true":
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--window-size=1366,768")

        # Selenium 4 usa Selenium Manager para localizar/descargar ChromeDriver
        # si no existe uno configurado en PATH.
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, DEFAULT_TIMEOUT)
        self.open_home()

    def teardown_method(self) -> None:
        """Cierra el navegador despues de cada prueba."""
        if os.getenv("SELENIUM_KEEP_OPEN", "false").lower() == "true":
            return

        if getattr(self, "driver", None):
            self.driver.quit()

    def open_home(self) -> None:
        self.driver.get(BASE_URL)

    def open_dashboard(self) -> None:
        self.open_path("/dashboard/")

    def open_path(self, path: str) -> None:
        self.driver.get(f"{BASE_URL.rstrip('/')}/{path.lstrip('/')}")

    def find_visible(self, locator: tuple[str, str]):
        return self.wait.until(EC.visibility_of_element_located(locator))

    def find_clickable(self, locator: tuple[str, str]):
        return self.wait.until(EC.element_to_be_clickable(locator))

    def click(self, locator: tuple[str, str]) -> None:
        self.find_clickable(locator).click()

    def type_text(self, locator: tuple[str, str], value: str) -> None:
        element = self.find_visible(locator)
        element.clear()
        element.send_keys(value)

    def wait_for_url_contains(self, text: str) -> None:
        self.wait.until(EC.url_contains(text))

    def wait_for_text(self, text: str) -> None:
        self.wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "body"), text))

    def wait_for_any_visible(self, locators: Iterable[tuple[str, str]]):
        last_error: Exception | None = None
        for locator in locators:
            try:
                return self.find_visible(locator)
            except TimeoutException as exc:
                last_error = exc
        raise TimeoutException(f"No se encontro ningun selector visible: {list(locators)}") from last_error

    def print_success(self, module_name: str, test_name: str) -> None:
        print(f"[OK] Prueba exitosa | Modulo validado: {module_name} | Caso: {test_name}")

    def print_error(self, module_name: str, test_name: str, error: Exception) -> None:
        print(f"[ERROR] Modulo: {module_name} | Caso: {test_name} | Error encontrado: {error}")

    def take_screenshot(self, test_name: str) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = SCREENSHOTS_DIR / f"{test_name}_{timestamp}.png"
        self.driver.save_screenshot(str(file_path))
        print(f"[EVIDENCIA] Screenshot generado: {file_path}")
        return file_path

    def login(self, email: str | None = None, password: str | None = None) -> None:
        """
        Login reutilizable.

        Reemplazar los selectores si el HTML real usa otros atributos. Se
        recomienda usar data-testid para pruebas estables, por ejemplo:
        data-testid="login-username".
        """
        email = email or os.getenv("SELENIUM_EMAIL") or os.getenv("SELENIUM_USERNAME", "qa@example.com")
        password = password or os.getenv("SELENIUM_PASSWORD", "Istqb2026.Temp!")

        self.open_path("/login/")
        self.type_text((By.NAME, "email"), email)
        self.type_text((By.NAME, "password"), password)
        self.click((By.CSS_SELECTOR, "button[type='submit'], input[type='submit']"))

        self.wait_for_url_contains("/dashboard/")
        self.wait_for_any_visible(
            [
                (By.CSS_SELECTOR, ".app-sidebar"),
                (By.CSS_SELECTOR, ".sidebar-nav"),
                (By.CSS_SELECTOR, ".app-content"),
            ]
        )

    def logout(self) -> None:
        """Cierre de sesion reutilizable con selectores genericos."""
        self.click((By.CSS_SELECTOR, ".user-menu, [data-testid='user-menu']"))
        self.click(
            (
                By.CSS_SELECTOR,
                "[data-testid='logout'], a[href*='logout'], .dropdown-menu a[href*='logout']",
            )
        )
        self.wait_for_any_visible(
            [
                (By.NAME, "username"),
                (By.NAME, "email"),
                (By.CSS_SELECTOR, "[data-testid='login-form']"),
                (By.CSS_SELECTOR, "form"),
            ]
        )
