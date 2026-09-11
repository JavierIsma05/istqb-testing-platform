# Auditoría de controles y trazabilidad

**Repositorio:** `JavierIsma05/istqb-testing-platform`  
**Rama evaluada:** `main`  
**Fecha:** 11 de septiembre de 2026

## Conclusión

La plataforma ya tiene varias reglas de negocio reales. No es correcto decir que todo se limita a llenar formularios. Por ejemplo, la ejecución exige evidencia, valida el archivo, deriva el resultado a partir de lo obtenido, puede crear un defecto desde una ejecución fallida, vincula las confirmaciones con defectos y recalcula el estado del caso después de revisar los pasos.

Sin embargo, el control todavía es **desigual**. La ejecución tiene reglas relativamente fuertes; el plan de pruebas tiene métricas y criterios de salida; pero la mayoría de los estados de requisitos, planes, casos y defectos no están modelados todavía como máquinas de estados estrictas. En varios lugares el usuario puede seleccionar o modificar un estado sin que el sistema exija las condiciones que justifican esa transición.

Para lograr una trazabilidad sólida, cada artefacto debe responder cinco preguntas: **qué se creó, quién lo creó, contra qué requisito o riesgo se relaciona, en qué versión y ambiente se validó, y qué evidencia permite aceptar o rechazar la conclusión**.

## 1. Qué controles ya existen

| Aspecto | Estado actual verificado | Evaluación |
|---|---|---|
| Evidencia de ejecución | La ejecución exige un archivo y acepta PNG, JPG, GIF, WEBP, PDF, TXT, LOG y CSV, con límite de 10 MB | Bueno, pero la validación depende principalmente de extensión y tamaño |
| Evidencia por paso | Cada paso puede tener archivo o captura; se exige al menos uno | Bueno |
| Evidencia automatizada | Hay capturas, logs y resultados de reglas automatizadas | Bueno para el alcance actual |
| Resultado de ejecución | Se deriva de `actual_result`: “Cumple” produce aprobado y “No cumple” produce fallido | Bueno, pero debe impedir inconsistencias entre resultado global y pasos |
| Pasos ejecutados | Cada paso exige resultado obtenido y estado válido; fallos y bloqueos requieren comentario | Bueno |
| Revisión docente | Existe revisión de ejecución y revisión de pasos; se guarda revisor, fecha y comentario | Bueno |
| Recalculo | La revisión recalcula el resultado agregado y el estado del caso | Bueno |
| Defecto desde fallo | Una ejecución fallida puede generar un defecto vinculado al caso y a la ejecución | Bueno |
| Confirmación de defecto | Una ejecución de confirmación debe seleccionar un defecto; si pasa cierra el defecto y si falla lo devuelve a progreso | Bueno, requiere restricciones adicionales |
| Versionado | Requisitos, planes y casos tienen modelos de versión e historial | Bueno, pero falta convertirlos en baselines inmutables |
| Riesgos | El plan permite registrar riesgos y producir matriz y métricas | Parcial; el uso del riesgo para priorizar casos no es obligatorio |
| Plan de pruebas | Se calcula cobertura, tasa de éxito, defectos, riesgos, revisiones y criterios de salida | Bueno como medición posterior |
| Auditoría | Se registran acciones de creación, actualización y eliminación en varios flujos | Bueno, pero debe cubrir todas las transiciones y cambios críticos |

## 2. Problemas de lógica por artefacto

### 2.1 Requisitos

Los requisitos tienen estados `Pendiente`, `En revisión` y `Aprobado`. La plataforma utiliza el requisito aprobado como condición para permitir la ejecución de un caso, lo cual es una regla correcta.

La brecha es que debe controlarse también cómo se llega a cada estado. Un requisito no debería pasar a aprobado si está vacío, no tiene aceptación definida, no tiene prioridad o no fue revisado por un responsable. Tampoco debería poder editarse libremente después de ser aprobado sin crear una nueva versión o devolverlo a revisión.

**Reglas recomendadas:**

- Un requisito aprobado debe ser inmutable en sus campos sustantivos.
- Cualquier cambio después de la aprobación debe crear una nueva versión en estado pendiente o revisión.
- La aprobación debe guardar usuario, fecha, comentario y evidencia.
- Un requisito aprobado debe tener criterios de aceptación verificables.
- Debe existir una validación de calidad mínima: descripción, tipo, prioridad, origen, responsable y criterio de aceptación.
- Si un requisito cambia, los casos relacionados deben marcarse como “requieren revisión”.
- Un requisito rechazado o modificado debe generar una alerta de impacto sobre casos, ejecuciones y defectos vinculados.

### 2.2 Plan de pruebas

