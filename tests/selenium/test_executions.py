"""Pruebas funcionales para registro de ejecuciones."""

from datetime import datetime
from pathlib import Path

from selenium.webdriver.common.by import By

from apps.testcases.models import TestCase
from base_test import SeleniumBaseTest


class TestExecutions(SeleniumBaseTest):
    def test_registrar_ejecucion_y_validar_mensaje_exito(self):
        module_name = "Registro de ejecuciones"
        test_name = "registrar ejecucion"

        try:
            self.login()
            case_id = self.ensure_test_case()
            project_id = TestCase.objects.select_related("test_plan").get(pk=case_id).test_plan.project_id
            self.open_path(f"/executions/?case={case_id}&project={project_id}")

            # El workspace tiene dos modos. Seleccionamos manual de forma explicita
            # para que el E2E no dependa del modo persistido/default del caso.
            self.click((By.CSS_SELECTOR, "[data-execution-mode-tab='manual']"))
            self.wait_for_any_visible(
                [
                    (By.CSS_SELECTOR, "form[data-execution-form]"),
                    (By.CSS_SELECTOR, "input[name='actual_result']"),
                ]
            )

            body = self.driver.find_element(By.TAG_NAME, "body").text
            if "Modo lectura" in body and "Registrar Resultado" not in body:
                raise AssertionError(
                    "Selenium inicio sesión en modo lectura; el usuario QA debe conservar el rol STUDENT."
                )
            if "No se puede ejecutar" in body or "requisito" in body.lower() and "aprob" in body.lower():
                raise AssertionError(
                    "El caso E2E requiere aprobación docente antes de ejecutar. "
                    "La precondición debe quedar satisfecha en el bootstrap de Selenium."
                )

            self.click((By.CSS_SELECTOR, "label[for='id_actual_result_cumple']"))
            execution_date = datetime.now().date().replace(day=max(1, datetime.now().day - 1))
            self.set_date((By.NAME, "planned_date"), execution_date.isoformat())

            evidence = Path(__file__).resolve().parent / "screenshots" / "evidencia_test.png"
            file_input = self.driver.find_element(By.CSS_SELECTOR, "form[data-execution-form] input[type='file']")
            file_input.send_keys(str(evidence))

            self.click((By.CSS_SELECTOR, "form[data-execution-form] button[type='submit']"))
            self.wait_for_text("Resultado de ejecucion registrado correctamente.")
            self.print_success(module_name, test_name)
        except Exception as error:
            self.print_error(module_name, test_name, error)
            raise

    def test_separar_paneles_manual_y_automatizado(self):
        module_name = "Modos de ejecución"
        test_name = "separar paneles manual y automatizado"

        try:
            self.login()
            case_id = self.ensure_test_case()
            project_id = TestCase.objects.select_related("test_plan").get(pk=case_id).test_plan.project_id
            self.open_path(f"/executions/?case={case_id}&project={project_id}")

            manual_panel = self.driver.find_element(By.CSS_SELECTOR, "[data-execution-mode-panel='manual']")
            automated_panel = self.driver.find_element(By.CSS_SELECTOR, "[data-execution-mode-panel='automated']")
            automated_tab = self.driver.find_element(By.CSS_SELECTOR, "[data-execution-mode-tab='automated']")
            manual_tab = self.driver.find_element(By.CSS_SELECTOR, "[data-execution-mode-tab='manual']")

            self.click((By.CSS_SELECTOR, "[data-execution-mode-tab='manual']"))
            if not manual_panel.is_displayed():
                raise AssertionError("El panel manual debe estar visible al seleccionar ejecución manual.")
            if automated_panel.is_displayed():
                raise AssertionError("El panel automatizado no debe mostrarse junto al panel manual.")

            self.click((By.CSS_SELECTOR, "[data-execution-mode-tab='automated']"))
            if manual_panel.is_displayed():
                raise AssertionError("El panel manual no debe mostrarse al seleccionar ejecución automatizada.")
            if not automated_panel.is_displayed():
                raise AssertionError("El panel automatizado debe ocupar el panel de resultados al seleccionarlo.")
            if self.driver.find_elements(By.CSS_SELECTOR, "[data-execution-mode-panel='automated'] form[data-execution-form]"):
                raise AssertionError("El formulario de ejecución manual no debe pertenecer al panel automatizado.")

            # Volver a manual debe restaurar exclusivamente su panel.
            self.click((By.CSS_SELECTOR, "[data-execution-mode-tab='manual']"))
            if not manual_panel.is_displayed() or automated_panel.is_displayed():
                raise AssertionError("Los paneles de ejecución no se alternan de forma exclusiva.")
            if not manual_tab.get_attribute("aria-pressed") == "true":
                raise AssertionError("La pestaña manual debe quedar marcada como activa.")
            if not automated_tab.get_attribute("aria-pressed") == "false":
                raise AssertionError("La pestaña automatizada debe quedar inactiva al volver a manual.")

            self.print_success(module_name, test_name)
        except Exception as error:
            self.print_error(module_name, test_name, error)
            raise
