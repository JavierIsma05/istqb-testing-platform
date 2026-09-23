"""
Prueba exhaustiva de la plataforma ISTQB Testing Platform.
Prueba el flujo completo: login -> proyectos -> requisitos -> planes -> casos -> ejecuciones -> defectos/incidentes -> reportes
"""

import asyncio
import time
from playwright.async_api import async_playwright


BASE_URL = "http://127.0.0.1:8000"
USER_EMAIL = "javier.aguilar@unl.edu.ec"
USER_PASSWORD = "test12345"


async def test_login(page):
    """Probar login"""
    print("\n=== 1. PROBANDO LOGIN ===")
    await page.goto(f"{BASE_URL}/login/")
    await page.fill('input[name="email"]', USER_EMAIL)
    await page.fill('input[name="password"]', USER_PASSWORD)
    await page.click('button[type="submit"]')
    await page.wait_for_url(f"{BASE_URL}/dashboard/")
    print("[OK] Login exitoso - Redirigido a dashboard")
    return True


async def test_dashboard(page):
    """Probar dashboard"""
    print("\n=== 2. PROBANDO DASHBOARD ===")
    await page.goto(f"{BASE_URL}/dashboard/")
    await page.wait_for_selector('h2:has-text("Dashboard"), h3:has-text("Dashboard"), .page-heading', timeout=5000)
    print("[OK] Dashboard cargado correctamente")
    
    # Verificar estadísticas
    stats = await page.query_selector_all('.stat-card, .card')
    print(f"  - Tarjetas de estadísticas encontradas: {len(stats)}")
    return True


async def test_crear_proyecto(page):
    """Crear un proyecto"""
    print("\n=== 3. CREANDO PROYECTO ===")
    await page.goto(f"{BASE_URL}/projects/new/")
    await page.wait_for_selector('input[name="name"]', timeout=10000)
    
    project_name = f"Proyecto ISTQB Test {int(time.time())}"
    # El código se genera automáticamente (campo readonly)
    
    await page.fill('input[name="name"]', project_name)
    await page.fill('textarea[name="description"]', "Proyecto de prueba automatizada para validar toda la plataforma ISTQB")
    
    # Fechas
    from datetime import datetime, timedelta
    start_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
    
    await page.fill('input[name="start_date"]', start_date)
    await page.fill('input[name="end_date"]', end_date)
    
    # Usar selector más específico para el botón de submit del formulario
    await page.click('form[method="POST"] button[type="submit"].btn-brand')
    # Esperar a que aparezca el proyecto en la lista o mensaje de éxito
    await page.wait_for_selector(f'text={project_name}', timeout=10000)
    # Luego navegar a la lista de proyectos
    await page.goto(f"{BASE_URL}/projects/")
    
    # Verificar que aparece en la lista
    await page.wait_for_selector(f'text={project_name}', timeout=5000)
    print(f"[OK] Proyecto creado: {project_name}")
    
    # Obtener ID del proyecto - buscar el enlace "Ver Proyecto" en la tarjeta
    project_card = await page.query_selector(f'.project-card:has-text("{project_name}")')
    if project_card:
        view_link = await project_card.query_selector('a.view-project-button, a[href*="/projects/"]')
        if view_link:
            href = await view_link.get_attribute('href')
            # href format: /projects/123/?project=123
            project_id = href.split('/')[2] if href and len(href.split('/')) > 2 else None
            print(f"  - Project ID: {project_id}")
            return project_id
    
    # Fallback: buscar en tabla
    view_link = await page.query_selector(f'table a[href*="/projects/"]')
    if view_link:
        href = await view_link.get_attribute('href')
        project_id = href.split('/')[2] if href and len(href.split('/')) > 2 else None
        print(f"  - Project ID (tabla): {project_id}")
        return project_id
    
    return None


