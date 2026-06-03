"""Pruebas funcionales del modulo de inicio y cierre de sesion."""

from selenium.webdriver.common.by import By

from base_test import SeleniumBaseTest


class TestLogin(SeleniumBaseTest):
    def test_login_exitoso_redirecciona_al_dashboard(self):
        module_name = "Inicio de sesion"
        test_name = "login exitoso y redireccion"

        try:
            self.login()

            self.wait_for_any_visible(
                [
                    (By.CSS_SELECTOR, "[data-testid='dashboard']"),
                    (By.CSS_SELECTOR, ".dashboard"),
                    (By.TAG_NAME, "main"),
                ]
            )
            assert "login" not in self.driver.current_url.lower()

            self.print_success(module_name, test_name)
        except Exception as error:
            self.print_error(module_name, test_name, error)
            raise

    def test_logout_exitoso_redirecciona_al_login(self):
        module_name = "Cierre de sesion"
        test_name = "logout exitoso y redireccion"

        try:
            self.login()
            self.logout()

            assert "login" in self.driver.current_url.lower() or self.driver.find_elements(By.NAME, "username")
            self.print_success(module_name, test_name)
        except Exception as error:
            self.print_error(module_name, test_name, error)
            raise


if __name__ == "__main__":
    test = TestLogin()
    test.setup_method()
    try:
        test.test_login_exitoso_redirecciona_al_dashboard()
    finally:
        test.teardown_method()
