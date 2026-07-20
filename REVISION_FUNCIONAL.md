# Revision funcional del proyecto

## Resumen general

Se realizo una revision funcional tipo QA sobre la plataforma Django ISTQB Testing Platform, enfocada en navegacion, botones, enlaces, formularios, CRUD, permisos, flujo funcional RF01-RF11 y consistencia general de interfaz.

El objetivo fue verificar funcionamiento, no agregar nuevas funcionalidades. Las correcciones realizadas mantienen la logica existente.

## Estado del proyecto

El proyecto se encuentra funcional para demostracion con la suite automatizada disponible:

- `98 passed in 138.50s`
- `python manage.py check --settings=config.settings.testing`: sin errores.

La suite cubre flujos de autenticacion, proyectos, requisitos, planes, casos, ejecuciones manuales y automatizadas, riesgos, defectos, trazabilidad, dashboard, fases, notificaciones e informes PDF.

## Errores encontrados

1. Enlace sin funcionalidad en login:
   - Archivo: `src/templates/authentication/login.html`
   - Problema: el enlace "Olvidaste tu contrasena?" apuntaba a `href="#"`.
   - Riesgo: boton/enlace decorativo sin accion real.

2. Colores de defectos poco claros:
   - Archivos: `src/apps/defects/views.py`, `src/templates/defects/index.html`, `src/static/css/main.css`
   - Problema: el estado `Abierto` estaba representado con estilo `danger`, por lo que casi todos los defectos aparecian rojos aunque su severidad fuera media o baja.
   - Riesgo: perdida de significado visual; rojo parecia criticidad aunque solo indicaba estado abierto.

3. Artefactos temporales generados por pruebas:
   - `__pycache__` regenerados durante ejecucion de tests.
   - `src/.coverage` generado por `pytest-cov`.
   - `.pytest_cache` regenerado por pytest y bloqueado por Windows.

## Errores corregidos

- Se elimino el enlace `href="#"` de recuperacion de contrasena en login, ya que no existe flujo implementado para esa funcionalidad.
- Se ajusto la semantica visual de defectos:
  - `Abierto` ahora usa tono ambar/naranja suave.
  - Rojo queda reservado para severidad/prioridad critica.
  - Alta usa naranja, media amarillo suave y baja gris.
  - El icono del defecto toma color segun severidad.
- Se eliminaron `__pycache__` regenerados.
- Se elimino `src/.coverage`.

## Archivos modificados

- `src/templates/authentication/login.html`
- `src/apps/defects/views.py`
- `src/templates/defects/index.html`
- `src/static/css/main.css`
- `REVISION_FUNCIONAL.md`

Ademas, existen cambios previos en el arbol de trabajo que no forman parte exclusiva de esta revision y no fueron revertidos.

## Funcionalidades verificadas

- RF01 Gestion de usuarios y proyecto.
- RF02 Gestion de requisitos.
- RF03 Plan de pruebas.
- RF04 Analisis de incidencias/riesgos.
- RF05 Casos de prueba.
- RF06 Ejecucion manual y semi-automatizada.
- RF07 Defectos.
- RF08 Trazabilidad.
- RF09 Dashboard.
- RF10 Informe PDF.
- RF11 Control de fases.

## Botones corregidos

- Login: se retiro el enlace decorativo sin accion real.
- Defectos: se mantuvieron acciones reales de crear, editar y eliminar; se corrigio la interpretacion visual de estado/severidad para que los botones y etiquetas no induzcan a error.

## Enlaces corregidos

- Eliminado `href="#"` en `authentication/login.html`.

Busqueda posterior:

- No se encontraron `href="#"`.
- No se encontraron `javascript:void`.
- No se encontraron textos `Lorem/lorem`.

## Formularios corregidos

No se detectaron formularios rotos en la suite automatizada. Se verifico:

- Login y registro.
- Proyecto.
- Requisitos e importacion desde PDF.
- Planes de prueba.
- Casos de prueba.
- Ejecuciones y evidencia.
- Reglas automatizadas.
- Riesgos/incidencias.
- Defectos.
- Reportes.
- Revision docente de ejecuciones.

## CRUD verificados

La suite valida operaciones de creacion, lectura, actualizacion y eliminacion en:

- Proyectos.
- Requisitos.
- Planes de prueba.
- Casos de prueba.
- Ejecuciones.
- Reglas automatizadas.
- Incidencias/riesgos.
- Defectos.
- Reportes.
- Notificaciones.
- Fases.

## Pantallas revisadas

- Landing.
- Login.
- Registro.
- Dashboard.
- Proyectos.
- Requisitos.
- Importacion de requisitos.
- Planes de prueba.
- Casos de prueba.
- Ejecuciones.
- Historial de ejecuciones.
- Calendario de ejecuciones.
- Incidencias/riesgos.
- Defectos.
- Trazabilidad.
- Reportes.
- Detalle de reporte.
- Notificaciones.
- Fases.
- Perfil.

## Problemas pendientes

- `.pytest_cache` queda bloqueado por Windows despues de ejecutar pruebas; esta en `.gitignore`, pero debe eliminarse manualmente cuando el sistema libere el bloqueo.
- `apps/core/module_views.py` y los templates `components/module_index.html` / `components/module_form.html` no estan conectados a URLs activas. No rompen el sistema, pero son candidatos a limpieza si se confirma que no se usaran como scaffolding.
- La revision visual se valido por codigo y pruebas; queda pendiente una pasada manual en navegador por viewport movil si se requiere certificacion visual completa.
- La configuracion de produccion aun requiere valores reales de dominio y hardening antes de despliegue.

## Recomendaciones

- Mantener la suite de 98 pruebas como gate minimo antes de cada demostracion.
- Agregar pruebas de smoke test para renderizar todas las rutas principales autenticadas.
- Evitar enlaces placeholder; si una funcionalidad no existe, no mostrarla.
- Separar color de estado y color de severidad en todos los modulos donde aplique.
- Antes de defensa o despliegue, ejecutar revision manual con datos reales del flujo completo RF01-RF11.
