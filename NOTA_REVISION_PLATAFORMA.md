# Nota de revisión funcional — Plataforma ISTQB Testing Lifecycle

**Fecha:** 2026-09-28 · **Revisión:** instalación real, suite completa de tests, migraciones, datos demo (`seed_demo_data`) y recorrido funcional por HTTP con los 3 roles (admin, estudiante, docente).

**Veredicto general:** la plataforma está sólida. **345 de 346 tests pasan** (el único que falla requiere el navegador Chromium de Playwright instalado). El módulo de **ejecuciones —el corazón del sistema— funciona bien en casi todo**, pero se encontraron **2 bugs reales que devuelven HTTP 500** y algunos detalles menores.

---

## ✅ QUÉ SIRVE (verificado en vivo)

### Ejecuciones (lo importante)
| Funcionalidad | Estado | Evidencia |
|---|---|---|
| Workspace de ejecución manual (selección de caso, formulario, pasos) | ✅ OK | Carga 200 y registra ejecuciones reales |
| Registro de ejecución manual paso a paso | ✅ OK | Ejecución creada, 3 pasos guardados, resultado agregado calculado automáticamente |
| Resultado global a partir de pasos (fallido > bloqueado > aprobado) | ✅ OK | `aggregate_step_result` + tests |
| Bloqueo de re-ejecución normal duplicada | ✅ OK | "ya existe una ejecución normal equivalente" — obliga a usar regresión/confirmación |
| Máquina de estados NOT_RUN → RUNNING → resultado final | ✅ OK | `execution_transition_allowed` aplicada en el POST |
| Sincronización del estado del caso tras ejecutar | ✅ OK | Caso pasa a PASSED/FAILED/BLOCKED según resultado |
| Creación automática de defecto al fallar (manual y automatizada) | ✅ OK | Defecto trazable con caso, ejecución y log |
| Prueba de confirmación (defecto RESOLVED + ejecución aprobada) | ✅ OK | Defecto → CLOSED con `verification_execution`; caso → PASSED (302 limpio) |
| Confirmación fallida → defecto REOPENED sin duplicar defectos | ✅ OK | Cubierto por tests y lógica verificada |
| Regresión vinculada a defecto del mismo caso/proyecto | ✅ OK | Validado en `clean()` del modelo |
| Revisión docente desde workspace y endpoint `/review/` | ✅ OK | `review_status=VALIDATED`, auditoría REVIEW registrada |
| Revisión docente por paso con recálculo del global | ✅ OK | Paso PASSED→FAILED recalculó la ejecución a FAILED con 67% de aprobación |
| Inmutabilidad tras revisión | ✅ OK | Ejecución revisada bloquea cambios por paso, evidencia y borrado |
| Evidencia obligatoria (extensión y tamaño ≤10 MB) y evidencia por paso | ✅ OK | Validado en formularios y probado por HTTP |
| Borrado protegido | ✅ OK | Solo ejecuciones propias, PENDING y vacías; con evidencia/resultados se bloquea; ajenas se rechazan |
| Reglas automatizadas declarativas (OPEN_URL, FILL_TEXT, CLICK, VERIFY, WAIT) | ✅ OK | Sin código libre, paso auto-numerado, validación por tipo de acción |
| Seguridad de automatización (allowlist de hosts, anti-SSRF a IPs internas) | ✅ OK | `validate_automation_url` + interceptación de rutas |
| Runner automatizado con log técnico y resultado por regla | ✅ OK | Degradación elegante a ERROR con mensaje claro si falta el navegador (no revienta con 500) |
| Endpoint JSON `POST /casos/<id>/ejecutar-automatizado/` | ✅ OK | Respuesta JSON con estado y salida |
| Calendario, historial y detalle de ejecuciones | ✅ OK | 200 con contenido real |
| API docente (proyectos → estudiantes → casos) | ✅ OK | JSON correcto cuando el docente es miembro del proyecto |
| Docentes en modo solo-lectura en el workspace | ✅ OK | Redirects y bloqueos de POST verificados |