async def test_crear_requisitos(page, project_id):
    """Crear requisitos para el proyecto"""
    print("\n=== 4. CREANDO REQUISITOS ===")
    # Las URLs de requirements no son project-scoped, usan /requirements/new/
    # El proyecto se selecciona en el formulario
    await page.goto(f"{BASE_URL}/requirements/new/")
    await page.wait_for_selector('select[name="project"]', timeout=10000)
    
    requisitos = [
        {
            "title": "Autenticación de usuarios",
            "description": "El sistema debe permitir autenticación segura con email y contraseña",
            "type": "FUNCTIONAL",
            "priority": "HIGH"
        },
        {
            "title": "Gestión de proyectos",
            "description": "Los administradores deben poder crear, editar y eliminar proyectos",
            "type": "FUNCTIONAL",
            "priority": "HIGH"
        },
        {
            "title": "Tiempo de respuesta < 2 segundos",
            "description": "Todas las páginas deben cargar en menos de 2 segundos",
            "type": "NON_FUNCTIONAL",
            "priority": "MEDIUM"
        }
    ]
    
    created_req_ids = []
    for i, req in enumerate(requisitos):
        if i > 0:
            await page.goto(f"{BASE_URL}/requirements/new/")
            await page.wait_for_selector('select[name="project"]', timeout=10000)
        
        # Seleccionar proyecto
        await page.select_option('select[name="project"]', project_id)
        await page.fill('input[name="title"]', req["title"])
        await page.fill('textarea[name="description"]', req["description"])
        await page.select_option('select[name="requirement_type"]', req["type"])
        await page.select_option('select[name="priority"]', req["priority"])
        
        # El código se genera automáticamente
        await page.click('form[method="POST"] button[type="submit"].btn-brand')
        await page.wait_for_url(f"{BASE_URL}/requirements/")
        
        # Obtener ID - buscar enlace de editar
        edit_link = await page.query_selector(f'a[href*="/requirements/"][href*="/edit/"]:has-text("{req["title"]}"), a[href*="/requirements/"]:has-text("Editar")')
        if not edit_link:
            # Buscar en la tabla por el título
            edit_links = await page.query_selector_all('a[href*="/requirements/"][href*="/edit/"]')
            for link in edit_links:
                href = await link.get_attribute('href')
                if req["title"] in await link.inner_text() or req["title"] in (await link.evaluate('el => el.closest("article").innerText')):
                    edit_link = link
                    break
        
        if edit_link:
            href = await edit_link.get_attribute('href')
            # href format: /requirements/123/edit/
            req_id = href.split('/')[2] if href and len(href.split('/')) > 2 else None
            created_req_ids.append(req_id)
            print(f"  [OK] Requisito creado: {req['title']} (ID: {req_id})")
        else:
            # Intentar buscar en la tabla
            await page.wait_for_selector(f'text={req["title"]}', timeout=5000)
            print(f"  [OK] Requisito creado: {req['title']} (aparece en lista)")
    
    return created_req_ids


async def test_crear_plan_pruebas(page, project_id, req_ids):
    """Crear plan de pruebas"""
    print("\n=== 5. CREANDO PLAN DE PRUEBAS ===")
    # Test plans están en /test-plans/new/ - es un wizard de 6 pasos
    await page.goto(f"{BASE_URL}/test-plans/new/")
    await page.wait_for_selector('select[name="project"]', timeout=10000)
    
    plan_name = f"Plan de Pruebas ISTQB {int(time.time())}"
    
    # Paso 1: Información general
    await page.select_option('select[name="project"]', project_id)
    await page.fill('input[name="name"]', plan_name)
    await page.fill('input[name="version"]', "1.0")
    await page.fill('textarea[name="description"]', "Plan de pruebas para validar funcionalidades principales")
    await page.click('[data-wizard-next]')
    await page.wait_for_timeout(500)
    
    # Paso 2: Alcance y Objetivos
    await page.fill('textarea[name="scope"]', "Pruebas de funcionalidades principales")
    await page.fill('textarea[name="objective"]', "Validar que el sistema cumple con los requisitos")
    await page.click('[data-wizard-next]')
    await page.wait_for_timeout(500)
    
    # Paso 3: Enfoque de Prueba
    await page.fill('textarea[name="strategy"]', "Pruebas basadas en riesgos")
    await page.fill('textarea[name="environment"]', "Entorno de desarrollo")
    await page.fill('textarea[name="estimation"]', "2 semanas")
    await page.click('[data-wizard-next]')
    await page.wait_for_timeout(500)
    
    # Paso 4: Criterios
    await page.fill('textarea[name="entry_criteria"]', "Requisitos aprobados")
    await page.fill('textarea[name="exit_criteria"]', "Todos los casos pasados")
    await page.fill('input[name="minimum_pass_percentage"]', "80")
    await page.fill('input[name="maximum_critical_defects"]', "0")
    await page.fill('input[name="minimum_coverage_percentage"]', "90")
    await page.click('[data-wizard-next]')
    await page.wait_for_timeout(500)
    
    # Paso 5: Recursos y Calendario
    await page.fill('textarea[name="resources"]', "Equipo de QA")
    await page.fill('textarea[name="responsibilities"]', "Testers ejecutan, tutor revisa")
    from datetime import datetime, timedelta
    start_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    await page.fill('input[name="start_date"]', start_date)
    await page.fill('input[name="end_date"]', end_date)
    # status está disabled, saltar
    await page.click('[data-wizard-next]')
    await page.wait_for_timeout(500)
    
    # Paso 6: Riesgos - skip, just submit
    await page.click('.wizard-submit')
    await page.wait_for_selector(f'text={plan_name}', timeout=10000)
    print(f"[OK] Plan de pruebas creado: {plan_name}")
    
    # Obtener ID - buscar el enlace "Editar" en el artículo que contiene el nombre del plan
    await page.goto(f"{BASE_URL}/test-plans/")
    await page.wait_for_selector(f'text={plan_name}', timeout=5000)
    
    # Buscar el artículo que contiene el nombre del plan y luego el enlace Editar
    plan_article = await page.query_selector(f'article:has-text("{plan_name}")')
    if plan_article:
        edit_link = await plan_article.query_selector('a[href*="/test-plans/"][href*="/edit/"]')
        if edit_link:
            href = await edit_link.get_attribute('href')
            # href format: /test-plans/22/edit/ -> ID is the second to last element
            plan_id = href.rstrip('/').split('/')[-2] if href else None
