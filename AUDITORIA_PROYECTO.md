# Auditoria del proyecto ISTQB Testing Platform

## Resumen ejecutivo

El proyecto es una plataforma Django modular para gestionar el ciclo de vida de pruebas en proyectos de titulacion con enfoque ISTQB. La estructura general es adecuada para una tesis basada en RAD: separa configuracion, aplicaciones de dominio, templates, static, pruebas y documentacion.

La auditoria encontro una base funcional consistente, con trazabilidad principal entre proyecto, requisitos, planes, casos, ejecuciones, defectos e informes. Tambien se detectaron riesgos de mantenibilidad por vistas muy extensas, algunos modulos con responsabilidades mezcladas y deuda de limpieza por caches y carpetas vacias.

Se aplicaron correcciones de bajo riesgo: limpieza de artefactos temporales, eliminacion de carpetas vacias sin utilidad, correccion del contexto del dashboard docente, reduccion parcial de codigo muerto en reportes y adicion de un comando de auditoria de usuarios.

## Arquitectura encontrada

- Proyecto Django ubicado en `src/`, con settings separados en `base.py`, `development.py`, `testing.py` y `production.py`.
- Apps por dominio: `projects`, `requirements`, `testplans`, `testcases`, `executions`, `incidents`, `defects`, `traceability`, `reports`, `phases`, `dashboard`, `users`, `authentication`, `notifications`, `audit` y `core`.
- Templates centralizados en `src/templates`.
- Assets centralizados en `src/static`.
- Pruebas unitarias y de flujo en `tests/` y pruebas por app.
- Documentacion tecnica y evidencias en `docs/` y `src/docs/`.

## Arquitectura propuesta

- Mantener la modularidad por apps RAD, pero mover reglas de negocio pesadas desde vistas hacia `services/` y `selectors/`.
- Mantener vistas como capa HTTP: validacion de request, llamada a servicios, render o redirect.
- Crear servicios especificos para:
  - generacion de reportes PDF,
  - calculo de metricas de dashboard,
  - avance de fases RF11,
  - trazabilidad y cobertura,
  - auditoria de usuarios.
- Normalizar nombres de relaciones y reportes para que el flujo RF01 a RF10 sea visible desde codigo y documentacion.

## Fortalezas

- Arquitectura modular por apps Django.
- Modelo de usuario personalizado con roles `ADMIN`, `TEACHER` y `STUDENT`.
- Separacion de settings por entorno.
- Uso de `login_required` en vistas de negocio.
- Filtro central `visible_projects_for()` para restringir datos por usuario.
- Modelos con relaciones claras para el flujo ISTQB.
- Trazabilidad directa e indirecta entre requisitos y casos mediante `TestCase.requirement` y `TraceabilityLink`.
- Validacion en `TestCase.clean()` para impedir casos sin requisito o con requisito de otro proyecto.
- RF11 esta representado transversalmente con `phases`, criterios y avance por fase.
- Existe auditoria de acciones mediante `apps.audit.services.log_action`.

## Debilidades

- `src/apps/reports/views.py` es demasiado grande y mezcla consultas, calculos, narrativa, graficos PDF y vistas HTTP.
- Algunas vistas contienen logica de negocio que deberia estar en servicios (`dashboard`, `phases`, `executions`, `reports`).
- `requirements.txt` raiz no esta alineado con `requirements/base.txt`: falta `pypdf` y `reportlab` en el archivo raiz.
- `production.py` usa `ALLOWED_HOSTS = ['tu-dominio.com']`, valor placeholder que debe ajustarse antes de produccion.
- `Report` guarda contenido agregado en JSON; esto es util para snapshot, pero requiere controles claros de regeneracion y versionado.
- Existen textos con problemas de codificacion visibles como `CrÃ­tica` en varios archivos; conviene normalizar encoding a UTF-8.
- Hay una referencia de diseno Figma dentro de `src/docs/figma_reference` que es util como referencia, pero no debe mezclarse con codigo productivo.

## Riesgos

- Alto: vistas extensas dificultan pruebas, revisiones y cambios seguros.
- Alto: configuracion de produccion incompleta puede provocar despliegues inseguros o inaccesibles.
- Medio: duplicidad conceptual entre `TestCase.requirement` y `TraceabilityLink`; actualmente se maneja, pero requiere convencion clara.
- Medio: `Report.content` puede quedar desactualizado si cambian datos despues de generar el informe.
- Medio: dependencias de automatizacion con Playwright requieren entorno completo para ejecutar pruebas automatizadas.
- Bajo: carpetas de referencia y documentos grandes pueden aumentar ruido del repositorio si no se separan de entregables.

## Flujo funcional auditado

El flujo principal esta representado asi:

1. RF01 Gestion de usuarios y proyecto: `users`, `authentication`, `projects`.
2. RF02 Gestion de requisitos: `requirements`.
3. RF03 Plan de pruebas: `testplans`.
4. RF05 Casos de prueba: `testcases`.
5. RF06 Ejecucion: `executions`.
6. RF04 Incidencias: `incidents`.
7. RF07 Defectos: `defects`.
8. RF08 Trazabilidad: `traceability`.
9. RF09 Dashboard: `dashboard`.
10. RF10 Informe PDF: `reports`.
11. RF11 Validacion transversal de avance: `phases`.

No se modificaron requisitos funcionales. Se corrigio el dashboard docente porque el contexto calculado no se devolvia a la plantilla.

## Trazabilidad

Relaciones principales encontradas:

