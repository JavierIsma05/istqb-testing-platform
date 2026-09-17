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