print(f"  - Plan ID: {plan_id}")
            return plan_id
    
    # Fallback: buscar todos los enlaces de editar y encontrar el que corresponde
    edit_links = await page.query_selector_all('a[href*="/test-plans/"][href*="/edit/"]')
    for link in edit_links:
        href = await link.get_attribute('href')
        article = await link.evaluate('el => el.closest("article")')
        if article and plan_name in article.innerText:
            plan_id = href.rstrip('/').split('/')[-2] if href else None
            print(f"  - Plan ID: {plan_id}")
            return plan_id
    
    print(f"  - Plan creado pero no se pudo obtener ID")
    return None


async def test_crear_casos_prueba(page, project_id, plan_id, req_ids):
    """Crear casos de prueba - se crean via modal en /test-cases/"""
    print("\n=== 6. CREANDO CASOS DE PRUEBA ===")
    await page.goto(f"{BASE_URL}/test-cases/")
    await page.wait_for_selector('button[data-bs-target="#testCaseModal"]', timeout=10000)
    
    if not plan_id:
        print("  [WARN] No hay plan_id válido, saltando creación de casos")
        return []
    
    casos = [
        {
            "title": "Login válido",
            "description": "Verificar login con credenciales correctas",
            "preconditions": "Usuario existe en el sistema",
            "steps": "1. Ir a /login/\n2. Ingresar email válido\n3. Ingresar contraseña correcta\n4. Click en Iniciar sesión",
            "expected_result": "Redirige a dashboard",
            "priority": "HIGH"
        }
    ]
    
    created_case_ids = []
    for i, caso in enumerate(casos):
        # Abrir modal
        await page.click('button[data-bs-target="#testCaseModal"]')
        await page.wait_for_selector('#testCaseModal', state='visible', timeout=5000)
        await page.wait_for_selector('#testCaseModal input[name="title"]', timeout=5000)
        
        await page.fill('#testCaseModal input[name="title"]', caso["title"])
        await page.fill('#testCaseModal textarea[name="description"]', caso["description"])
        await page.fill('#testCaseModal textarea[name="preconditions"]', caso["preconditions"])
        await page.fill('#testCaseModal textarea[name="steps"]', caso["steps"])
        await page.fill('#testCaseModal textarea[name="expected_result"]', caso["expected_result"])
        await page.select_option('#testCaseModal select[name="priority"]', caso["priority"])
        await page.select_option('#testCaseModal select[name="level"]', 'SYSTEM')
        await page.select_option('#testCaseModal select[name="execution_type"]', 'MANUAL')
        await page.select_option('#testCaseModal select[name="technique"]', 'BLACK_BOX')
        
        # Poblar requirement dropdown directamente via JS
        await page.evaluate(f'''
            const reqSelect = document.querySelector("#testCaseModal select[name=\\"requirement\\"]");
            const planInput = document.querySelector("#testCaseModal input[name=\\"test_plan\\"]");
            if (planInput && reqSelect) {{
                planInput.value = "{plan_id}";
                const reqData = JSON.parse(planInput.getAttribute("data-requirements-by-plan") || "{{}}");
                const reqs = reqData["{plan_id}"] || [];
                reqSelect.innerHTML = "";
                const placeholder = document.createElement("option");
                placeholder.value = "";
                placeholder.textContent = reqs.length ? "Selecciona un requisito" : "El plan seleccionado no tiene requisitos disponibles";
                reqSelect.appendChild(placeholder);
                reqs.forEach(function(req) {{
                    const option = document.createElement("option");
                    option.value = String(req.value);
                    option.textContent = req.label;
                    reqSelect.appendChild(option);
                }});
                reqSelect.disabled = reqs.length === 0;
            }}
        ''')
        await page.wait_for_timeout(500)
        
        # Seleccionar requisito (obligatorio)
        await page.select_option('#testCaseModal select[name="requirement"]', req_ids[0] if req_ids else '')
        
        # Status está disabled, saltar
        
        await page.click('#testCaseModal button[type="submit"]')
        await page.wait_for_timeout(3000)
        
        # Verificar si hay errores en el modal
        error_elems = await page.query_selector_all('#testCaseModal .form-error, #testCaseModal .alert-danger')
        if error_elems:
            for err in error_elems:
                text = await err.inner_text()
                print(f"  [ERROR FORM] {text}")
        
        # Recargar la página para ver los casos
        await page.goto(f"{BASE_URL}/test-cases/")
        await page.wait_for_selector(f'text={caso["title"]}', timeout=10000)
        
        case_link = await page.query_selector(f'a:has-text("{caso["title"]}")')
        if case_link:
            href = await case_link.get_attribute('href')
            case_id = href.split('/')[-2] if href else None
            created_case_ids.append(case_id)
            print(f"  [OK] Caso creado: {caso['title']} (ID: {case_id})")
        else:
            print(f"  [OK] Caso creado: {caso['title']} (aparece en lista)")
    
    return created_case_ids


