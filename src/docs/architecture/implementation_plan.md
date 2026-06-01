# Plan de construccion

## Decision arquitectonica

La plataforma queda como monolito modular Django. No se separa frontend/backend como en Node porque Django permite entregar una aplicacion web completa con templates, formularios, autenticacion, permisos, modelos y administracion en el mismo proyecto. Si mas adelante se requiere una SPA o app movil, se puede exponer una API con Django REST Framework sin romper los modulos actuales.

## Modulos iniciales

- `users`: usuario personalizado por email y roles ADMIN, STUDENT, TEACHER.
- `authentication`: login y logout.
- `dashboard`: resumen operativo.
- `projects`: proyectos de prueba.
- `requirements`: requisitos trazables.
- `testplans`: planes de prueba.
- `testcases`: casos de prueba.
- `executions`: ejecuciones y evidencias.
- `defects`: defectos derivados de pruebas.
- `incidents`: incidentes operativos.
- `traceability`: matriz requisito-caso.
- `reports`: reportes generados.
- `notifications`: avisos internos.
- `audit`: bitacora para acciones relevantes.
- `phases`: fases del proceso de pruebas.
- `core`: abstracciones compartidas.

## Requisitos no funcionales a validar

- Seguridad: roles, permisos, CSRF, cookies HttpOnly, contrasenas robustas, auditoria, configuracion por entorno.
- Mantenibilidad: apps separadas, modelos pequenos, servicios/selectores cuando la logica crezca, pruebas por capa.
- Disponibilidad: PostgreSQL con volumen persistente y configuracion por variables de entorno.
- Usabilidad: navegacion consistente, interfaz responsiva, feedback de validacion.
- Trazabilidad: relaciones requisito-plan-caso-ejecucion-defecto-reporte.
- Testabilidad: `settings.testing` con SQLite y carpetas `tests/unit`, `tests/integration`, `tests/e2e`.

## Incrementos sugeridos

1. Autenticacion completa: registro controlado, recuperacion de contrasena y perfiles.
2. CRUD de proyectos y miembros.
3. CRUD de requisitos y aprobacion.
4. Planes y casos de prueba con versionado basico.
5. Ejecuciones con carga de evidencia.
6. Defectos, incidentes y flujo de estados.
7. Matriz de trazabilidad y reportes.
8. Permisos finos por rol y auditoria automatica.
9. Pruebas unitarias, integracion y e2e.
