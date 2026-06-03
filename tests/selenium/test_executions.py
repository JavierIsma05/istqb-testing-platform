"""Pruebas funcionales para registro de ejecuciones."""

from selenium.webdriver.common.by import By

from base_test import SeleniumBaseTest


class TestExecutions(SeleniumBaseTest):
    def test_registrar_ejecucion_y_validar_mensaje_exito(self):
        module_name = "Registro de ejecuciones"
        test_name = "registrar ejecucion"

        try:
            self.login()
            self.open_path("/executions/create/")

            self.type_text((By.NAME, "result"), "Passed")
            self.type_text((By.NAME, "comments"), "Ejecucion registrada por Selenium.")
            self.click((By.CSS_SELECTOR, "button[type='submit'], input[type='submit']"))

            self.wait_for_any_visible(
                [
                    (By.CSS_SELECTOR, ".alert-success"),
                    (By.CSS_SELECTOR, ".messages .success"),
                    (By.CSS_SELECTOR, "[data-testid='success-message']"),
                ]
            )

            self.print_success(module_name, test_name)
        except Exception as error:
            self.print_error(module_name, test_name, error)
            raise
