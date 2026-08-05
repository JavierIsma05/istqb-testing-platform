"""Pruebas funcionales para registro de ejecuciones."""

from pathlib import Path

from selenium.webdriver.common.by import By

from base_test import SeleniumBaseTest


class TestExecutions(SeleniumBaseTest):
    def test_registrar_ejecucion_y_validar_mensaje_exito(self):
        module_name = "Registro de ejecuciones"
        test_name = "registrar ejecucion"

        try:
            self.login()
            self.open_path("/executions/?case=10")

            self.wait_for_any_visible(
                [
                    (By.CSS_SELECTOR, "form[data-execution-form]"),
                    (By.CSS_SELECTOR, ".execution-manual"),
                    (By.CSS_SELECTOR, "input[name='actual_result']"),
                ]
            )

            self.click((By.CSS_SELECTOR, "label[for='id_actual_result_cumple']"))
            self.set_date((By.NAME, "planned_date"), "2026-08-10")

            evidence = Path(__file__).resolve().parent / "screenshots" / "evidencia_test.png"
            file_input = self.driver.find_element(By.CSS_SELECTOR, "form[data-execution-form] input[type='file']")
            file_input.send_keys(str(evidence))

            self.click((By.CSS_SELECTOR, "form[data-execution-form] button[type='submit']"))

            self.wait_for_any_visible(
                [
                    (By.CSS_SELECTOR, ".alert-success"),
                    (By.CSS_SELECTOR, ".messages .success"),
                    (By.CSS_SELECTOR, "[data-testid='success-message']"),
                ]
            )
            assert "Resultado de ejecucion registrado correctamente." in self.driver.find_element(By.TAG_NAME, "body").text

            self.print_success(module_name, test_name)
        except Exception as error:
            self.print_error(module_name, test_name, error)
            raise
