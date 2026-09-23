# Auditoría y redimensionamiento integral de ISTQB Testing Platform

**Repositorio evaluado:** `JavierIsma05/istqb-testing-platform`  
**Rama y commit de referencia:** `main`, `c428828e9bf1366596b1d43ead2016201c62a896`  
**Fecha de auditoría:** 23 de septiembre de 2026  
**Alcance:** auditoría de arquitectura, datos, ciclo de vida de pruebas, trazabilidad, testware, riesgos, defectos, ejecución, métricas, frontend, seguridad, pruebas y una mejora vertical de bajo riesgo.

## 1. Resumen ejecutivo

La plataforma es una aplicación Django modular para administrar un flujo académico y operativo de pruebas. **No es un CRUD superficial**: conecta proyectos, requisitos, planes, casos, ejecuciones, evidencias, defectos, riesgos, trazabilidad, revisiones docentes, métricas, reportes, auditoría y fases del ciclo.

La evidencia permite afirmar que el sistema representa una parte amplia del flujo fundamental de gestión de pruebas basado en conceptos de ISTQB. No permite afirmar que implemente todo ISTQB Foundation Level ni que sea conforme o certificado por ISTQB. El alcance visible es una **plataforma académica avanzada, funcionalmente presentable y parcialmente gobernada**.

La diferencia principal entre “la aplicación funciona” y “la aplicación representa adecuadamente un proceso de gestión de pruebas” se encuentra en el contexto de control. El sistema ejecuta y conserva resultados, pero todavía mezcla ejecuciones de diferentes iteraciones porque no existe un contenedor formal de campaña o `TestRun`. Además, los riesgos tienen probabilidad, impacto y mitigación, pero hasta esta auditoría no tenían responsable, plan de contingencia ni fecha de revisión. La cobertura de requisitos puede provenir de una relación directa o de `TraceabilityLink`, lo que es útil, pero exige una convención más explícita para evitar interpretaciones distintas.

Como mejora implementada en esta intervención, el módulo de riesgos ahora permite registrar **responsable**, **plan de contingencia** y **fecha de revisión**. El cambio conserva compatibilidad con datos existentes, usa una migración aditiva y deja evidencia en la bitácora de auditoría. No se reescribieron tecnologías ni módulos completos.

## 2. Arquitectura actual

El proyecto utiliza Django 6.0.5 con PostgreSQL como configuración base y SQLite para pruebas locales. La organización por aplicaciones de dominio es adecuada para una plataforma de gestión de pruebas:

| Capa | Implementación | Evidencia principal | Evaluación |
|---|---|---|---|
| Configuración | Settings base, development, testing, testing_postgres y production | `src/config/settings/` | Implementada |
| Dominio | Apps separadas para proyectos, requisitos, planes, casos, ejecuciones, defectos, incidentes, trazabilidad, reportes, fases, usuarios, notificaciones y auditoría | `src/apps/` | Implementada y modular |
| Persistencia | Modelos Django, relaciones FK/M2M, restricciones y migraciones | `src/apps/*/models.py`, `migrations/` | Implementada |
| Presentación | Templates Django, Bootstrap, CSS propio, JavaScript y layout con sidebar | `src/templates/`, `src/static/` | Implementada |
| Autenticación | Usuario personalizado con email y roles ADMIN, TEACHER y STUDENT | `src/apps/users/models/user.py` | Implementada |
| Autorización | Filtros de proyectos visibles, decoradores y reglas por rol | `src/apps/core/permissions.py` | Implementada, con lógica distribuida en algunas vistas |
| API | Endpoints JSON para consultas docentes y ejecución automatizada | `src/apps/executions/aux_views.py`, `urls.py` | Parcial y acotada |
| Reportes | HTML, PDF, CSV y métricas de calidad | `src/apps/reports/`, `traceability/export.py` | Implementada |
| Auditoría | Registro de actor, acción, entidad y metadata | `src/apps/audit/` | Implementada |
| Despliegue | Docker Compose, Gunicorn, PostgreSQL y pipeline GitHub Actions | `docker/`, `.github/workflows/ci.yml` | Implementado técnicamente |

La principal deuda arquitectónica está en el tamaño de algunas unidades. `src/apps/reports/views.py`, `src/static/css/main.css`, `src/static/js/main.js` y `src/apps/executions/views.py` concentran muchas responsabilidades. La aplicación mantiene una separación por dominio, pero no siempre una separación suficiente entre HTTP, consultas, reglas de negocio, cálculo de métricas y generación de documentos.

## 3. Inventario funcional