El plan no es solo un formulario. Actualmente alimenta riesgos, versiones, reportes, métricas, criterios de salida y el bloqueo de ejecución por requisitos no aprobados. Eso es positivo.

No obstante, el plan aún funciona más como un **contenedor de configuración** que como un controlador completo del proceso. Sus campos de objetivo, estrategia, alcance, recursos, ambiente y responsabilidades se almacenan, pero no todos se contrastan automáticamente con la ejecución.

**Validaciones que faltan o conviene reforzar:**

- No permitir aprobar un plan sin objetivo, alcance, estrategia, criterios de entrada y salida.
- Exigir al menos un requisito aprobado antes de pasar el plan a aprobado.
- Exigir que cada requisito dentro del alcance tenga una decisión: cubierto, excluido con justificación o pendiente.
- Exigir que cada caso tenga una técnica, prioridad, nivel, requisito y criterio esperado.
- Comparar el ambiente declarado en el plan con el ambiente registrado en la ejecución.
- Comparar la fecha planificada con la fecha real y marcar desviaciones.
- Comparar responsabilidades declaradas con el ejecutor y el revisor real.
- Bloquear el cierre si existen casos no ejecutados, ejecuciones pendientes de revisión, defectos críticos abiertos o riesgos altos sin tratamiento.
- Al aprobar el plan, crear una versión aprobada inmutable.
- Si cambian el alcance, estrategia, criterios o umbrales, crear nueva versión y solicitar nueva aprobación.

El plan debe dejar de ser solo una ficha descriptiva y convertirse en la **fuente de reglas de aceptación del ciclo**.

### 2.3 Casos de prueba

Los casos tienen una estructura adecuada: requisito, técnica, nivel, prioridad, precondiciones, datos, pasos, resultado esperado, versión y tipo de ejecución. También se impide ejecutar un caso que no tenga requisito aprobado.

La principal debilidad es la falta de control de madurez del caso. Un caso puede tener un estado, pero debe haber reglas para que `Listo para ejecutar` signifique realmente que está completo y revisado.

**Reglas recomendadas:**

- `En redacción`: puede editarse, pero no ejecutarse.
- `En revisión`: no debe editarse por el autor mientras está siendo revisado.
- `Listo para ejecutar`: debe tener requisito aprobado, pasos, precondiciones, datos, resultado esperado, técnica y prioridad.
- `Ejecutando`: solo debe asignarse mientras existe una ejecución activa.
- `Completado`: debe provenir de una ejecución aprobada y revisada.
- `Fallido`: debe tener evidencia y defecto asociado, salvo que el fallo sea un bloqueo técnico documentado.
- `Bloqueado`: debe exigir motivo, dependencia o incidente relacionado.
- Una modificación a un caso listo, ejecutando o completado debe crear una nueva versión y reiniciar la revisión.
- El sistema debe mostrar qué versión del caso fue ejecutada.
- Debe impedirse que una ejecución antigua se interprete como válida para una versión nueva del caso.

### 2.4 Ejecuciones

Las ejecuciones son el módulo con mejor lógica actual. Se exige resultado obtenido, evidencia y resultados por paso. La ejecución puede ser manual, automatizada, de confirmación o de regresión. Además, los estados se agregan desde los pasos.

La pregunta “si ya ejecuté algo, ¿solo se puede volver a ejecutar si se abre el caso?” requiere una decisión de negocio. La recomendación ISTQB no debería ser bloquear toda repetición. Debe distinguirse entre:

- **Repetición accidental:** evitar crear una ejecución duplicada idéntica sin justificación.
- **Reejecución legítima:** permitirla cuando sea regresión, confirmación de defecto, nueva versión del producto, nuevo ambiente o corrección de datos.

**Reglas recomendadas:**

- No permitir una segunda ejecución normal abierta para el mismo caso y la misma versión, campaña y ambiente.
- Permitir reejecución si se selecciona `Confirmación` o `Regresión`, o si cambió la versión del software, el ambiente o los datos.
- Exigir un motivo de reejecución y vincular la ejecución anterior.
- Crear una entidad `TestRun` o `ExecutionCycle` para agrupar las ejecuciones de una campaña.
- Guardar versión del producto, commit/build, navegador, sistema operativo, ambiente, datos y plan usado.
- No permitir editar una ejecución cerrada; cualquier corrección debe quedar como revisión o nueva ejecución.
- Una ejecución fallida debe exigir defecto o justificación de que no corresponde registrar defecto.
- Una ejecución bloqueada debe exigir incidente o bloqueo documentado.
- Una ejecución de confirmación debe estar vinculada a un defecto resuelto y no a cualquier defecto abierto.
- Una ejecución aprobada debe conservar exactamente el caso, plan y datos utilizados, aunque luego cambien.

