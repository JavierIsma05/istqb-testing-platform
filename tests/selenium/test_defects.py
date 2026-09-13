"""Pruebas funcionales para registro de defectos."""

from selenium.webdriver.common.by import By

from base_test import SeleniumBaseTest


class TestDefects(SeleniumBaseTest):
    def test_registrar_defecto_y_validar_mensaje_exito(self):
        module_name = "Registro de defectos"
        test_name = "registrar defecto"

        try:
            self.login()
            self.open_path("/defects/new/")

            self.select_first_available_option((By.NAME, "test_case"))

            self.type_text((By.NAME, "title"), "DEF-SEL-001 Mensaje de validacion")
            self.type_text((By.NAME, "description"), "Defecto de ejemplo registrado por Selenium.")

            severity_select = self.find_visible((By.NAME, "severity"))
            Select(severity_select).select_by_visible_text("Media")

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