### Resto de la plataforma
- **Autenticación:** login funciona; todos los módulos protegidos redirigen al login sin sesión ✅
- **Módulos:** proyectos, requisitos, planes (`/test-plans/`), casos (`/test-cases/`), defectos, incidentes, trazabilidad, reportes, notificaciones, fases y dashboard cargan 200 ✅
- **Reportes:** PDF del informe final del plan ✅ (`application/pdf`), métricas de calidad en PDF/CSV/HTML ✅ (requieren `?project=<id>`), reporte de ejecuciones del plan ✅
- **Admin Django con Jazzmin:** carga correctamente ✅
- **Suite de tests:** 345 passed, 1 deselected (Playwright) ✅

---

## ❌ QUÉ NO SIRVE / BUGS ENCONTRADOS

### 🔴 Bug 1 — HTTP 500 al crear variables de datos de prueba (ejecuciones automatizadas)
- **Ruta:** `POST /executions/cases/<id>/test-data/new/`
- **Síntoma:** la variable **sí se guarda** en base de datos, pero el usuario recibe una página de error 500.
- **Causa:** `src/apps/executions/aux_views.py` registra en auditoría `data.name`, pero el modelo `TestData` no tiene campo `name` (usa `key` y `value`) → `AttributeError`.
- **Fix sugerido:** cambiar `'name': data.name` por `'key': data.key` (y envolver en `transaction.atomic` para que no quede guardada si la auditoría falla).

### 🔴 Bug 2 — HTTP 500 + datos a medias en prueba de confirmación sobre defectos IN_PROGRESS o REOPENED
- **Síntoma:** confirmar un defecto que está en `IN_PROGRESS` o `REOPENED` revienta con 500. La ejecución queda creada (PASSED) **pero** el defecto no se sincroniza y el caso tampoco: estado inconsistente.
- **Causa (doble):**
  1. `TestExecution.clean()` permite CONFIRMATION con defecto en `{IN_PROGRESS, RESOLVED, REOPENED, PENDING_CONFIRMATION}`, pero el ciclo de vida (`defect_transition_allowed`) solo permite cerrar desde `RESOLVED` (con verificación) o `PENDING_CONFIRMATION` → `ValidationError` no manejado en la vista.
  2. El POST del workspace **no es transaccional**: la ejecución se guarda antes del fallo y no hay rollback.
- **Fix sugerido:** alinear los estados permitidos para confirmación (p. ej. solo `RESOLVED`/`PENDING_CONFIRMATION`) o manejar la transición devolviendo un error de formulario; además decorar el POST del workspace con `@transaction.atomic`.
- **Nota:** el caso feliz (RESOLVED → confirmación aprobada → CLOSED) funciona perfecto; los tests solo cubren ese camino.

### 🟠 Bug 3 (datos demo) — El docente no puede revisar el proyecto demo
- `seed_demo_data` asigna `tutor` al proyecto pero no lo añade a `members`; la visibilidad docente se filtra por `members/created_by`, así que el docente demo ve el workspace vacío y cualquier revisión da 404.
- En el flujo real **no ocurre** (al crear/editar un proyecto, `projects/views.py` añade al tutor a `members`), por lo que es un gap solo de la semilla.
- **Fix sugerido:** `project.members.add(user)` también para el tutor en `seed_demo_data`.

### 🟡 Detalles menores (no rompen nada)
- `automated_execution_run_view` en `views.py` es **código muerto**: las URLs usan el de `automated_views.py` (con `@require_POST`, por eso GET responde 405 en vez de redirigir).
- `AutomatedStepForm.save()` tiene una condición muerta (`self.test_case_id if hasattr(...)` siempre False).
- `GET /reports/quality-metrics.pdf` sin `?project=` da 404; es por diseño pero un mensaje amigo sería mejor.

---

## ⚠️ Requisitos de entorno (importante para demostrar)

1. **Python ≥ 3.12 obligatorio:** `requirements.txt` fija `Django==6.0.5`, que no instala en Python 3.11 (verificado). El README ya indica 3.12 — respetarlo al desplegar. (Esta revisión corrió con Django 5.2.7 en Python 3.11 y todo funcionó igual.)
2. **Ejecución automatizada requiere `playwright install`** (Chromium). Sin navegador, el sistema degrada bien: ejecución `ERROR` con log técnico y mensaje al usuario — no hay 500.
3. `requirements/base.txt` incluye `django-jazzmin` pero el `requirements.txt` de la raíz **no** lo lista; usar `requirements/base.txt` o sincronizarlos.
4. `src/config/settings/live_review.py` se añadió solo para esta revisión (SQLite + todos los hosts); puede eliminarse.

