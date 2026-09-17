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

    def ensure_project(self) -> str:
        self.open_path("/requirements/new/")
        project_elements = self.driver.find_elements(By.NAME, "project")
        if project_elements:
            try:
                return self.select_first_available_option((By.NAME, "project"))
            except TimeoutException:
                pass
        today = datetime.now().date(); year = today.year
        start_date = today + timedelta(days=1); end_date = datetime(year, 12, 31).date()
        if start_date.year != year or start_date > end_date:
            start_date = datetime(year, 1, 1).date()
        self.open_path("/projects/new/")
        self._require_form((By.NAME, "name"), "creación de proyecto")
        self.type_text((By.NAME, "name"), f"Proyecto E2E {int(time.time())}")
        self.type_text((By.NAME, "description"), "Proyecto auxiliar para pruebas funcionales automatizadas.")
        self.set_date((By.NAME, "start_date"), start_date.isoformat())
        self.set_date((By.NAME, "end_date"), end_date.isoformat())
        self.click((By.CSS_SELECTOR, "button[type='submit'], input[type='submit']"))
        self.wait.until(lambda driver: "/projects/" in driver.current_url or "/requirements/" in driver.current_url)
        self.open_path("/requirements/new/")
        return self.select_first_available_option((By.NAME, "project"))

    def ensure_requirement(self) -> str:
        project_id = self.ensure_project()
        self.open_path("/requirements/new/")
        self._require_form((By.NAME, "project"), "creación de requisito")
        self.select_option((By.NAME, "project"), project_id)
        self.type_text((By.NAME, "title"), f"REQ-E2E-{int(time.time())} Requisito funcional")
        self.type_text((By.NAME, "description"), "El sistema debe permitir validar una funcionalidad del proyecto.")
        if self.driver.find_elements(By.NAME, "acceptance_criteria"):
            self.type_text((By.NAME, "acceptance_criteria"), "La funcionalidad cumple el comportamiento esperado.")
        self.select_option((By.NAME, "requirement_type"), "FUNCTIONAL")
        self.select_option((By.NAME, "priority"), "HIGH")
        self.click((By.CSS_SELECTOR, "button[type='submit'], input[type='submit']"))
        self.wait_for_text("Requisito creado correctamente.")
        return project_id

    def ensure_test_plan(self) -> str:
        project_id = self.ensure_requirement()
        self.open_path("/test-plans/new/")
        project_select = self._require_form((By.NAME, "project"), "creación de plan de pruebas")
        date_ranges_raw = project_select.get_attribute("data-date-ranges") or "{}"
        try: date_ranges = json.loads(date_ranges_raw)
        except json.JSONDecodeError: date_ranges = {}
        project_range = date_ranges.get(str(project_id), {})
        start_date = project_range.get("start") or f"{datetime.now().year}-01-01"
        end_date = project_range.get("end") or f"{datetime.now().year}-12-31"
        self.select_option((By.NAME, "project"), project_id)
        values = {
            "name": f"Plan E2E {int(time.time())}", "version": "1.0",
            "description": "Plan auxiliar para pruebas funcionales automatizadas.",
            "scope": "Validacion funcional de la cadena E2E.",
            "objective": "Verificar la trazabilidad completa desde requisito hasta ejecucion.",
            "strategy": "Pruebas funcionales manuales.", "entry_criteria": "Requisito registrado y disponible.",
            "exit_criteria": "Ejecucion registrada con evidencia.", "resources": "Selenium y ambiente local.",
            "environment": "Chrome y servidor local.", "responsibilities": "Responsable de pruebas E2E.",
            "estimation": "1 hora.", "minimum_pass_percentage": "80", "maximum_critical_defects": "0",
            "minimum_coverage_percentage": "90",
        }
        for name, value in values.items():
            if self.driver.find_elements(By.NAME, name):
                element = self.driver.find_element(By.NAME, name)
                self.driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles:true})); arguments[0].dispatchEvent(new Event('change', {bubbles:true}));", element, value)
        for name, value in (("start_date", start_date), ("end_date", end_date)):
            if self.driver.find_elements(By.NAME, name): self.set_date((By.NAME, name), value)
        for step in range(2, 6):
            self.click((By.CSS_SELECTOR, "[data-wizard-next]"))
            self.wait.until(lambda driver, current=step: driver.find_element(By.CSS_SELECTOR, ".wizard-panel.active").get_attribute("data-step-panel") == str(current))
        self.click((By.CSS_SELECTOR, "button.wizard-submit[type='submit']"))
        self.wait_for_text("Plan de pruebas creado correctamente.")
        self.open_path("/test-cases/")
        self.click((By.CSS_SELECTOR, "[data-bs-target='#testCaseModal']"))
        self.find_visible((By.ID, "testCaseModal"))
        plan_id = self.driver.find_element(By.NAME, "test_plan").get_attribute("value")
        if not plan_id: raise TimeoutException("El formulario de caso no tiene un plan de pruebas seleccionado.")
        return plan_id

    def ensure_test_case(self) -> str:
        """Devuelve el caso persistente de CI; localmente conserva el bootstrap aislado."""
        if os.getenv("CI", "").lower() == "true":
            case = TestCase.objects.filter(code="TC-E2E-001", test_plan__project__code="E2E-CI").first()
            if case:
                return str(case.pk)
            raise AssertionError("CI no preparo el caso Selenium TC-E2E-001 en el proyecto E2E-CI.")
        case_id = self._bootstrap_executable_case()
        self.open_path(f"/executions/?case={case_id}")
        return case_id

    def wait_for_url_contains(self, text: str) -> None:
        self.wait.until(EC.url_contains(text))

    def wait_for_text(self, text: str) -> None:
        try:
            self.wait.until(EC.text_to_be_present_in_element((By.TAG_NAME, "body"), text))
        except TimeoutException as exc:
            url = self.driver.current_url
            body = self.driver.find_element(By.TAG_NAME, "body").text.strip().replace("\n", " | ")
            body = body[:1000] if body else "<sin contenido visible>"
            raise TimeoutException(f"No apareció el texto esperado {text!r}. URL actual: {url}. Contenido visible: {body}") from exc

    def wait_for_any_visible(self, locators: Iterable[tuple[str, str]]):
        locators = list(locators); last_error: Exception | None = None
        for locator in locators:
            try: return self.find_visible(locator)
            except TimeoutException as exc: last_error = exc
        raise TimeoutException(f"No se encontro ningun selector visible: {locators}") from last_error

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
        self.wait_for_any_visible([
            (By.CSS_SELECTOR, ".app-sidebar"),
            (By.CSS_SELECTOR, ".sidebar-nav"),
            (By.CSS_SELECTOR, ".app-content"),
        ])

    def logout(self) -> None:
        self.click((By.CSS_SELECTOR, ".user-menu, [data-testid='user-menu']"))
        forms = self.driver.find_elements(By.CSS_SELECTOR, "form[action*='logout']")
        if forms:
            form = next((form for form in forms if form.is_displayed()), forms[0])
            self.driver.execute_script("arguments[0].submit();", form)
        else:
            self.click((By.CSS_SELECTOR, "[data-testid='logout'], a[href*='logout'], .dropdown-menu a[href*='logout']"))
        self.wait_for_url_contains("/login/")
        self.wait_for_any_visible([
            (By.NAME, "username"),
            (By.NAME, "email"),
            (By.CSS_SELECTOR, "[data-testid='login-form']"),
            (By.CSS_SELECTOR, "form"),
        ])