| Módulo | Funcionalidad | Entidades involucradas | Archivos principales | Estado actual |
|---|---|---|---|---|
| Usuarios y autenticación | Registro, login, logout, perfil y roles | `User`, `Profile` | `apps/users`, `apps/authentication` | Implementada |
| Proyectos | Crear, editar, listar, cerrar y asociar miembros/tutor | `Project`, `User` | `apps/projects` | Implementada |
| Requisitos | Crear, editar, revisar, aprobar, importar y versionar | `Requirement`, `RequirementVersion` | `apps/requirements` | Implementada; conceptualmente incompleta como base de pruebas porque no existe una entidad separada de condición de prueba |
| Planes | Objetivo, alcance, estrategia, tipos, criterios, umbrales, recursos, ambiente y responsabilidades | `TestPlan`, `TestPlanVersion` | `apps/testplans` | Implementada con buena cobertura documental |
| Casos | Técnicas, nivel, precondiciones, datos, pasos, resultado esperado y tipo manual/automatizado | `TestCase`, `TestCaseVersion`, `TestData` | `apps/testcases`, `apps/executions` | Implementada |
| Riesgos | Probabilidad, impacto, nivel calculado, mitigación, relación con requisito/plan/casos | `Incident` | `apps/incidents`, `apps/testplans/risks.py` | Parcial; mejorada en esta intervención con responsable, contingencia y revisión |
| Ejecución | Manual, automatizada, por pasos, resultados, logs, entorno y evidencias | `TestExecution`, `TestStepExecution`, `AutomatedValidationRule`, `AutomatedExecutionResult` | `apps/executions` | Implementada; falta campaña o ciclo formal |
| Defectos | Registro, asignación, estados, historial, ejecución originadora y confirmación | `Defect`, `DefectHistory` | `apps/defects` | Implementada; faltan causa raíz, versión encontrada/corregida y clasificación más precisa de anomalías |
| Trazabilidad | Matriz requisito-caso-ejecución-defecto, cobertura y exportación | `TraceabilityLink` y relaciones directas | `apps/traceability` | Implementada; la cadena no está versionada de extremo a extremo |
| Reportes | Resumen, cobertura, defectos, ejecuciones, métricas y PDF | `Report`, `ReportDownload` | `apps/reports` | Implementada; principalmente snapshot y con poca tendencia histórica |
| Fases | Progreso, criterios de entrada/salida y control académico del ciclo | `TestingPhase` | `apps/phases` | Implementada como control transversal, no como orquestador completo del STLC |
| Auditoría | Bitácora de acciones y exportaciones | `AuditLog` | `apps/audit` | Implementada |
| Notificaciones | Mensajes por usuario y proyecto | `Notification` | `apps/notifications` | Implementada |
| Borradores | Persistencia temporal por usuario y módulo | `Draft` | `apps/drafts` | Implementada, auxiliar |

No se observa un módulo completo para revisiones estáticas, condiciones de prueba, baselines, releases, builds, pruebas no funcionales o cierre formal con lecciones aprendidas. Cuando una práctica no puede demostrarse con la evidencia del repositorio, se clasifica como **no verificable con la evidencia disponible** o **no implementada**, no como existente por el nombre de una pantalla.

## 4. Mapeo contra ISTQB Foundation Level

El CTFL v4.0 cubre fundamentos, actividades durante el ciclo de vida, pruebas estáticas, análisis y diseño, gestión de actividades, defectos y herramientas [1]. El sistema cubre una parte importante de la gestión operativa, pero no todo el alcance.

