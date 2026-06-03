"""Pruebas funcionales de navegacion entre modulos."""

from selenium.webdriver.common.by import By

from base_test import SeleniumBaseTest


class TestNavigation(SeleniumBaseTest):
    def test_navegacion_entre_modulos_principales(self):
        module_name = "Navegacion entre modulos"
        test_name = "menu principal"

        links = [
            ("Proyectos", "projects"),
            ("Requisitos", "requirements"),
            ("Casos de prueba", "test-cases"),
            ("Ejecuciones", "executions"),
            ("Defectos", "defects"),
        ]

        try:
            self.login()

            for label, path in links:
                self.open_dashboard()
                self.click(
                    (
                        By.CSS_SELECTOR,
                        f"a[href*='{path}'], [data-testid='nav-{path}']",
                    )
                )
                self.wait_for_url_contains(path)
                print(f"[OK] Navegacion validada: {label}")

            self.print_success(module_name, test_name)
        except Exception as error:
            self.print_error(module_name, test_name, error)
            raise