### 2.5 Defectos

El defecto tiene código, título, descripción, pasos para reproducir, severidad, prioridad, estado, responsable, ejecución y reportante. La confirmación puede cerrar o reabrir el defecto. La base es correcta.

La lógica debe ser más estricta en las transiciones. El campo estado no debe ser solo una selección libre.

**Flujo recomendado:**

`Reportado → En análisis → Confirmado → En corrección → Resuelto → Pendiente de confirmación → Cerrado`

También deben existir salidas controladas para `Duplicado`, `No reproducible`, `Falso positivo`, `Rechazado` y `No se corregirá`.

**Reglas recomendadas:**

- Para pasar de reportado a confirmado, exigir análisis y clasificación.
- Para pasar a en corrección, exigir responsable y prioridad.
- Para pasar a resuelto, exigir resolución, versión corregida y comentario.
- Para pasar a pendiente de confirmación, exigir evidencia del cambio.
- Para cerrar, exigir una ejecución de confirmación aprobada y un verificador.
- Para reabrir, exigir nueva evidencia y motivo.
- Registrar versión encontrada, versión corregida, componente, ambiente, causa raíz e impacto.
- Evitar que el reportante y el verificador sean la misma persona cuando el contexto académico requiera independencia.
- Calcular tiempo de detección, tiempo de resolución, tiempo de confirmación y tasa de reapertura.

### 2.6 Reportes y criterios de salida

Los reportes sí utilizan datos operativos: cobertura, ejecución, tasa de aprobación, defectos, riesgos, evidencia, revisiones y criterios de salida. Esto significa que el plan no queda completamente aislado.

La mejora necesaria es hacer visible el razonamiento. El reporte debe indicar no solo “aprobado” o “no aprobado”, sino qué artefactos sustentan cada criterio.

Por cada criterio de salida debería verse:

- Fórmula aplicada.
- Valor actual.
- Umbral definido en el plan.
- Fuente de datos.
- Elementos que incumplen.
- Evidencia vinculada.
- Responsable de aceptar el riesgo.
- Fecha de la decisión.

La plataforma también debe evitar que un porcentaje global oculte problemas. Por ejemplo, una cobertura del 90 % no debería ser suficiente si el 10 % pendiente contiene requisitos críticos.

## 3. Archivos y evidencias: qué mejorar

La validación actual controla extensión y tamaño. Eso es útil, pero no demuestra que el contenido sea realmente seguro o válido.

**Mejoras técnicas y funcionales:**

- Validar MIME real y firma del archivo, no solo el nombre.
- Comprobar que las imágenes se puedan abrir y no estén corruptas.
- Usar antivirus o análisis de malware en un entorno real.
- Generar nombre interno único y no confiar en el nombre original.
- Evitar servir archivos privados directamente sin autorización.
- Verificar que el usuario pueda descargar solo evidencias de proyectos visibles.
- Mostrar tamaño, tipo, fecha, autor y hash del archivo.
- Registrar quién cargó, reemplazó o eliminó la evidencia.
- No permitir reemplazar una evidencia de una ejecución cerrada; crear una nueva versión.
- Generar miniaturas y vista previa para imágenes y PDF.
- Mostrar una lista ordenada de evidencias por ejecución y paso.
- Asociar cada evidencia a una versión de caso, ejecución, ambiente y resultado.
- Añadir checksum para demostrar que la evidencia no cambió después de la revisión.

## 4. Trazabilidad objetivo

La trazabilidad no debe ser únicamente una matriz visual. Debe ser una red de relaciones validada por reglas.

La cadena mínima recomendada es:

`Requisito → Riesgo → Condición de prueba → Caso de prueba → Versión del caso → Ejecución → Evidencia → Defecto o confirmación → Reporte → Decisión de salida`

Actualmente la plataforma cubre buena parte de la cadena, pero conviene añadir explícitamente:

- Riesgo y condición de prueba.
- Versión exacta de cada artefacto.
- Campaña o ciclo de ejecución.
- Versión/build del producto probado.
- Ambiente reproducible.
- Evidencia concreta por paso.
- Relación entre defecto resuelto y prueba de confirmación.
- Relación entre defecto reabierto y nueva ejecución.
- Impacto de cambios de requisito sobre casos y ejecuciones históricas.

La matriz debería mostrar al menos estos estados:

| Relación | Estados útiles |
|---|---|
| Requisito-caso | Cubierto, cubierto parcialmente, no cubierto, obsoleto |
| Caso-ejecución | No ejecutado, aprobado, fallido, bloqueado, pendiente de revisión |
| Ejecución-evidencia | Completa, incompleta, inválida, no requerida con justificación |
| Ejecución-defecto | Sin defecto, defecto abierto, resuelto, confirmado, reabierto |
| Riesgo-caso | Cubierto, cubierto parcialmente, sin cobertura |
| Plan-criterio de salida | Cumple, no cumple, pendiente, aceptado con riesgo |

## 5. Mejoras de diseño y experiencia de usuario

La interfaz debe ayudar a entender la trazabilidad, no solo mostrar formularios y tablas.

### En formularios

- Mostrar una barra de progreso del flujo: requisito, plan, caso, ejecución, defecto y cierre.
- Mostrar un panel lateral con relaciones existentes mientras se edita un artefacto.
- Deshabilitar campos que no pueden modificarse por estado y explicar el motivo.
- Mostrar validaciones antes de guardar, no solo después del envío.
- Mostrar campos obligatorios según el estado elegido.
- Mostrar un resumen de impacto antes de aprobar o cambiar un artefacto.

### En listados

- Usar filtros combinados por estado, prioridad, responsable, riesgo, versión y cobertura.
- Diferenciar visualmente estados “pendiente”, “en revisión”, “aprobado”, “fallido” y “bloqueado”.
- Mostrar alertas de trazabilidad rota.
- Mostrar indicadores de evidencia faltante.
- Mostrar la versión ejecutada junto al caso.
- Añadir acciones contextuales: revisar, aprobar, reabrir, crear ejecución de confirmación o abrir defecto.

### En el detalle

- Mostrar una línea de tiempo de cambios y revisiones.
- Mostrar las relaciones aguas arriba y aguas abajo.
- Mostrar qué reportes y criterios de salida se ven afectados.
- Mostrar la diferencia entre versiones.
- Mostrar un indicador de integridad del artefacto.

### En reportes

- Incorporar una sección “Por qué este resultado”.
- Mostrar excepciones críticas antes de los porcentajes agregados.
- Permitir navegar desde una métrica hasta los registros que la componen.
- Mostrar tendencia histórica por ciclo, no solo una fotografía.
- Utilizar colores accesibles y no depender exclusivamente del color para comunicar estados.

## 6. Prioridad de implementación

| Prioridad | Funcionalidad | Resultado esperado |
|---|---|---|
| P0 | Máquina de estados para requisitos, casos, ejecuciones y defectos | Los estados dejan de ser selecciones libres |
| P0 | Campaña de ejecución con versión, ambiente y build | Se distingue cada ciclo y se habilita la regresión |
| P0 | Bloqueo de edición de artefactos aprobados o cerrados | Se conserva la integridad histórica |
| P0 | Reejecución controlada con motivo y relación anterior | Se evita duplicidad sin impedir confirmación o regresión |
| P0 | Defecto obligatorio o justificación para una ejecución fallida | Se cierra la trazabilidad del fallo |
| P1 | Validación de aprobación del plan contra requisitos, casos y riesgos | El plan gobierna realmente el ciclo |
| P1 | Evidencia con MIME, hash, permisos y metadatos | La evidencia es más confiable y auditable |
| P1 | Alertas de impacto por cambio de requisito | Se detecta trazabilidad obsoleta |
| P1 | Ejecuciones de confirmación y cierre de defecto con verificador | Se demuestra la corrección del defecto |
| P1 | Condiciones de prueba y justificación de técnicas | Se demuestra el diseño ISTQB |
| P2 | Revisiones estáticas | Se cubre una actividad faltante del proceso |
| P2 | Pruebas no funcionales | Se amplía la cobertura de calidad |
| P2 | Tendencias, baselines y comparaciones históricas | Se mejora la toma de decisiones |
| P2 | Integración CI/CD y resultados externos | Se reduce trabajo manual y se aumenta reproducibilidad |

## 7. Veredicto

La plataforma ya tiene una base funcional buena y posee reglas reales de ejecución, revisión y evidencia. El mayor déficit no es la cantidad de pantallas, sino la **fuerza de las relaciones y transiciones**.

La mejora más importante sería pasar de un modelo donde los artefactos se registran y se reportan a un modelo donde el sistema **impide inconsistencias**. Por ejemplo, no debería ser posible aprobar un plan sin requisitos aprobados, ejecutar un caso cuya versión cambió sin revisión, cerrar un defecto sin confirmación o presentar una métrica sin poder navegar hasta sus evidencias.

El objetivo de trazabilidad debería ser que, al abrir cualquier resultado final, el docente o auditor pueda recorrer la cadena completa y comprobarla sin depender de explicaciones externas.