| Área ISTQB/testing | Lo que existe actualmente | Evidencia | Nivel | Brecha principal |
|---|---|---|---|---|
| Fundamentos y objetivos | La interfaz y documentación presentan la plataforma como gestión del ciclo de pruebas | `README.md`, templates y `phases` | Parcial | No existe un modelo explícito que obligue a relacionar cada actividad con su objetivo de calidad |
| Planificación | Plan con objetivo, alcance, estrategia, tipos, criterios, recursos, ambiente y responsabilidades | `TestPlan` | Completo para el alcance actual | Falta aprobación formal con baseline, supuestos, dependencias y riesgos residuales |
| Monitoreo y control | Fases, métricas, dashboard, alertas visuales y criterios de salida | `phases`, `reports`, `dashboard` | Parcial | No hay series temporales ni decisiones/acciones correctivas registradas como objetos |
| Análisis de pruebas | Requisitos, criterios de aceptación y bloqueo de ejecución sin requisito aprobado | `Requirement`, `lifecycle.py` | Parcial | No hay entidad “condición de prueba” derivada o revisada explícitamente |
| Diseño de pruebas | Catálogo de técnicas, niveles, pasos, datos y resultados esperados | `TestCase` | Parcial | Las técnicas son principalmente etiquetas; faltan particiones, límites, reglas o estados documentados |
| Implementación/preparación | Pasos estructurados, datos, reglas automatizadas y evidencias | `steps_data`, `TestData`, automation rules | Parcial | Falta paquete de prueba versionado y configuración reproducible de una campaña |
| Ejecución | Resultados NOT RUN, RUNNING, PASSED, FAILED, BLOCKED y ERROR; ejecución manual/automática | `TestExecution` | Completo en ejecución individual | Falta `TestRun`/campaña, build, versión del producto y alcance de casos |
| Evaluación y reporte | Revisión docente, métricas, PDF, CSV y reportes de plan | `reports`, `quality_metrics.py` | Parcial-alto | Los reportes no siempre quedan ligados a una baseline completa |
| Finalización | Criterios de salida y estado CLOSED del plan | `lifecycle.py`, `TestPlan.Status` | Parcial | Falta acta de cierre, riesgos residuales, lecciones aprendidas y aceptación formal |
| Gestión de riesgos | Probabilidad, impacto, nivel, mitigación, plan y vínculos | `Incident` | Parcial | La gestión no prioriza automáticamente casos ni conserva historial específico de revisiones |
| Gestión de defectos | Flujo detectado, análisis, progreso, resolución, confirmación, cierre y reapertura | `Defect`, `lifecycle.py` | Parcial-alto | Faltan clasificación de anomalía, causa raíz, versiones, impacto operativo y motivo formal de cierre |
| Gestión de configuración | Versiones de requisitos, planes y casos | `RequirementVersion`, `TestPlanVersion`, `TestCaseVersion` | Bajo | No existe baseline integral que incluya producto, build, ambiente, datos y evidencias |
| Pruebas estáticas | No se observa módulo de revisión de documentos o hallazgos | Sin entidad o rutas equivalentes | No implementado | Crear revisiones, checklist, hallazgos y decisión de aceptación |
| Pruebas no funcionales | No se observa catálogo operativo de rendimiento, seguridad, accesibilidad o compatibilidad | No verificable con la evidencia disponible | No implementado | Crear tipos, criterios, resultados y evidencias específicas |
| Herramientas | Playwright acotado y Selenium en pruebas del producto | `automated_runner.py`, `tests/selenium` | Parcial | Falta importación de JUnit/Allure y asociación con builds/commits |

La definición oficial de testing basado en riesgos exige que la gestión, selección, priorización y uso de actividades y recursos se basen en tipos y niveles de riesgo [2]. El sistema calcula `risk_level`, pero todavía no usa de forma automática ese nivel para seleccionar, priorizar o justificar el alcance de las pruebas. Por eso la clasificación correcta es **gestión de riesgos parcial**, no completa.

## 5. Análisis del STLC

| Etapa STLC | Implementación actual | Evidencia en código | Datos gestionados | Trazabilidad | Vacíos | Mejora propuesta |
|---|---|---|---|---|---|---|
| Requisitos | Registro, tipo, prioridad, aceptación, revisión y versiones | `requirements/models.py` | Título, descripción, aceptación, prioridad, estado | Requisito → caso directo o `TraceabilityLink` | No hay condición de prueba separada | Crear `TestCondition` cuando el volumen metodológico lo justifique |
| Análisis | Validaciones, aprobación y relación con riesgos | `core/lifecycle.py`, `incidents` | Criterios de aceptación, riesgo y estado | Indirecta hacia casos | No se conserva la decisión analítica | Registrar condición, fuente, riesgo y cobertura |
| Diseño | Casos, técnicas, niveles, pasos, datos y resultados esperados | `testcases/models.py` | Testware ejecutable | Caso → requisito | Técnica sin estructura metodológica suficiente | Plantillas por técnica y justificación de diseño |
| Implementación/preparación | Casos listos, pasos JSON, datos y reglas automatizadas | `testcases`, `executions` | Datos, pasos, selectores, URLs y reglas | Caso → ejecución | No hay set/campaña ni baseline | Crear `TestRun` con plan, versión, ambiente y alcance |
| Ejecución | Ejecución manual/automatizada, pasos, tiempos, evidencias y revisión | `executions` | Resultado, evidencia, logs, ambiente, usuario | Caso → ejecución → pasos | Ejecuciones no agrupadas por ciclo | Implementar campaña de ejecución y comparación entre ciclos |
| Evaluación | Agregación de estados y revisión docente | `views.py`, `services/review.py` | Resultado global, porcentaje y revisión | Ejecución → resultado | No hay decisión formal separada del estado | Registrar decisión, criterio evaluado y responsable |
| Reporte | Reportes de plan, métricas, PDF y CSV | `reports`, `traceability` | Snapshots y métricas | Usa relaciones actuales | Poca evolución histórica | Guardar periodo, baseline y fuente de cada métrica |
| Cierre | Estados CLOSED, umbrales y criterios de salida | `lifecycle.py`, `reports` | Cobertura, aprobación, defectos críticos | Plan → reporte | No hay cierre formal completo | Acta, riesgos residuales, lecciones aprendidas y aceptación |