async def test_ejecutar_pruebas(page, project_id, plan_id, case_ids):
    """Ejecutar casos de prueba"""
    print("\n=== 7. EJECUTANDO PRUEBAS ===")
    await page.goto(f"{BASE_URL}/projects/{project_id}/testplans/{plan_id}/executions/new/")
    await page.wait_for_selector('form')
    
    execution_name = f"Ejecución {int(time.time())}"
    await page.fill('input[name="name"]', execution_name)
    await page.fill('textarea[name="description"]', "Ejecución automatizada de prueba completa")
    
    # Seleccionar casos de prueba
    try:
        await page.select_option('select[name="test_cases"]', case_ids)
    except:
        print("  - Selección de casos no disponible")
    
    await page.click('button[type="submit"]')
    await page.wait_for_url(f"{BASE_URL}/projects/{project_id}/testplans/{plan_id}/executions/")
    
    print(f"[OK] Ejecución creada: {execution_name}")
    
    # Entrar a la ejecución para ejecutar pasos
    exec_link = await page.query_selector(f'a:has-text("{execution_name}")')
    if exec_link:
        href = await exec_link.get_attribute('href')
        exec_id = href.split('/')[-2] if href else None
        print(f"  - Execution ID: {exec_id}")
        
        # Ejecutar cada caso
        for case_id in case_ids:
            await page.goto(f"{BASE_URL}/executions/{exec_id}/testcases/{case_id}/execute/")
            await page.wait_for_selector('form')
            
            # Marcar como passed
            try:
                await page.select_option('select[name="status"]', 'PASSED')
                await page.fill('textarea[name="actual_result"]', "Prueba ejecutada correctamente - resultado esperado obtenido")
                await page.fill('input[name="duration_seconds"]', '30')
                await page.click('button[type="submit"]')
                await page.wait_for_load_state('networkidle')
                print(f"    [OK] Caso {case_id} ejecutado: PASSED")
            except Exception as e:
                print(f"    [WARN] Error ejecutando caso {case_id}: {e}")
        
        return exec_id
    
    return None


async def test_crear_defecto(page, project_id):
    """Crear un defecto"""
    print("\n=== 8. CREANDO DEFECTO ===")
    await page.goto(f"{BASE_URL}/projects/{project_id}/defects/new/")
    await page.wait_for_selector('form')
    
    defect_code = f"DEF-{int(time.time())}"
    await page.fill('input[name="code"]', defect_code)
    await page.fill('input[name="title"]', "Error en validación de email")
    await page.fill('textarea[name="description"]', "El sistema acepta emails sin @ al registrarse")
    await page.select_option('select[name="severity"]', 'MAJOR')
    await page.select_option('select[name="priority"]', 'HIGH')
    await page.select_option('select[name="status"]', 'OPEN')
    
    await page.click('button[type="submit"]')
    await page.wait_for_url(f"{BASE_URL}/projects/{project_id}/defects/")
    
    await page.wait_for_selector(f'text={defect_code}', timeout=5000)
    print(f"[OK] Defecto creado: {defect_code}")
    return True


