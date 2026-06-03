"""Pruebas funcionales para registro de defectos."""

from selenium.webdriver.common.by import By

from base_test import SeleniumBaseTest


class TestDefects(SeleniumBaseTest):
    def test_registrar_defecto_y_validar_mensaje_exito(self):
        module_name = "Registro de defectos"
        test_name = "registrar defecto"

        try:
            self.login()
            self.open_path("/defects/create/")

            self.type_text((By.NAME, "title"), "DEF-SEL-001 Mensaje de validacion")
            self.type_text((By.NAME, "description"), "Defecto de ejemplo registrado por Selenium.")
            self.type_text((By.NAME, "severity"), "Medium")
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