- `Project` -> `Requirement`
- `Project` -> `TestPlan`
- `TestPlan` -> `TestCase`
- `Requirement` -> `TestCase`
- `Requirement` -> `TraceabilityLink` -> `TestCase`
- `TestCase` -> `TestExecution`
- `TestExecution` -> `Defect`
- `Project` -> `Incident`
- `Project` -> `Report`

La trazabilidad esta funcionalmente cubierta. Se recomienda documentar que `TestCase.requirement` es la relacion primaria y `TraceabilityLink` es soporte para matriz o relaciones adicionales.

## Auditoria de usuarios

El sistema separa roles con `User.Roles.ADMIN`, `TEACHER` y `STUDENT`.

Se agrego el comando:

```powershell
cd src
python manage.py audit_users --settings=config.settings.development
```

El comando reporta:

- cantidad de administradores,
- cantidad de docentes,
- cantidad de estudiantes,
- estado activo/inactivo,
- ultimo acceso,
- proyecto asociado,
- tutor asociado.

No imprime contrasenas ni hashes.

## Problemas encontrados

- Bug en `build_teacher_dashboard()`: calculaba metricas docentes pero no retornaba el contexto.
- Codigo muerto parcial en `build_unl_pdf()`: existia una variable sobrante y un bloque PDF antiguo inalcanzable despues de `return`.
- Caches `__pycache__`, `.pytest_cache` y `.tmp-pytest` dentro del proyecto.
- Carpetas vacias sin utilidad operativa.
- Vistas con responsabilidades mezcladas y alta cantidad de lineas.
- Dependencias del archivo raiz incompletas frente a `requirements/base.txt`.

## Archivos eliminados

- Archivos `.pyc` dentro de directorios `__pycache__` del proyecto.
- Cache de Pytest en `.pytest_cache` fue identificado como temporal. Tras ejecutar pruebas se regenero y Windows denego su eliminacion final; queda pendiente borrarlo manualmente cuando no este bloqueado.
- Temporales de Pytest en `.tmp-pytest`.

No se elimino `venv`.

## Carpetas eliminadas

- `__pycache__` en raiz, `src` y `tests`.
- `.pytest_cache` fue intentada, pero quedo bloqueada por permisos del sistema de archivos despues de la ejecucion de pruebas.
- `.tmp-pytest`.
- `src/tests`.
- `src/apps/authentication/services`.
- `src/static/icons`.
- `src/static/img`.
- `src/static/vendors`.
- `src/templates/partials`.
- `src/templates/components/modals`.

## Modelos corregidos

No se modificaron modelos para evitar migraciones innecesarias. La auditoria no encontro una relacion critica rota que exigiera cambio estructural inmediato.

## Relaciones corregidas

No se cambiaron relaciones de base de datos. Se valido que las relaciones principales sostienen el flujo ISTQB.

## Codigo optimizado

- Corregido `src/apps/dashboard/views/dashboard_views.py` para devolver correctamente el contexto del dashboard docente.
- Reducida deuda parcial en `src/apps/reports/views.py` retirando variable inalcanzable en la generacion PDF.
- Agregado `src/apps/users/management/commands/audit_users.py` como herramienta operativa de auditoria.

## Mejoras realizadas

- Limpieza de caches y temporales, excepto `.pytest_cache` regenerada y bloqueada por Windows al cierre.
- Eliminacion de carpetas vacias sin contenido util.
- Correccion de bug en dashboard docente.
- Comando de auditoria de usuarios sin exposicion de contrasenas.
- Documentacion de arquitectura, riesgos, flujo RF y pendientes.

## Mejoras propuestas por prioridad

| Prioridad | Mejora | Motivo |
| --- | --- | --- |
| Alta | Extraer generacion PDF de `reports/views.py` hacia `reports/services/pdf.py` | Reduce riesgo y facilita pruebas |
| Alta | Completar `production.py` con hosts reales, seguridad HTTPS y static con WhiteNoise | Necesario para despliegue profesional |
| Alta | Alinear `requirements.txt` con `requirements/base.txt` o documentar un unico punto de instalacion | Evita entornos incompletos |
| Media | Extraer metricas de dashboard a servicios/selectors | Mejora mantenibilidad |
| Media | Documentar convencion entre `TestCase.requirement` y `TraceabilityLink` | Evita duplicidad confusa |
| Media | Normalizar textos a UTF-8 | Mejora presentacion academica y UX |
| Media | Agregar pruebas de permisos por rol para cada CRUD | Reduce regresiones de autorizacion |
| Baja | Separar referencias Figma fuera de `src` o marcar como documentacion | Reduce ruido del codigo productivo |

## Pendientes

- Ejecutar suite completa de pruebas unitarias y Selenium en un entorno con base de datos y navegadores configurados.
- Revisar visualmente todas las pantallas principales con datos reales.
- Completar hardening de produccion.
- Refactorizar reportes en servicios.
- Agregar pruebas especificas para el comando `audit_users`.
- Eliminar el bloque PDF inalcanzable restante en `reports/views.py` cuando se normalice la codificacion del archivo.

## Recomendaciones futuras

- Adoptar una regla de arquitectura por app: `models.py`, `forms.py`, `views.py`, `services/`, `selectors/`, `permissions.py` cuando aplique.
- Mantener RF11 como mecanismo transversal de validacion de avance, no como modulo aislado.
- Tratar informes PDF como snapshots versionados.
- Mantener `.env`, bases SQLite locales, `media/`, `staticfiles/`, caches y virtualenv fuera de Git.
- Antes de la defensa de tesis, generar un set de datos demostrativo que recorra RF01 a RF11 completo.
