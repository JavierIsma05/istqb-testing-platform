"""Pruebas funcionales CRUD para requisitos."""

from selenium.webdriver.common.by import By

from base_test import SeleniumBaseTest


class TestRequirements(SeleniumBaseTest):
    def test_crear_requisito_y_validar_mensaje_exito(self):
        module_name = "CRUD de requisitos"
        test_name = "crear requisito"

        try:
            self.login()
            self.open_path("/requirements/create/")

            self.type_text((By.NAME, "title"), "REQ-SEL-001 Validar acceso al sistema")
            self.type_text((By.NAME, "description"), "El usuario autenticado debe acceder al dashboard.")
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

    def test_listar_requisitos(self):
        module_name = "CRUD de requisitos"
        test_name = "listar requisitos"

        try:
            self.login()
            self.open_path("/requirements/")
            self.wait_for_any_visible(
                [
                    (By.CSS_SELECTOR, "table"),
                    (By.CSS_SELECTOR, "[data-testid='requirements-list']"),
                    (By.CSS_SELECTOR, ".requirement-list"),
                ]
            )
            self.print_success(module_name, test_name)
        except Exception as error:
            self.print_error(module_name, test_name, error)
            raise
