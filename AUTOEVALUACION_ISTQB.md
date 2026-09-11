# Autoevaluación de la plataforma ISTQB

**Repositorio evaluado:** [JavierIsma05/istqb-testing-platform](https://github.com/JavierIsma05/istqb-testing-platform)  
**Rama evaluada:** `main`  
**Commit de referencia:** `4dc7044` — integración de `fix/flujo-funcional-fase-7-8`  
**Fecha de evaluación:** 11 de septiembre de 2026  
**Autor:** Manus AI

## 1. Conclusión ejecutiva

La plataforma ya implementa un **flujo funcional amplio de gestión del ciclo de vida de pruebas**. Actualmente permite administrar proyectos, requisitos, planes de pruebas, casos de prueba, ejecuciones manuales y automatizadas, evidencias, defectos, trazabilidad, revisiones docentes, auditoría, notificaciones, fases y reportes de calidad.

Mi valoración es que el sistema se encuentra en un nivel de **MVP avanzado o piloto académico**, equivalente aproximadamente a un **nivel 3 de 5: proceso definido y parcialmente gestionado**. Esta escala es una evaluación interna de madurez y **no es una certificación ISTQB ni una escala oficial del ISTQB**.

La plataforma ya tiene una base sólida para demostrar el flujo ISTQB fundamental. Sin embargo, todavía no debería presentarse como una implementación completa del estándar porque faltan capacidades importantes de gobierno de pruebas, gestión formal de riesgos, pruebas estáticas, pruebas no funcionales, configuración de entornos, control de cambios y evidencia de calidad automatizada a nivel de producto.

## 2. Qué está implementado actualmente

| Área del proceso | Evidencia observada en el código | Evaluación actual |
|---|---|---|
| Gestión de proyectos | Aplicación `projects`, participantes y tutores | Implementada |
| Requisitos | Requisitos funcionales y no funcionales, prioridad, estados y versiones | Bien encaminada |
| Plan de pruebas | Objetivo, alcance, estrategia, tipos, criterios de entrada y salida, umbrales, recursos, entorno, responsabilidades, estimación y fechas | Implementada con buena cobertura documental |
| Casos de prueba | Precondiciones, datos, pasos, resultado esperado, prioridad, técnica, nivel, versión y tipo manual/automatizado | Implementada |
| Técnicas de diseño | Partición de equivalencia, valores límite, tabla de decisión, transición de estados, casos de uso, experiencia, caja negra, caja blanca y exploratoria | Catálogo implementado; falta asistencia metodológica y evidencia de uso |
| Trazabilidad | Asociación requisito-caso y matriz de trazabilidad | Implementada |
| Ejecución | Resultados, ejecución manual y automatizada, pasos, evidencias, capturas, logs, ambiente, navegador, duración y notas | Implementada |
| Revisión | Estados de revisión, docente revisor, fecha y notas; recalculo de aprobación después de revisar pasos | Implementada |
| Defectos | Código, descripción, pasos para reproducir, severidad, prioridad, estado, responsable, ejecución relacionada e historial | Implementada, pero requiere fortalecer el flujo de ciclo de vida |
| Incidentes y riesgos | Existe módulo de incidentes y relación de riesgos cubiertos por casos | Parcial; falta formalizar el análisis de riesgo |
| Reportes | Cobertura, ejecuciones, defectos, métricas ISTQB, criterios de salida, veredicto y exportación | Implementada y útil para un piloto |
| Auditoría | Registro de eventos y exportaciones | Implementada |
| Fases del ciclo | Fases, controles y condiciones de avance | Implementada como control académico |
| Automatización | Reglas de validación con Playwright/Chromium, acciones y comparadores | Implementada de forma acotada |
| Pruebas del producto | Pruebas unitarias/integración Django, pruebas de flujo y suites Selenium | Existe una base importante |
| Despliegue | Docker Compose, PostgreSQL y configuración para SQLite local | Implementado técnicamente |

## 3. Comparación con el proceso ISTQB Foundation Level

El CTFL v4.0 organiza el conocimiento alrededor de fundamentos, pruebas durante el ciclo de vida, pruebas estáticas, análisis y diseño, gestión de actividades, gestión de defectos y herramientas de prueba [2]. La comparación siguiente se realiza contra esos temas y contra la evidencia visible en el repositorio.

| Actividad ISTQB | Estado en la plataforma | Qué falta para considerarla más completa |
|---|---|---|
| Planificación de pruebas | **Fuerte** | Convertir el plan en un objeto gobernado con aprobaciones, baselines, cambios y responsables explícitos |
| Monitorización y control | **Medio** | Histórico de métricas por fecha, tendencias, alertas, decisiones y acciones correctivas |
| Análisis de pruebas | **Medio-bajo** | Derivar condiciones de prueba desde requisitos, riesgos y criterios de aceptación; registrar cobertura de condiciones |
| Diseño de pruebas | **Medio** | Asistentes o plantillas para técnicas ISTQB y registro de particiones, límites, reglas y estados cubiertos |
| Implementación de pruebas | **Medio** | Versionado del testware, paquetes de ejecución, orden, dependencias, datos y configuración reproducible |
| Ejecución de pruebas | **Fuerte** | Mejorar reintentos, comparación entre ciclos, ejecución por build y consolidación de resultados automatizados |
| Finalización de pruebas | **Medio-alto** | Acta de cierre, lecciones aprendidas, riesgos residuales, aceptación formal y archivado de testware |
| Gestión de defectos | **Medio** | Workflow configurable, clasificación de anomalía, causa raíz, impacto, resolución, verificación, reapertura y SLA |
| Gestión de configuración | **Bajo** | Versionar aplicación, requisitos, casos, planes, datos, entornos, builds y evidencias con identificadores de baseline |
| Pruebas estáticas | **Bajo o no visible** | Revisiones de requisitos, casos y documentos; hallazgos de revisión; checklist; inspección y análisis estático |
| Pruebas no funcionales | **Bajo** | Rendimiento, seguridad, usabilidad, compatibilidad, accesibilidad, confiabilidad y mantenibilidad |
| Herramientas de prueba | **Medio** | Integraciones con CI/CD, importación de resultados JUnit/Allure, webhooks, APIs y herramientas externas |

## 4. Evaluación específica de plan, casos, ejecuciones y defectos

### 4.1 Plan de pruebas

El plan de pruebas es uno de los componentes más completos. El modelo incluye objetivo, alcance, estrategia, tipos de prueba, criterios de entrada y salida, porcentaje mínimo de aprobación, límite de defectos críticos, cobertura mínima, recursos, entorno, responsabilidades, estimación y fechas.

Esto permite construir un plan operativo razonable. También existen versiones del plan y estados de borrador, revisión, aprobado y cerrado.

Las principales mejoras necesarias son las siguientes:

1. Separar explícitamente **estrategia de pruebas**, **enfoque de pruebas** y **plan de pruebas** cuando el proyecto lo requiera.
2. Asociar cada criterio de salida con una métrica, una fuente de evidencia y una decisión responsable.
3. Registrar supuestos, restricciones, dependencias, riesgos y mitigaciones dentro del plan.
4. Implementar aprobación formal con usuario, fecha, comentario y versión aprobada.
5. Evitar que los umbrales, como cobertura mínima o porcentaje de aprobación, se utilicen como sustituto de un análisis contextual.

### 4.2 Casos de prueba

Los casos ya contemplan técnicas de prueba, nivel, prioridad, precondiciones, datos, pasos, resultado esperado, requisito asociado, versión y ejecución manual o automatizada. Además, la plataforma bloquea la ejecución cuando no existe un requisito aprobado, lo que constituye una regla de gobernanza útil.

El principal riesgo es que el catálogo de técnicas exista solo como una etiqueta. Para demostrar una aplicación real de ISTQB, cada caso debería poder documentar la lógica de diseño utilizada. Por ejemplo, un caso basado en valores límite debería registrar las particiones, límites válidos, límites inválidos y valores seleccionados.

También convendría añadir:

- Identificador de condición de prueba.
- Datos de entrada y datos de salida estructurados.
- Prioridad basada en riesgo.
- Dependencias entre casos.
- Requisitos previos de ambiente.
- Criterio de aprobación del caso.
- Estado de revisión del caso.
- Historial de quién aprobó cada versión.
- Relación con pruebas de regresión y suites.

### 4.3 Ejecución y evidencia

La ejecución es una fortaleza del sistema. Se registran resultados como aprobado, fallido, bloqueado, error técnico y no ejecutado. También se guardan resultados por paso, evidencia general, capturas, logs técnicos, navegador, entorno, URL, duración, ejecutor y revisión.

Esto permite sostener una conclusión con evidencia, no solamente con un estado manual. La revisión docente y el recálculo de la aprobación después de revisar pasos son especialmente adecuados para el contexto académico.

Para subir de nivel, sería conveniente implementar ciclos de ejecución o **test runs** explícitos. Actualmente existe la ejecución individual, pero falta un contenedor completo que represente una versión del producto, una compilación, un sprint, una iteración o una campaña de regresión. Ese contenedor debería conservar el conjunto de casos ejecutados, el entorno, la versión del software y el resultado global.

### 4.4 Defectos

El módulo de defectos contiene los datos esenciales: código, título, descripción, pasos para reproducir, severidad, prioridad, estado, responsable, ejecución relacionada, reportante e historial. El flujo actual contempla estados de apertura, progreso, resolución, cierre y reapertura.

Según la orientación de gestión de defectos del ISTQB, el proceso mínimo debe permitir gestionar una anomalía desde su descubrimiento hasta su cierre, incluyendo registro, análisis, clasificación, decisión de respuesta y cierre [3]. La plataforma cubre gran parte de ese flujo, pero todavía debería distinguir mejor entre:

- Anomalía reportada.
- Defecto confirmado.
- Falso positivo.
- Solicitud de cambio.
- Duplicado.
- No reproducible.
- Rechazado por comportamiento esperado.

También faltan campos o procesos recomendables: causa raíz, componente afectado, versión encontrada, versión corregida, entorno de reproducción, evidencia específica, impacto, fecha objetivo, motivo de cierre, verificador y vínculo con la ejecución de confirmación o regresión.

## 5. Brechas prioritarias

| Prioridad | Brecha | Impacto | Recomendación |
|---|---|---|---|
| P0 | Validar el producto con una suite reproducible en CI | No se puede demostrar de forma continua que los cambios mantienen el flujo | Configurar GitHub Actions para migraciones, pruebas Django, pruebas de flujo y validaciones de seguridad |
| P0 | Robustecer el flujo de defectos | El registro existe, pero la decisión y el cierre pueden quedar ambiguos | Añadir clasificación de anomalía, resolución, causa raíz, verificador y relación con prueba de confirmación |
| P0 | Implementar ciclos de ejecución | Dificulta comparar iteraciones, versiones y regresiones | Crear `TestRun` o campaña de ejecución con versión, ambiente, alcance y resultado global |
| P1 | Formalizar gestión de riesgos | La priorización actual no está completamente basada en riesgo | Crear riesgo con probabilidad, impacto, nivel, mitigación, contingencia, propietario y estado |
| P1 | Añadir pruebas estáticas | Se omite una parte relevante del proceso ISTQB | Crear revisiones de requisitos, casos y documentos con hallazgos y checklist |
| P1 | Fortalecer configuración y baselines | Los cambios de requisitos, planes y casos pueden perder contexto | Asociar cada ejecución y reporte a versiones del producto, plan, casos, datos y ambiente |
| P1 | Completar el catálogo no funcional | El sistema se enfoca principalmente en pruebas funcionales | Añadir tipos, atributos de calidad, criterios y evidencias de rendimiento, seguridad, accesibilidad y usabilidad |
| P2 | Mejorar diseño basado en técnicas | Las técnicas están catalogadas, pero no necesariamente justificadas | Registrar particiones, límites, reglas, estados y cobertura por técnica |
| P2 | Añadir tendencias y análisis histórico | Las métricas actuales son principalmente fotografías del estado | Graficar evolución de cobertura, defectos, tasa de fallos, tiempo de resolución y retrabajo |
| P2 | Integrar herramientas externas | La automatización está limitada a reglas propias | Importar resultados JUnit/Playwright/Allure y enlazar builds, commits y ejecuciones |
| P2 | Mejorar cierre formal | El veredicto automático no reemplaza la aceptación responsable | Crear acta de cierre, riesgos residuales, lecciones aprendidas y aprobación final |

## 6. Nivel estimado por capacidad

| Capacidad | Nivel estimado | Interpretación |
|---|---:|---|
| Gestión documental de pruebas | 4/5 | El plan, los casos, las versiones y los reportes tienen una base sólida |
| Trazabilidad | 3.5/5 | Existe relación requisito-caso-ejecución-defecto, pero falta consolidarla por versiones y campañas |
| Ejecución | 4/5 | Se registran resultados, pasos, evidencias y revisiones |
| Defectos | 3/5 | El flujo básico existe, pero faltan clasificación y cierre con causa y verificación formal |
| Riesgos | 2.5/5 | Hay conceptos y relaciones de riesgo, pero falta un registro y tratamiento completo |
| Pruebas estáticas | 1/5 | No se observa un módulo completo de revisiones estáticas |
| Pruebas no funcionales | 1.5/5 | No se observa cobertura operacional suficiente |
| Configuración y releases | 2/5 | Hay versionado de entidades, pero no una baseline integral del testware y producto |
| Automatización e integración | 2.5/5 | Hay automatización acotada, pero falta integración continua completa |
| Reportes y decisión | 3.5/5 | Hay métricas y veredictos, pero falta mayor contexto histórico y aprobación formal |

## 7. Roadmap recomendado

### Fase 1: confiabilidad y control del núcleo

Primero conviene asegurar el núcleo antes de añadir más módulos. Deben automatizarse las pruebas en GitHub Actions, documentarse los comandos reproducibles, verificar migraciones y crear datos de prueba controlados. También debe añadirse una prueba de regresión específica para el informe de defectos sin responsable y para cada transición crítica del flujo.

El resultado esperado es que cada cambio en `main` ejecute automáticamente las pruebas, informe fallos y conserve evidencia del resultado.

### Fase 2: ejecución por campañas y versiones

La siguiente prioridad es crear la entidad de campaña o ciclo de ejecución. Cada campaña debe apuntar a una versión del producto, un plan, un entorno y un conjunto de casos. Debe permitir ejecutar nuevamente un caso, comparar resultados con la campaña anterior y generar un reporte de regresión.

Esta mejora dará contexto temporal a las métricas y evitará mezclar resultados de diferentes iteraciones.

### Fase 3: gestión formal de defectos y riesgos

Después debe fortalecerse el proceso de defectos. La transición debería exigir campos según el estado. Por ejemplo, cerrar un defecto debería requerir resolución, versión corregida, verificador y evidencia de confirmación.

En paralelo, debe existir un registro de riesgos con probabilidad, impacto, nivel, respuesta, propietario, fecha de revisión y riesgo residual. El ISTQB define las pruebas basadas en riesgos como un enfoque en el que la gestión, selección, priorización y uso de actividades y recursos dependen de los tipos y niveles de riesgo [4].

### Fase 4: calidad amplia y cierre

Finalmente, se deben incorporar revisiones estáticas, pruebas no funcionales, accesibilidad, seguridad básica, rendimiento y un cierre formal con lecciones aprendidas. Estas funciones permitirán que la plataforma represente mejor el proceso completo y no solo la gestión de pruebas funcionales.

## 8. Criterio de “lista para presentación académica”

Para una demostración o tesis, la plataforma puede considerarse **funcionalmente presentable** si se demuestra un flujo reproducible con estos pasos: aprobar requisito, crear plan, diseñar caso, ejecutar caso, registrar evidencia, crear defecto, resolverlo, ejecutar confirmación, actualizar trazabilidad y generar reporte final.

Para una afirmación más fuerte, como “implementa el proceso ISTQB completo”, todavía se necesita demostrar pruebas estáticas, riesgos, configuración, pruebas no funcionales, control de versiones del testware, ejecución por campañas y cierre formal.

La formulación más rigurosa para el estado actual sería:

> La plataforma implementa una solución web para gestionar gran parte del ciclo de vida de pruebas basado en conceptos ISTQB, con énfasis en requisitos, planificación, casos, ejecución, defectos, trazabilidad, revisión y reportes. Su alcance actual corresponde a una implementación académica avanzada y no a una certificación de conformidad completa con ISTQB.

## 9. Veredicto final

**Fortaleza principal:** la plataforma ya conecta los objetos esenciales del proceso: requisito, caso de prueba, ejecución, evidencia, defecto, trazabilidad y reporte.

**Limitación principal:** todavía mide y administra principalmente el flujo operativo, pero no controla con suficiente profundidad el contexto de riesgo, configuración, versiones, revisiones estáticas, calidad no funcional y cierre formal.

**Siguiente mejora recomendada:** implementar primero **campañas de ejecución + CI reproducible + flujo formal de defectos**. Estas tres capacidades aumentarían de forma inmediata la confiabilidad, la trazabilidad histórica y el valor demostrable del sistema.

## Referencias

[1]: https://github.com/JavierIsma05/istqb-testing-platform "Repositorio istqb-testing-platform"

[2]: https://istqb.org/certifications/certified-tester-foundation-level-ctfl-v4-0/ "Certified Tester Foundation Level (CTFL) v4.0 Overview"

[3]: https://astqb.org/5-5-defect-management/ "ISTQB Foundation Level Syllabus — Defect Management"

[4]: https://glossary.istqb.org/en_US/term/risk-based-testing "ISTQB Glossary — Risk-based testing"
