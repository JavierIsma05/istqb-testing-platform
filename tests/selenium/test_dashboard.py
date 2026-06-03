"""Pruebas funcionales del dashboard principal."""

from selenium.webdriver.common.by import By

from base_test import SeleniumBaseTest


class TestDashboard(SeleniumBaseTest):
    def test_dashboard_principal_muestra_modulos_istqb(self):
        module_name = "Dashboard principal"
        test_name = "visualizacion de accesos principales"

        try:
            self.login()

            self.wait_for_any_visible(
                [
                    (By.CSS_SELECTOR, "[data-testid='dashboard']"),
                    (By.CSS_SELECTOR, ".dashboard"),
                    (By.TAG_NAME, "main"),
                ]
            )

            expected_modules = ["Proyecto", "Requisito", "Caso", "Ejecucion", "Defecto"]
            body_text = self.driver.find_element(By.TAG_NAME, "body").text
            assert any(module in body_text for module in expected_modules)

            self.print_success(module_name, test_name)
        except Exception as error:
            self.print_error(module_name, test_name, error)
            raise