## 6. Auditoría de trazabilidad

La cadena técnica observable es:

> `Project → Requirement → TestPlan → TestCase → TestExecution → TestStepExecution → Defect → Report`

La relación requisito-caso tiene dos caminos: `TestCase.requirement` como requisito principal y `TraceabilityLink` como relación adicional muchos-a-muchos. Esta decisión permite cobertura múltiple, pero produce dos fuentes de verdad. `TestCase.associated_requirements` y los servicios de trazabilidad intentan consolidarlas, aunque los reportes deben mantener siempre la misma convención.

| Relación | Tipo actual | Integridad | Observación |
|---|---|---|---|
| Proyecto → requisito | FK obligatoria | Buena | Un requisito no puede cambiar de proyecto después de creado |
| Proyecto → plan | FK | Buena | Hay validación temporal contra fechas del proyecto |
| Plan → caso | FK obligatoria | Buena | El plan no puede cambiarse en un caso existente |
| Requisito → caso principal | FK opcional en modelo, obligatoria por `clean()` | Buena con regla de dominio | El modelo conserva una relación canónica |
| Requisito ↔ caso adicional | `TraceabilityLink` | Buena | Restricción única y validación de proyecto |
| Caso → ejecución | FK | Buena | Permite historial, confirmación y regresión |
| Ejecución → pasos | FK con número único por ejecución | Buena | Conserva resultados por paso y evidencia |
| Ejecución → defecto | FK directa y relación inversa | Parcial | Un defecto puede tener ejecución originadora y confirmación, pero el modelo no formaliza todas las clasificaciones |
| Defecto → requisito | Indirecta mediante caso | Parcial | Si el caso cambia de lógica, la relación depende de mantener el caso y sus vínculos |
| Riesgo → caso | M2M desde `TestCase.covered_risks` | Parcial | La relación existe, pero no conserva la justificación o fecha de cobertura |
| Artefactos → versión | Snapshots de requisito/plan/caso | Parcial | No cubre ambiente, producto, build, datos y evidencias en una baseline única |
| Ejecución → reporte | Consulta agregada | Parcial | El reporte puede regenerarse, pero no siempre conserva la selección exacta de datos que lo produjo |

**Pérdida de información:** se pierde contexto entre ejecuciones de diferentes iteraciones, versiones del producto y ambientes. La solución de mayor valor es un contenedor `TestRun` antes de agregar más métricas.

## 7. Campos y entidades faltantes

Los campos no deben agregarse solo porque aparecen en un glosario. Deben resolver una decisión del proceso.

| Necesidad | Evidencia actual | Consecuencia | Recomendación |
|---|---|---|---|
| Responsable y seguimiento de riesgo | Antes solo había `reported_by` | El riesgo podía existir sin propietario operativo | **Implementado:** `owner`, `review_date` |
| Acción si el riesgo ocurre | Solo existía mitigación preventiva | No se distinguía reducción preventiva de contingencia | **Implementado:** `contingency_plan` |
| Condición de prueba | El requisito pasa directamente al caso | No se conserva la descomposición analítica | P1: nueva entidad si el uso metodológico lo exige |
| Campaña de ejecución | Cada ejecución es independiente | No se puede comparar una iteración completa | P0/P1: `TestRun` |
| Baseline | Existen versiones parciales | La ejecución no identifica producto, build y conjunto de testware | P1: baseline compuesta |
| Defecto técnico completo | Existen descripción, pasos, severidad, prioridad y resolución | Falta contexto de versión y causa | P1: versión encontrada, versión corregida, componente, causa y motivo de cierre |
| Cierre de pruebas | Hay criterios y veredicto | Falta responsabilidad y aceptación formal | P2: `TestClosure` o snapshot de cierre |

