"""Pruebas funcionales CRUD para casos de prueba."""

from selenium.webdriver.common.by import By

from base_test import SeleniumBaseTest


class TestTestCases(SeleniumBaseTest):
    def test_crear_caso_de_prueba_y_validar_mensaje_exito(self):
        module_name = "CRUD de casos de prueba"
        test_name = "crear caso de prueba"

        try:
            self.login()
            self.open_path("/test-cases/create/")

            self.type_text((By.NAME, "title"), "TC-SEL-001 Login exitoso")
            self.type_text((By.NAME, "preconditions"), "Usuario registrado y activo.")
            self.type_text((By.NAME, "steps"), "1. Abrir login\n2. Ingresar credenciales\n3. Enviar formulario")
            self.type_text((By.NAME, "expected_result"), "El sistema muestra el dashboard principal.")
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

    def test_listar_casos_de_prueba(self):
        module_name = "CRUD de casos de prueba"
        test_name = "listar casos de prueba"

        try:
            self.login()
            self.open_path("/test-cases/")
            self.wait_for_any_visible(
                [
                    (By.CSS_SELECTOR, "table"),
                    (By.CSS_SELECTOR, "[data-testid='testcases-list']"),
                    (By.CSS_SELECTOR, ".testcase-list"),
                ]
            )
            self.print_success(module_name, test_name)
        except Exception as error:
            self.print_error(module_name, test_name, error)
            raise
