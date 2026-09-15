# Revision funcional del proyecto

## Resumen general

Se realizo una revision funcional tipo QA sobre la plataforma Django ISTQB Testing Platform, enfocada en navegacion, botones, enlaces, formularios, CRUD, permisos, flujo funcional RF01-RF11 y consistencia general de interfaz.

El objetivo fue verificar funcionamiento, no agregar nuevas funcionalidades. Las correcciones realizadas mantienen la logica existente.

## Estado del proyecto

El proyecto se encuentra funcional para demostracion con la suite automatizada disponible. La suite incluye cobertura de smoke tests de rutas publicas y modulos protegidos para detectar rapidamente regresiones de enrutamiento y autenticacion.

## Errores encontrados y corregidos

- Se elimino el enlace decorativo de recuperacion de contrasena en login, ya que no existe flujo implementado.
- Se ajusto la semantica visual de defectos para separar estado de severidad.
- Se eliminaron artefactos temporales de pruebas que no deben versionarse.
- Se reforzaron las restricciones de integridad de ejecuciones, requisitos y casos mediante validaciones y restricciones de base de datos.
- Se retiraron credenciales de ejemplo que no debian aparecer en documentacion publica.

## Funcionalidades verificadas

- RF01 Gestion de usuarios y proyecto.
- RF02 Gestion de requisitos e importacion.
- RF03 Plan de pruebas.
- RF04 Analisis de incidencias/riesgos.
- RF05 Casos de prueba.
- RF06 Ejecucion manual y semi-automatizada.
- RF07 Defectos.
- RF08 Trazabilidad.
- RF09 Dashboard.
- RF10 Informe PDF.
- RF11 Control de fases.

## Seguridad e integridad

- Autenticacion requerida en los modulos protegidos.
- Operaciones destructivas principales requieren POST y proteccion CSRF.
- Los usuarios se filtran por rol y los proyectos por visibilidad.
- Los artefactos existentes conservan su pertenencia al proyecto para proteger la trazabilidad historica.
- Las ejecuciones revisadas y sus pasos tienen reglas de integridad para evitar modificaciones o duplicados incompatibles.
- La configuracion de produccion exige secretos y dominios mediante variables de entorno.

## Smoke tests

Se incorporo `src/apps/core/test_smoke_routes.py` para verificar:

- Las rutas publicas principales responden correctamente.
- Las rutas principales de los modulos requieren autenticacion.
- Una ruta protegida no puede convertirse silenciosamente en una pagina publica por una regresion de URLs o decoradores.

## Problemas pendientes

- `.pytest_cache` puede quedar bloqueado por Windows despues de ejecutar pruebas; esta en `.gitignore` y puede eliminarse cuando el sistema libere el bloqueo.
- `apps/core/module_views.py` y los templates `components/module_index.html` / `components/module_form.html` permanecen como infraestructura reutilizable; no deben eliminarse mientras existan pruebas o componentes que dependan de ellos.
- La revision visual se valido por codigo y pruebas; queda pendiente una pasada manual en navegador por viewport movil si se requiere certificacion visual completa.
- La configuracion de produccion requiere valores reales de dominio, secretos y servicios antes del despliegue.

## Recomendaciones

- Mantener la suite automatizada como gate minimo antes de cada demostracion.
- Ejecutar tambien `python manage.py check --deploy --settings=config.settings.production` en un entorno de despliegue con sus variables configuradas.
- Mantener smoke tests de rutas junto con las pruebas funcionales.
- Evitar enlaces placeholder y separar siempre color de estado y color de severidad.
- Antes de defensa o despliegue, ejecutar revision manual con datos reales del flujo completo RF01-RF11.