## 8. Testware administrado

| Testware | ¿Existe? | Dónde | Relación | Evaluación |
|---|---|---|---|---|
| Requisitos | Sí | `Requirement` | Proyecto, casos, vínculos | Implementado |
| Plan | Sí | `TestPlan` | Proyecto, casos, riesgos, reportes | Implementado |
| Condiciones de prueba | No como entidad | No verificable | Implícitas en aceptación y casos | Conceptualmente incompleto |
| Casos | Sí | `TestCase` | Requisitos, plan, ejecuciones | Implementado |
| Datos | Sí, principalmente texto/variables | `TestCase.test_data`, `TestData` | Caso y ejecución | Parcialmente estructurado |
| Procedimientos | Sí, pasos del caso | `steps`, `steps_data` | Caso y resultados por paso | Implementado |
| Scripts | Parcial | Reglas Playwright y salida generada | Caso y ejecución automática | Acotado a reglas seguras |
| Evidencias | Sí | Archivos generales y por paso | Ejecución y paso | Implementado |
| Resultados | Sí | `TestExecution`, `TestStepExecution` | Caso, defecto, revisión | Implementado |
| Incidentes/riesgos | Sí | `Incident` | Proyecto, requisito, plan, casos | Parcial, mejorado |
| Defectos | Sí | `Defect`, `DefectHistory` | Caso, ejecución, confirmación | Implementado con brechas |
| Informes | Sí | `Report` y vistas PDF/CSV | Proyecto/plan | Implementado |
| Matriz | Sí | `TraceabilityLink` y vistas | Requisito-caso-ejecución-defecto | Implementada, sin baseline integral |

## 9. Riesgos y defectos

### Riesgos

El flujo actual es `OPEN → ANALYSIS → MITIGATED → CLOSED`, con validación de mitigación antes de mitigar o cerrar. Se registra probabilidad, impacto y un nivel calculado. Esta estructura es razonable como primer registro de riesgo.

La mejora implementada añade:

- `owner`: responsable operativo del riesgo, limitado a usuarios visibles del proyecto.
- `contingency_plan`: acción prevista cuando el riesgo se materializa.
- `review_date`: fecha explícita para el siguiente seguimiento.

Los nuevos campos se muestran en el formulario y en el listado. También se registran en la metadata de auditoría. La migración es aditiva y permite valores nulos o vacíos para no invalidar datos existentes.

### Defectos

El flujo implementado es:

> `OPEN → ANALYSIS → IN_PROGRESS → RESOLVED → PENDING_CONFIRMATION → CLOSED`

También admite reapertura, rechazo y duplicado. El cierre exige una ejecución de confirmación aprobada. Esta es una fortaleza clara de gobernanza.

Las brechas pendientes son la clasificación formal entre defecto, falso positivo, cambio, duplicado y no reproducible; causa raíz; componente; versión encontrada/corregida; ambiente de reproducción; impacto; fecha objetivo; motivo de cierre y verificador. No se agregaron en esta intervención porque requieren una decisión de diseño más amplia y una migración que debe coordinarse con reportes y estados.

## 10. Ejecución y evidencia

La ejecución manual exige requisito aprobado, resultado obtenido y evidencia. Los pasos pueden registrar acción, esperado, obtenido, estado, comentario, archivo, captura y log. La agregación determina el resultado general dando prioridad a `FAILED` y luego `BLOCKED`. La ejecución automatizada usa reglas seguras de Playwright, URLs autorizadas, selectores y comparadores.

La cadena `caso → ejecución → resultado → evidencia → defecto` es funcional. La inconsistencia principal no está en la persistencia individual, sino en el contexto: falta una entidad que responda “¿a qué campaña, versión, build y alcance pertenece esta ejecución?”. También falta una separación completa entre una ejecución planificada y una ejecución realmente realizada.

## 11. Reportes y métricas

Existen métricas de cobertura de requisitos, requisitos aprobados, ejecución de casos, tasa de aprobación, revisión docente, evidencia por paso, defectos abiertos, defectos críticos y trazabilidad. Estas métricas responden decisiones útiles, como determinar si el plan tiene cobertura o si la evidencia es suficiente.

La métrica `traceability_index` es una decisión propia del proyecto. No es una fórmula oficial de ISTQB y debe presentarse como indicador interno. Las métricas actuales son principalmente fotografías del estado; no hay una serie histórica general que permita observar tendencia, velocidad de cierre, crecimiento de defectos o evolución de cobertura por ciclo.