---

## 🔧 MEJORAS APLICADAS EN EJECUCIONES (2026-09-28, segunda pasada)

Tras la revisión anterior se reportó que la pantalla de ejecuciones podía verse "en blanco". Se aplicaron estas mejoras:

1. **Bootstrap vendoreado localmente** (`src/static/vendor/`) — la página cargaba Bootstrap 5.3.3 y Bootstrap Icons desde `cdn.jsdelivr.net`; si el CDN fallaba o la red lo bloqueaba, la interfaz quedaba sin estilos/JS y se veía rota o en blanco. Ahora todo sale del servidor: **0 dependencias de CDN** en las plantillas.
2. **Estado vacío en el workspace** — si no hay caso seleccionado (porque el proyecto no tiene casos), antes la página quedaba literalmente en blanco bajo el encabezado. Ahora muestra una tarjeta guía con botones hacia planes/casos de prueba (`index.html` + estilos en `main.css`).
3. **Fix bug 500 al crear variables de datos de prueba** — `aux_views.py` auditaba `data.name` (atributo inexistente del modelo `TestData`); ahora usa `data.key`.
4. **Fix bug 500 + datos a medias en prueba de confirmación** — se alinearon los estados permitidos (solo defectos `RESOLVED`/`PENDING_CONFIRMATION`) en modelo y formulario, con mensaje amigable en pantalla; y el POST del workspace ahora es `@transaction.atomic`: nunca queda una ejecución guardada a medias.
5. **Seed demo mejorado** (`seed_demo_data`):
   - `TC-DEMO-001` queda con **2 reglas automatizadas simples** (abrir login + verificar título) y **2 variables de datos** (`usuario_demo`, `clave_demo`) → la pestaña Automatizada ya tiene qué ejecutar sin configurar nada.
   - Nuevo caso `TC-DEMO-003` en estado PENDIENTE para practicar una primera ejecución manual de punta a punta.
   - Opción `--teacher-email` para vincular un docente/tutor como miembro del proyecto (la revisión docente demo funciona de inmediato).
6. **3 tests de regresión nuevos** en `src/apps/executions/tests.py` cubriendo los dos bugs 500 y el caso feliz de confirmación.

7. **Preview en blanco por `X-Frame-Options: DENY`** — el preview del sandbox se muestra en un iframe de otro origen; con DENY el navegador se niega a renderizarlo y se ve completamente en blanco. En `live_review.py` se quita el middleware de clickjacking solo para el entorno de revisión (producción mantiene DENY).
8. **Cuentas demo en el login** (solo si existe `settings.DEMO_ACCOUNTS`) — botones de un clic para entrar como estudiante/docente/admin sin teclear credenciales.
9. **Fix 500 por variable de datos duplicada** — crear dos veces la misma clave (`unique_together`) devolvía un IntegrityError 500; ahora muestra un mensaje amigable.

**Estado actual:** suite completa 349 passed / 1 deselected (el de Playwright requiere `playwright install`).

## Cómo se validó
- `pytest src` → **345 passed, 1 deselected** (el de Playwright necesita Chromium).
- Servidor Django real con datos demo; recorrido HTTP con sesiones de estudiante, docente y admin: login, workspace de ejecuciones, ejecución manual, repetición bloqueada, confirmación de defecto, revisión docente global y por paso, evidencia por paso, reglas y ejecución automatizada, borrados protegidos, calendario/historial/detalle, APIs docentes, PDFs y smoke de todos los módulos.

**Credenciales de la instancia demo (si se quiere repetir):** `estudiante@review.local / Rev1ewStudent!2026`, `docente@review.local / Rev1ewTeacher!2026`, `admin@review.local / Rev1ewAdmin!2026` (settings `config.settings.live_review`, SQLite).
