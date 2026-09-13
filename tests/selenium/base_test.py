"""
Base reutilizable para pruebas funcionales automatizadas con Selenium 4.

Este modulo centraliza la inicializacion del navegador, las esperas explicitas,
las acciones comunes y la captura de screenshots. La separacion permite que los
casos de prueba sigan el enfoque ISTQB: precondiciones, pasos, resultado
esperado y evidencias.
"""

from __future__ import annotations

import os
import time
from datetime import datetime
from pathlib import Path
from typing import Iterable

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
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

    def scroll_into_view(self, locator: tuple[str, str]):
        element = self.find_clickable(locator)
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        return element

    def type_text(self, locator: tuple[str, str], value: str) -> None:
        element = self.find_visible(locator)
        element.clear()
        element.send_keys(value)

    def set_date(self, locator: tuple[str, str], value: str) -> None:
        """Asigna un valor a un input type=date via JS."""
        element = self.find_visible(locator)
        self.driver.execute_script(
            "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles: true})); arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
            element,
            value,
        )

    def select_option(self, locator: tuple[str, str], value: str) -> None:
        Select(self.find_visible(locator)).select_by_value(value)

    def select_first_available_option(self, locator: tuple[str, str]) -> str:
        """Selecciona la primera opción real disponible, sin depender de IDs fijos."""
        select = Select(self.find_visible(locator))
        for option in select.options:
            value = option.get_attribute("value")
            if value and option.is_enabled():
                select.select_by_value(value)
                return value
        raise TimeoutException(f"No hay opciones disponibles para: {locator}")

    def ensure_project(self) -> str:
        """Garantiza un proyecto visible para las pruebas E2E."""
        self.open_path("/requirements/new/")
        project_select = Select(self.find_visible((By.NAME, "project")))
        for option in project_select.options:
            value = option.get_attribute("value")
            if value:
                project_select.select_by_value(value)
                return value

        year = datetime.now().year
        self.open_path("/projects/new/")
        self.type_text((By.NAME, "name"), f"Proyecto E2E {int(time.time())}")
        self.type_text((By.NAME, "description"), "Proyecto auxiliar para pruebas funcionales automatizadas.")
        self.set_date((By.NAME, "start_date"), f"{year}-01-01")
        self.set_date((By.NAME, "end_date"), f"{year}-12-31")
        self.click((By.CSS_SELECTOR, "button[type='submit'], input[type='submit']"))
        self.wait_for_url_contains("/projects/")

        self.open_path("/requirements/new/")
        return self.select_first_available_option((By.NAME, "project"))

    def ensure_requirement(self) -> str:
        """Crea un requisito si el proyecto visible no tiene uno utilizable."""
        project_id = self.ensure_project()
        self.select_option((By.NAME, "project"), project_id)
        title = f"REQ-E2E-{int(time.time())} Requisito funcional"
        self.type_text((By.NAME, "title"), title)
        self.type_text((By.NAME, "description"), "El sistema debe permitir validar una funcionalidad del proyecto.")
        if self.driver.find_elements(By.NAME, "acceptance_criteria"):
            self.type_text((By.NAME, "acceptance_criteria"), "La funcionalidad cumple el comportamiento esperado.")
        self.select_option((By.NAME, "requirement_type"), "FUNCTIONAL")
        self.select_option((By.NAME, "priority"), "HIGH")
        self.click((By.CSS_SELECTOR, "button[type='submit'], input[type='submit']"))
        self.wait_for_text("Requisito creado correctamente.")
        self.open_path(f"/requirements/?project={project_id}")

        for link in self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/requirements/']"):
            href = link.get_attribute("href") or ""
            if "/edit/" in href:
                continue
            parts = href.rstrip("/").split("/")
            if parts and parts[-1].isdigit():
                return parts[-1]
        raise TimeoutException("No se pudo identificar el requisito creado.")

    def ensure_test_case(self) -> str:
        """Garantiza un caso de prueba siguiendo la cadena proyecto -> requisito -> plan -> caso."""
        self.open_path("/executions/")
        for option in self.driver.find_elements(By.CSS_SELECTOR, "select[name='test_case'] option"):
            value = option.get_attribute("value")
            if value:
                return value

        self.ensure_requirement()
        self.open_path("/testplans/new/")
        self.select_first_available_option((By.NAME, "project"))
        year = datetime.now().year
        values = {
            "name": f"Plan E2E {int(time.time())}",
            "version": "1.0",
            "description": "Plan auxiliar para pruebas funcionales automatizadas.",
            "scope": "Validacion funcional de la cadena E2E.",
            "objective": "Verificar la trazabilidad completa desde requisito hasta ejecucion.",
            "strategy": "Pruebas funcionales manuales.",
            "entry_criteria": "Requisito registrado y disponible.",
            "exit_criteria": "Ejecucion registrada con evidencia.",
            "resources": "Selenium y ambiente local.",
            "environment": "Chrome y servidor local.",
            "responsibilities": "Responsable de pruebas E2E.",
            "estimation": "1 hora.",
            "minimum_pass_percentage": "80",
            "maximum_critical_defects": "0",
            "minimum_coverage_percentage": "90",
        }
        for name, value in values.items():
            if self.driver.find_elements(By.NAME, name):
                self.type_text((By.NAME, name), value)
        if self.driver.find_elements(By.NAME, "start_date"):
            self.set_date((By.NAME, "start_date"), f"{year}-01-01")
        if self.driver.find_elements(By.NAME, "end_date"):
            self.set_date((By.NAME, "end_date"), f"{year}-12-31")
        self.click((By.CSS_SELECTOR, "button[type='submit'], input[type='submit']"))
        self.wait_for_text("Plan de pruebas creado correctamente.")

        self.open_path("/test-cases/")
        self.click((By.CSS_SELECTOR, "[data-bs-target='#testCaseModal']"))
        self.find_visible((By.ID, "testCaseModal"))
        self.select_first_available_option((By.NAME, "requirement"))
        self.type_text((By.NAME, "title"), f"Caso E2E {int(time.time())}")
        self.type_text((By.NAME, "description"), "Caso auxiliar para pruebas funcionales automatizadas.")
        self.select_option((By.NAME, "priority"), "HIGH")
        self.select_option((By.NAME, "technique"), "EQUIVALENCE")
        for name, value in {"preconditions": "Usuario registrado y activo.", "test_data": "Datos de prueba E2E.", "steps": "1. Abrir la funcionalidad\n2. Ejecutar la acción principal", "expected_result": "La funcionalidad responde correctamente."}.items():
            self.type_text((By.NAME, name), value)
        if self.driver.find_elements(By.NAME, "level"):
            self.select_first_available_option((By.NAME, "level"))
        if self.driver.find_elements(By.NAME, "execution_type"):
            self.select_first_available_option((By.NAME, "execution_type"))
        if self.driver.find_elements(By.NAME, "version"):
            self.type_text((By.NAME, "version"), "1.0")
        submit = self.find_clickable((By.CSS_SELECTOR, "#testCaseModal button[type='submit']"))
        self.driver.execute_script("arguments[0].click();", submit)
        self.wait_for_text("Caso de prueba creado correctamente.")

        self.open_path("/executions/")
        return self.select_first_available_option((By.NAME, "test_case"))

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
        email = email or os.getenv("SELENIUM_EMAIL") or os.getenv("SELENIUM_USERNAME", "qa@example.com")
        password = password or os.getenv("SELENIUM_PASSWORD", "Istqb2026.Temp!")
        self.open_path("/login/")
        self.type_text((By.NAME, "email"), email)
        self.type_text((By.NAME, "password"), password)
        self.click((By.CSS_SELECTOR, "button[type='submit'], input[type='submit']"))
        self.wait_for_url_contains("/dashboard/")
        self.wait_for_any_visible(
            [(By.CSS_SELECTOR, ".app-sidebar"), (By.CSS_SELECTOR, ".sidebar-nav"), (By.CSS_SELECTOR, ".app-content")]
        )

    def logout(self) -> None:
        self.click((By.CSS_SELECTOR, ".user-menu, [data-testid='user-menu']"))
        self.click((By.CSS_SELECTOR, "[data-testid='logout'], a[href*='logout'], .dropdown-menu a[href*='logout']"))
        self.wait_for_any_visible(
            [(By.NAME, "username"), (By.NAME, "email"), (By.CSS_SELECTOR, "[data-testid='login-form']"), (By.CSS_SELECTOR, "form")]
        )