La principal mejora recomendada es asociar cada métrica a una fecha de corte, una campaña, una versión del producto, un plan y una definición explícita. No conviene añadir indicadores sin una decisión asociada.

## 12. Frontend, UX y UI

La interfaz tiene una arquitectura visual consistente: sidebar persistente, agrupación por diseño/ejecución/informes, tarjetas de métricas, badges, tablas responsive, mensajes de estado y modal de confirmación. La navegación comunica razonablemente que el producto gestiona un ciclo de pruebas.

El flujo principal es reconocible:

> Proyecto → Requisitos → Plan → Casos → Ejecución → Defecto → Trazabilidad → Reporte

Los principales problemas UX son de orientación metodológica, no de estética. “Plan de pruebas” y “Fases ISTQB” no siempre explican qué actividad está pendiente ni qué dato produce. El usuario puede ver un caso listo para ejecutar sin comprender completamente la relación con el criterio de entrada. La matriz muestra los vínculos, pero el estado de cada enlace y su justificación pueden quedar densos en pantallas grandes.

La interfaz de riesgos ahora muestra responsable y próxima revisión, lo que convierte un registro estático en una actividad de seguimiento. El próximo rediseño debe añadir mensajes de “siguiente acción” y estados vacíos que indiquen la actividad del proceso, no solo el nombre del módulo.

No se realizó una validación visual automatizada completa ni una revisión con lectores de pantalla. Por tanto, accesibilidad visual y responsive completo quedan **no verificables con la evidencia ejecutada en esta sesión**.

## 13. Arquitectura técnica y calidad

Fortalezas técnicas:

- Separación por apps de dominio.
- Validaciones de modelo para integridad de proyecto, fechas y relaciones.
- Restricciones únicas para códigos y pasos.
- Filtros de visibilidad por usuario y proyecto.
- Protección CSRF y decoradores de login.
- Configuración de producción separada.
- Pipeline de CI con PostgreSQL, migraciones y pruebas.
- Pruebas de ciclo de vida, seguridad, permisos, API y ejecución.

Deuda técnica:

- Vistas grandes y con consultas, reglas de negocio y presentación mezcladas.
- `reports/views.py` concentra generación de datos, narrativa y PDF.
- La relación directa y muchos-a-muchos de requisitos exige una convención documentada.
- Hay muchas migraciones de reconciliación en planes y ejecuciones; no es un error inmediato, pero aumenta el costo de mantenimiento.
- Los documentos existentes son útiles, pero algunas conclusiones anteriores deben actualizarse al commit actual.
- La suite no cubre de forma equivalente todas las rutas de navegador y pruebas PostgreSQL dentro de esta sesión.

## 14. Matriz maestra de comparación

| Área | Actual | Evidencia | Nivel | Brecha | Mejora |
|---|---|---|---|---|---|
| Proyectos | CRUD, miembros, tutor, estados | `projects/models.py` | Completo | No hay release formal | Añadir release/baseline |
| Requisitos | Tipo, prioridad, aceptación, revisión, versión | `requirements/models.py` | Parcial-alto | Falta condición de prueba | Crear entidad y revisión analítica |
| Planificación | Objetivo, alcance, estrategia, criterios, umbrales | `testplans/models.py` | Completo para MVP | Falta aprobación baseline | Aprobar versión con actor, fecha y comentario |
| Diseño | Casos, técnicas, pasos, resultado esperado | `testcases/models.py` | Parcial-alto | Técnica no suficientemente estructurada | Plantillas de diseño por técnica |
| Riesgos | Probabilidad, impacto, mitigación, vínculos, propietario y revisión | `incidents/models.py` | Parcial mejorado | Priorización no automatizada | Vincular nivel a prioridad y cobertura |
| Ejecución | Manual, automática, pasos, resultados, evidencia | `executions/models.py` | Parcial-alto | Sin campaña | Crear `TestRun` |
| Defectos | Workflow, historial, confirmación y reapertura | `defects`, `core/lifecycle.py` | Parcial-alto | Faltan clasificación y causa | Completar campos y reglas por estado |
| Trazabilidad | Matriz y exportación | `traceability` | Parcial-alto | No versionada de extremo a extremo | Baseline integral |
| Reportes | HTML, PDF, CSV y métricas | `reports` | Parcial-alto | Sin tendencia suficiente | Series históricas por campaña |
| Configuración | Versiones de entidades | migrations/version models | Bajo | No hay build/release/ambiente como baseline | Modelo de configuración |
| Estático | No observable | Sin app equivalente | No implementado | No hay revisiones | Módulo de reviews |
| No funcional | No observable como flujo | Sin entidades equivalentes | No implementado | No hay criterios específicos | Tipos y resultados NFR |
| Seguridad | Roles, filtros, CSRF, restricciones de uploads | `permissions.py`, tests | Parcial-alto | Requiere ampliar pruebas de navegador | Suite de permisos por CRUD |
| CI | GitHub Actions, PostgreSQL, migraciones, pytest | `.github/workflows/ci.yml` | Implementado | Browser/E2E separado | Ejecutar y publicar artefactos E2E |

