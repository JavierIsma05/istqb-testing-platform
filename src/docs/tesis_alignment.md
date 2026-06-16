# Alineacion de la plataforma con ISTQB y el STLC

## Proposito

La plataforma gestiona y evidencia el ciclo de vida de pruebas de proyectos de titulacion. Su valor academico no esta en almacenar formularios o capturas, sino en aplicar reglas de trazabilidad, ejecucion, seguimiento de defectos y medicion automatica.

## Orden funcional de la plataforma

1. **Dashboard**: resume calidad, avance y alertas.
2. **Proyectos**: define el contexto, estudiante responsable y tutor.
3. **Requisitos**: registra la base verificable del producto.
4. **Plan de Pruebas**: define alcance, estrategia, tipos de prueba, ambiente, recursos y criterios cuantitativos de salida.
5. **Riesgos del Plan**: identifica amenazas futuras y su mitigacion dentro de un plan.
6. **Casos de Prueba**: disena pruebas trazables con tecnica ISTQB, datos y pasos estructurados.
7. **Ejecucion**: compara por paso el resultado esperado con el obtenido.
8. **Defectos**: registra fallos reales originados por ejecuciones fallidas.
9. **Trazabilidad**: presenta la cadena requisito, caso, ejecucion y defecto.
10. **Informes**: genera metricas y evidencia academica del proceso.

## Fases del ciclo

1. Analisis de requisitos.
2. Planificacion y analisis de riesgos.
3. Diseno de pruebas.
4. Implementacion y preparacion del ambiente.
5. Ejecucion y gestion de defectos.
6. Cierre e informes.

Las fases avanzan en orden y sus criterios se calculan con datos reales de la plataforma.

## Reglas de negocio centrales

- Un caso de prueba debe estar asociado a un requisito del mismo proyecto.
- Un riesgo debe pertenecer a un plan de pruebas.
- Cada paso ejecutado registra accion, resultado esperado, resultado obtenido, estado y comentario.
- El resultado del caso se calcula automaticamente: `FAIL` prevalece sobre `BLOCKED`, y `PASS` requiere que todos los pasos aprueben.
- La evidencia grafica es opcional y no reemplaza el resultado obtenido.
- Un defecto manual debe originarse en una ejecucion fallida del mismo proyecto.
- La cobertura es `(requisitos cubiertos / requisitos totales) * 100` y no disminuye por defectos o revisiones pendientes.
- La tasa de exito es `(ejecuciones PASS / ejecuciones realizadas) * 100`.
- La densidad es `defectos / casos ejecutados`.

## Estado implementado

- Roles Estudiante y Docente/Tutor con permisos diferenciados.
- Proyectos, requisitos y planes con historial y versionado basico.
- Riesgos diferenciados de defectos y asociados al plan.
- Casos con tecnicas ISTQB, version, datos de prueba y pasos estructurados.
- Ejecucion paso a paso con resultado automatico y evidencia opcional.
- Creacion automatica de defecto desde una ejecucion fallida.
- Confirmacion de correcciones y regresion.
- Matriz de trazabilidad y metricas automaticas.
- Informes PDF con cobertura, ejecucion, defectos y riesgos.
- Flujo de fases con criterios de entrada y salida verificables.

## Trabajo pendiente para cierre de tesis

- Asociacion directa de requisitos al plan, adicional a la relacion mediante casos.
- Version actual explicita del proyecto y compatibilidad de versiones entre plan, caso y ejecucion.
- Evidencia opcional por paso, no solo por ejecucion.
- Aprobacion o rechazo formal de requisitos, planes y casos por parte del tutor.
- Evaluacion automatica de todos los criterios cuantitativos para cerrar cada plan.
- Pruebas Selenium estables en integracion continua y matriz de navegadores.
- Capitulo de validacion con casos de estudio, resultados, limitaciones y amenazas a la validez.

## Evidencias sugeridas para el documento

- Matriz de trazabilidad completa de un proyecto piloto.
- Caso de prueba con tecnica ISTQB y pasos estructurados.
- Ejecucion fallida con comparacion esperado/obtenido y defecto generado.
- Ejecucion de confirmacion que cierre el defecto.
- Informe de cobertura, tasa de exito y densidad de defectos.
- Registro de revision del tutor y bitacora de auditoria.
