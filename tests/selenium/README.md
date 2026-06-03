# Pruebas funcionales automatizadas con Selenium 4

Esta carpeta contiene pruebas funcionales para un sistema web Django orientado
a procesos ISTQB: autenticacion, dashboard, proyectos, requisitos, casos de
prueba, ejecuciones, defectos y navegacion.

## Requisitos

Instalar dependencias:

```bash
pip install selenium pytest pytest-django
```

Selenium 4 puede usar Selenium Manager para resolver ChromeDriver
automaticamente. Tambien puedes instalar ChromeDriver manualmente y dejarlo en
el `PATH`.

## Ejecucion desde Visual Studio Code

1. Abrir una terminal en la raiz del proyecto.
2. Levantar Django:

```bash
python src/manage.py runserver
```

3. En otra terminal, ejecutar todas las pruebas Selenium:

```bash
pytest tests/selenium -s
```

4. Ejecutar un archivo especifico:

```bash
pytest tests/selenium/test_login.py -s
```

5. Ejecutar directamente el ejemplo de login:

```bash
python tests/selenium/test_login.py
```

## Variables de entorno opcionales

```bash
set SELENIUM_BASE_URL=http://127.0.0.1:8000/
set SELENIUM_EMAIL=qa@example.com
set SELENIUM_PASSWORD=Istqb2026.Temp!
set SELENIUM_HEADLESS=false
```

En PowerShell:

```powershell
$env:SELENIUM_BASE_URL="http://127.0.0.1:8000/"
$env:SELENIUM_EMAIL="qa@example.com"
$env:SELENIUM_PASSWORD="Istqb2026.Temp!"
$env:SELENIUM_KEEP_OPEN="true"
```

`SELENIUM_KEEP_OPEN=true` deja Chrome abierto al finalizar o fallar la prueba,
util para depurar. Cuando quieras ejecucion normal, usa:

```powershell
$env:SELENIUM_KEEP_OPEN="false"
```

## Selectores genericos

Algunos selectores usan nombres comunes como `name="username"`,
`name="password"`, `.alert-success` o rutas como `/projects/create/`.
Si tu HTML usa otros nombres, reemplazalos por selectores estables.

Ejemplo recomendado:

```html
<input data-testid="login-username" name="username">
<input data-testid="login-password" name="password">
<button data-testid="login-submit" type="submit">Ingresar</button>
<div data-testid="success-message">Proyecto creado correctamente</div>
```

Y en Python:

```python
self.type_text((By.CSS_SELECTOR, "[data-testid='login-username']"), username)
```

## Evidencias

Cuando una prueba falla, `conftest.py` captura automaticamente una imagen en:

```text
tests/selenium/screenshots/
```

Estas evidencias pueden anexarse a la documentacion academica como resultado
de ejecucion de pruebas funcionales automatizadas.