## 15. Valoración de madurez

No se usa una puntuación arbitraria. La valoración se basa en diez capacidades observables:

1. Cobertura funcional del flujo.
2. Cobertura del STLC.
3. Trazabilidad.
4. Gestión de testware.
5. Gestión de defectos.
6. Gestión de riesgos.
7. Ejecución y evidencia.
8. Reportes y decisión.
9. Configuración y baselines.
10. Calidad técnica, seguridad y pruebas.

Con criterios cualitativos y evidencia de código, la plataforma se ubica en **madurez 3 de 5: proceso definido y parcialmente gestionado**. Esta escala es interna y no es una escala oficial de ISTQB.

La justificación es: el núcleo operativo está bien definido; la ejecución, evidencia, revisión, defectos y trazabilidad tienen implementación real; pero las campañas, configuración, pruebas estáticas, no funcionales, cierre formal y seguimiento histórico todavía no tienen representación completa.

## 16. Rediseño funcional propuesto

La arquitectura objetivo debería conservar las apps existentes y añadir capacidades transversales, no reemplazar el sistema:

```text
Proyecto
 ├── Baseline / Release / Build / Ambiente
 ├── Requisitos
 │    └── Condiciones de prueba
 ├── Plan de pruebas
 │    ├── Riesgos y respuestas
 │    ├── Casos y testware
 │    └── Criterios de entrada/salida
 ├── TestRun / Campaña
 │    ├── Alcance de casos
 │    ├── Ejecuciones
 │    ├── Evidencias
 │    └── Resultados
 ├── Defectos / Incidentes
 ├── Trazabilidad versionada
 └── Reporte y cierre
```

Debe mantenerse la relación directa `TestCase.requirement` como requisito principal y documentarse que `TraceabilityLink` representa coberturas adicionales. La futura campaña debe ser el contexto común de ejecuciones, reportes y comparaciones.

## 17. Plan de implementación priorizado

| Prioridad | Cambio | Justificación | BD | Backend | Frontend | Riesgo |
|---|---|---|---|---|---|---|
| P0 | Mantener bloqueos de ejecución, permisos, migraciones y CI | Protege integridad y trazabilidad actuales | Ninguna | Reforzar pruebas | Mensajes claros | Bajo |
| P0 | Crear `TestRun` o campaña de ejecución | Evita mezclar iteraciones y permite comparar resultados | Nueva entidad y FK opcional inicialmente | Servicios y validaciones | Crear/listar/asignar campaña | Medio |
| P1 | Baseline de release, ambiente y build | Hace reproducible la conclusión | Nuevas entidades o snapshot | Asociar a `TestRun` y reportes | Selector y detalle | Medio |
| P1 | Completar gestión de riesgos | Necesita propietario, contingencia y seguimiento | **Implementado en esta sesión** | Formulario, scope y auditoría | Formulario/listado actualizado | Bajo |
| P1 | Fortalecer defectos | Mejora análisis y cierre | Campos y reglas condicionadas | Servicios de transición | Formulario y detalle | Medio |
| P1 | Revisiones estáticas | Cubre una parte ausente del CTFL | Review, checklist, finding | Flujo de aceptación | Nuevo módulo | Medio |
| P2 | Diseño asistido por técnicas | Convierte etiquetas en evidencia metodológica | Particiones, límites, reglas, estados | Validaciones y cobertura | Asistentes | Medio |
| P2 | Tendencias | Permite monitoreo real | Snapshots periódicos | Consultas históricas | Gráficos | Medio |
| P3 | Pruebas no funcionales e integraciones | Amplía alcance | Tipos, criterios y adaptadores | Importadores JUnit/Allure | Panel de integración | Alto |

## 18. Cambios implementados en esta intervención

Se implementó una mejora vertical y acotada para cerrar una brecha de gestión de riesgos:

