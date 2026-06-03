"""Pruebas funcionales CRUD para proyectos."""

from selenium.webdriver.common.by import By

from base_test import SeleniumBaseTest


class TestProjects(SeleniumBaseTest):
    def test_crear_proyecto_y_validar_mensaje_exito(self):
        module_name = "CRUD de proyectos"
        test_name = "crear proyecto"
        project_name = "Proyecto Selenium ISTQB"

        try:
            self.login()
            self.open_path("/projects/create/")

            self.type_text((By.NAME, "name"), project_name)
            self.type_text((By.NAME, "description"), "Proyecto creado por prueba funcional automatizada.")
            self.click((By.CSS_SELECTOR, "button[type='submit'], input[type='submit']"))

            self.wait_for_text("Proyecto")
            self.wait_for_any_visible(
                [
                    (By.CSS_SELECTOR, ".alert-success"),
                    (By.CSS_SELECTOR, ".messages .success"),
                    (By.CSS_SELECTOR, "[data-testid='success-message']"),
                ]
            )
            assert project_name in self.driver.find_element(By.TAG_NAME, "body").text

            self.print_success(module_name, test_name)
        except Exception as error:
            self.print_error(module_name, test_name, error)
            raise

    def test_listar_proyectos(self):
        module_name = "CRUD de proyectos"
        test_name = "listar proyectos"

        try:
            self.login()
            self.open_path("/projects/")

            self.wait_for_any_visible(
                [
                    (By.CSS_SELECTOR, "table"),
                    (By.CSS_SELECTOR, "[data-testid='projects-list']"),
                    (By.CSS_SELECTOR, ".project-list"),
                ]
            )

            self.print_success(module_name, test_name)
        except Exception as error:
            self.print_error(module_name, test_name, error)
            raise
