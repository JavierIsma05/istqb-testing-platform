"""
Base reutilizable para pruebas funcionales automatizadas con Selenium 4.

Este modulo centraliza la inicializacion del navegador, las esperas explicitas,
las acciones comunes y la captura de screenshots. La separacion permite que los
casos de prueba sigan el enfoque ISTQB: precondiciones, pasos, resultado
esperado y evidencias.
"""

from __future__ import annotations

import json
import os
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable

from django.contrib.auth import get_user_model
from django.utils import timezone
from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.remote.webdriver import WebDriver

from apps.projects.models import Project
from apps.requirements.models import Requirement
from apps.testplans.models import TestPlan
from apps.testcases.models import TestCase

BASE_URL = os.getenv("SELENIUM_BASE_URL", "http://127.0.0.1:8000/")
DEFAULT_TIMEOUT = int(os.getenv("SELENIUM_TIMEOUT", "15"))
SCREENSHOTS_DIR = Path(__file__).resolve().parent / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)


class SeleniumBaseTest:
    def setup_method(self) -> None:
        chrome_options = webdriver.ChromeOptions()
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
        def visible_and_enabled(driver: WebDriver):
            for element in driver.find_elements(*locator):
                try:
                    if element.is_displayed() and element.is_enabled():
                        return element
                except Exception:
                    continue
            return False
        return self.wait.until(visible_and_enabled)

    def click(self, locator: tuple[str, str]) -> None:
        element = self.find_clickable(locator)
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", element)
        try:
            element.click()
        except ElementClickInterceptedException:
            self.driver.execute_script("arguments[0].click();", element)

    def scroll_into_view(self, locator: tuple[str, str]):
        element = self.find_clickable(locator)
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        return element

    def type_text(self, locator: tuple[str, str], value: str) -> None:
        element = self.find_visible(locator)
        element.clear()
        element.send_keys(value)

    def set_date(self, locator: tuple[str, str], value: str) -> None:
        element = self.find_visible(locator)
        self.driver.execute_script(
            "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles: true})); arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
            element,
            value,
        )

    def select_option(self, locator: tuple[str, str], value: str) -> None:
        Select(self.find_visible(locator)).select_by_value(value)

    def select_first_available_option(self, locator: tuple[str, str]) -> str:
        select = Select(self.find_visible(locator))
        for option in select.options:
            value = option.get_attribute("value")
            if value and option.is_enabled():
                select.select_by_value(value)
                return value
        raise TimeoutException(f"No hay opciones disponibles para: {locator}")

    def _require_form(self, locator: tuple[str, str], form_name: str):
        elements = self.driver.find_elements(*locator)
        for element in elements:
            if element.is_displayed():
                return element
        url = self.driver.current_url
        body = self.driver.find_element(By.TAG_NAME, "body").text.strip().replace("\n", " | ")
        body = body[:700] if body else "<sin contenido visible>"
        raise TimeoutException(f"No se renderizo el formulario '{form_name}'. URL actual: {url}. Contenido visible: {body}")

    def _bootstrap_executable_case(self) -> str:
        """Crea un conjunto E2E aislado y fuerza el usuario QA al rol estudiante."""
        User = get_user_model()
        email = os.getenv("SELENIUM_EMAIL", "qa@example.com")
        password = os.getenv("SELENIUM_PASSWORD", "Istqb2026.Temp!")
        user = User.objects.filter(email=email).first()
        if user is None:
            user = User.objects.create_user(email=email, password=password, first_name="QA", last_name="Automation")
        user.first_name = "QA"
        user.last_name = "Automation"
        if hasattr(User, "Roles"):
            user.role = User.Roles.STUDENT
        user.is_active = True
        user.set_password(password)
        user.save(update_fields=["first_name", "last_name", "role", "is_active", "password"])

        suffix = str(time.time_ns())[-10:]
        today = timezone.localdate()
        project = Project.objects.create(
            code=f"E2E-{suffix}", name=f"Proyecto E2E Selenium {suffix}",
            description="Proyecto auxiliar aislado para pruebas funcionales automatizadas.",
            status=Project.Status.ACTIVE, start_date=today.replace(month=1, day=1),
            end_date=today.replace(month=12, day=31), created_by=user, tutor=user,
        )
        project.members.add(user)

        requirement = Requirement.objects.create(
            project=project, code=f"REQ-{suffix}",
            title="Requisito E2E Selenium",
            description="El sistema permite registrar una prueba funcional.",
            acceptance_criteria="La prueba puede ejecutarse correctamente.",
            priority=Requirement.Priority.HIGH, status=Requirement.Status.APPROVED,
            created_by=user,
        )

        plan = TestPlan.objects.create(
            project=project, name=f"Plan E2E Selenium {suffix}", version="1.0",
            description="Plan auxiliar para Selenium.",
            objective="Validar el registro funcional de pruebas.", scope="Flujo E2E.",
            strategy="Pruebas funcionales manuales.", environment="Chrome",
            responsibilities="QA Automation", estimation="1 hora",
            start_date=project.start_date, end_date=project.end_date, created_by=user,
        )

        case = TestCase.objects.create(
            test_plan=plan, code=f"TC-{suffix}", requirement=requirement,
            title="Caso E2E Selenium", description="Caso auxiliar para pruebas Selenium.",
            technique=TestCase.Technique.EQUIVALENCE, level=TestCase.Level.SYSTEM,
            preconditions="Usuario registrado.", test_data="Datos E2E.",
            steps="Abrir funcionalidad => Se muestra correctamente",
            steps_data=[{"number": 1, "action": "Abrir funcionalidad", "expected_result": "Se muestra correctamente"}],
            expected_result="Se muestra correctamente.", priority=TestCase.Priority.HIGH,
            status=TestCase.Status.READY, created_by=user,
        )
        return str(case.pk)

    def ensure_test_case(self) -> str:
        """Usa el caso persistente de CI para que Selenium y Django compartan la misma BD.

        En ejecuciones locales sin datos preparados conserva el bootstrap aislado como
        respaldo. Esto evita que el servidor HTTP intente leer objetos creados dentro
        de la transaccion de un test pytest.
        """
        if os.getenv("CI", "").lower() == "true":
            case = TestCase.objects.filter(code="TC-E2E-001", test_plan__project__code="E2E-CI").first()
            if case:
                return str(case.pk)
            raise AssertionError("CI no preparo el caso Selenium TC-E2E-001 en el proyecto E2E-CI.")

        case_id = self._bootstrap_executable_case()
        self.open_path(f"/executions/?case={case_id}")
        return case_id

    def login(self) -> None:
        self.open_path("/login/")
        email = os.getenv("SELENIUM_EMAIL", "qa@example.com")
        password = os.getenv("SELENIUM_PASSWORD", "Istqb2026.Temp!")
        self.type_text((By.NAME, "email"), email)
        self.type_text((By.NAME, "password"), password)
        self.click((By.CSS_SELECTOR, "button[type='submit'], input[type='submit']"))
        self.wait.until(lambda driver: "/login" not in driver.current_url)

    def wait_for_text(self, text: str) -> None:
        self.wait.until(lambda driver: text in driver.find_element(By.TAG_NAME, "body").text)

    def wait_for_any_visible(self, locators: Iterable[tuple[str, str]]) -> None:
        def any_visible(driver: WebDriver):
            for locator in locators:
                for element in driver.find_elements(*locator):
                    if element.is_displayed():
                        return element
            return False
        self.wait.until(any_visible)

    def print_success(self, module_name: str, test_name: str) -> None:
        print(f"[OK] Modulo: {module_name} | Caso: {test_name}")

    def print_error(self, module_name: str, test_name: str, error: Exception) -> None:
        print(f"[ERROR] Modulo: {module_name} | Caso: {test_name} | Error encontrado: {error}")

    def take_screenshot(self, test_name: str) -> Path | None:
        if not getattr(self, "driver", None):
            return None
        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(char if char.isalnum() or char in "-_" else "_" for char in test_name)
        path = SCREENSHOTS_DIR / f"{safe_name}_{timestamp}.png"
        try:
            self.driver.save_screenshot(str(path))
        except Exception:
            return None
        print(f"[EVIDENCIA] Screenshot generado: {path}")
        return path