- `src/apps/incidents/models.py`: se añadieron `contingency_plan`, `owner` y `review_date`.
- `src/apps/incidents/migrations/0007_incident_contingency_plan_incident_owner_and_more.py`: migración aditiva y compatible con registros existentes.
- `src/apps/incidents/forms.py`: los responsables se filtran por proyectos visibles; se agregaron etiquetas, widgets, ayudas y validación de campos.
- `src/apps/incidents/views.py`: se optimizó la consulta con `select_related('owner')` y se incorporó metadata de responsable y fecha de revisión a la bitácora.
- `src/templates/incidents/form.html`: se incorporaron los tres campos al flujo de alta/edición.
- `src/templates/incidents/index.html`: se muestran responsable y próxima revisión en cada riesgo.
- `src/apps/incidents/tests.py`: se añadieron pruebas de alcance de responsables y persistencia de metadata.

No se eliminó ninguna funcionalidad, no se cambió de tecnología y no se alteraron relaciones existentes. La mejora no pretende resolver todo el déficit de riesgos basado en ISTQB; resuelve el seguimiento mínimo necesario para que el registro tenga propietario, respuesta preventiva/contingente y próxima revisión.

## 19. Pruebas realizadas

| Verificación | Resultado |
|---|---|
| Django `check` con settings de testing | Pasó |
| `makemigrations --check --dry-run` antes del cambio | Pasó |
| Aplicación de migraciones antes del cambio | Pasó |
| Suite no-browser posterior al cambio | **334 pasaron**, 14 fueron excluidas por markers, 22 warnings |
| Cobertura de suite posterior al cambio | 86% |
| Pruebas específicas de incidentes después del cambio | **11 pasaron** |
| `makemigrations --check --dry-run` después del cambio | Pasó |
| Aplicación limpia de todas las migraciones después del cambio | Pasó |
| Pruebas E2E Selenium | No ejecutadas en esta sesión |
| Pruebas Playwright marcadas como externas | No ejecutadas en esta sesión |
| Suite PostgreSQL real | No ejecutada en esta sesión; CI sí la configura |
| Validación visual completa y responsive | No verificable con la evidencia ejecutada |

La suite no-browser completa posterior al último cambio terminó correctamente. Las 14 pruebas excluidas corresponden a markers de navegador/Playwright y no deben interpretarse como pruebas fallidas.

## 20. Riesgos pendientes

Persisten cinco riesgos de producto importantes. Primero, las ejecuciones no están agrupadas por campaña. Segundo, las versiones de entidades no forman una baseline integral. Tercero, el riesgo calculado todavía no prioriza automáticamente pruebas. Cuarto, el defecto no conserva todos los datos recomendables para análisis de causa y versión. Quinto, no hay evidencia suficiente de pruebas estáticas y no funcionales.

También permanece deuda técnica por vistas y hojas de estilo grandes. La corrección debe hacerse por extracción gradual hacia servicios y selectores, con pruebas de regresión, no mediante una reescritura.

## 21. Próximas mejoras

La siguiente entrega debería implementar `TestRun` como agregado de campaña. Debe incluir nombre, plan, versión del producto, ambiente, build, alcance de casos, estado, fechas, responsable y resultado global. Cada ejecución debe poder pertenecer a una campaña sin perder su historial. Los reportes y la matriz deben filtrar por campaña y comparar campañas.

Después conviene introducir una baseline compuesta, fortalecer el flujo de defectos y crear revisiones estáticas. Solo una vez estabilizado ese núcleo se justifica añadir pruebas no funcionales, importadores de herramientas externas y análisis histórico avanzado.

## Referencias

[1]: https://istqb.org/certifications/certified-tester-foundation-level-ctfl-v4-0/ "Certified Tester Foundation Level (CTFL) v4.0 Overview"

[2]: https://glossary.istqb.org/en_US/term/risk-based-testing "ISTQB Glossary — risk-based testing"

[3]: https://github.com/JavierIsma05/istqb-testing-platform "Repositorio istqb-testing-platform"

[4]: https://istqb.org/wp-content/uploads/2024/11/ISTQB_CTFL_Syllabus_v4.0.1.pdf "ISTQB Certified Tester Foundation Level Syllabus v4.0.1"

[5]: https://astqb.org/5-5-defect-management/ "ISTQB Foundation Level Syllabus — Defect Management"

---

**Conclusión:** la plataforma ya tiene una base real y útil para gestionar el proceso de pruebas. Su afirmación técnica correcta es que implementa gran parte del ciclo operativo basado en conceptos ISTQB, no que implemente el estándar completo. La mejora realizada fortalece el gobierno de riesgos sin romper el núcleo existente. El salto de madurez más importante pendiente es introducir campañas de ejecución y baselines completas.