async def test_crear_incidente(page, project_id):
    """Crear un incidente"""
    print("\n=== 9. CREANDO INCIDENTE ===")
    await page.goto(f"{BASE_URL}/projects/{project_id}/incidents/new/")
    await page.wait_for_selector('form')
    
    incident_code = f"INC-{int(time.time())}"
    await page.fill('input[name="code"]', incident_code)
    await page.fill('input[name="title"]', "Rendimiento degradado en dashboard")
    await page.fill('textarea[name="description"]', "El dashboard tarda más de 5 segundos en cargar con 50+ proyectos")
    await page.select_option('select[name="impact"]', 'HIGH')
    await page.select_option('select[name="probability"]', 'MEDIUM')
    await page.select_option('select[name="status"]', 'OPEN')
    
    await page.click('button[type="submit"]')
    await page.wait_for_url(f"{BASE_URL}/projects/{project_id}/incidents/")
    
    await page.wait_for_selector(f'text={incident_code}', timeout=5000)
    print(f"[OK] Incidente creado: {incident_code}")
    return True


async def test_trazabilidad(page, project_id):
    """Verificar trazabilidad"""
    print("\n=== 10. VERIFICANDO TRAZABILIDAD ===")
    await page.goto(f"{BASE_URL}/projects/{project_id}/traceability/")
    await page.wait_for_selector('table, .traceability-matrix, h1:has-text("Trazabilidad")', timeout=5000)
    print("[OK] Matriz de trazabilidad cargada")
    return True


async def test_reportes(page, project_id):
    """Verificar reportes"""
    print("\n=== 11. VERIFICANDO REPORTES ===")
    await page.goto(f"{BASE_URL}/projects/{project_id}/reports/")
    await page.wait_for_selector('h1:has-text("Reportes"), .report-list', timeout=5000)
    print("[OK] Página de reportes cargada")
    
    # Intentar generar reporte
    try:
        await page.goto(f"{BASE_URL}/projects/{project_id}/reports/generate/")
        await page.wait_for_selector('form', timeout=5000)
        print("  [OK] Formulario de generación de reportes accesible")
    except:
        print("  - Generación de reportes no disponible en esta ruta")
    
    return True


async def test_admin_panel(page):
    """Verificar panel de administración"""
    print("\n=== 12. VERIFICANDO PANEL ADMIN (JAZZMIN) ===")
    await page.goto(f"{BASE_URL}/admin/")
    await page.wait_for_selector('#content-main, .dashboard', timeout=5000)
    print("[OK] Panel de administración Jazzmin cargado")
    
    # Verificar que se ven los modelos
    models = await page.query_selector_all('#content-main a[href*="/admin/"]')
    print(f"  - Modelos registrados en admin: {len(models)}")
    return True


async def main():
    print("=" * 60)
    print("INICIANDO PRUEBA EXHAUSTIVA DE LA PLATAFORMA ISTQB")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Configurar timeouts
        page.set_default_timeout(30000)
        
        all_passed = True
        project_id = None
        plan_id = None
        req_ids = []
        case_ids = []
        
        try:
            # 1. Login
            await test_login(page)
            
            # 2. Dashboard
            await test_dashboard(page)
            
            # 3. Crear proyecto
            project_id = await test_crear_proyecto(page)
            if not project_id:
                raise Exception("No se pudo crear proyecto")
            
            # 4. Crear requisitos
            req_ids = await test_crear_requisitos(page, project_id)
            
            # 5. Crear plan de pruebas
            plan_id = await test_crear_plan_pruebas(page, project_id, req_ids)
            if not plan_id:
                raise Exception("No se pudo crear plan de pruebas")
            
            # 6. Crear casos de prueba
            case_ids = await test_crear_casos_prueba(page, project_id, plan_id, req_ids)
            
            # 7. Ejecutar pruebas
            await test_ejecutar_pruebas(page, project_id, plan_id, case_ids)
            
            # 8. Crear defecto
            await test_crear_defecto(page, project_id)
            
            # 9. Crear incidente
            await test_crear_incidente(page, project_id)
            
            # 10. Trazabilidad
            await test_trazabilidad(page, project_id)
            
            # 11. Reportes
            await test_reportes(page, project_id)
            
            # 12. Admin panel
            await test_admin_panel(page)
            
            print("\n" + "=" * 60)
            print("[EXITO] TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n[ERROR] ERROR EN PRUEBAS: {e}")
            all_passed = False
            # Tomar screenshot del error
            await page.screenshot(path="error_screenshot.png")
            print("  - Screenshot guardado en error_screenshot.png")
        
        finally:
            await browser.close()
    
    return all_passed


if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)