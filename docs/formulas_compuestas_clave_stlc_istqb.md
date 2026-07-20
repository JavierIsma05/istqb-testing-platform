# Formulas compuestas clave STLC/ISTQB

Este documento separa las formulas principales del proyecto y las expresa con nombres en espanol, sin usar variables internas del codigo.

## Formulas principales

| Formula | Calculo |
|---|---|
| Cobertura de requisitos | `(Requisitos con al menos un caso de prueba / Total de requisitos) x 100` |
| Avance de ejecucion | `(Casos de prueba ejecutados / Total de casos de prueba) x 100` |
| Tasa de aprobacion | `(Ejecuciones aprobadas / Ejecuciones realizadas) x 100` |
| Densidad de defectos | `Total de defectos / Casos de prueba ejecutados` |
| Tasa de evidencia | `(Ejecuciones con evidencia / Total de ejecuciones) x 100` |
| Tasa de revision docente | `(Ejecuciones revisadas / Total de ejecuciones) x 100` |
| Tasa de ejecucion de requisitos | `(Requisitos con ejecucion en sus casos / Total de requisitos) x 100` |
| Tasa de trazabilidad de defectos | `(Defectos asociados a una ejecucion / Total de defectos) x 100` |
| Tasa de deteccion de defectos | `(Total de defectos / Total de ejecuciones) x 100` |
| Tasa de correccion de defectos | `(Defectos cerrados / Total de defectos) x 100` |
| Indice global de trazabilidad | `(Cobertura de requisitos + Tasa de ejecucion de requisitos + Tasa de evidencia + Tasa de revision docente + Tasa de trazabilidad de defectos) / 5` |
| Progreso de fase STLC | `(Criterios completados de la fase / Total de criterios de la fase) x 100` |
| Progreso general de fases | `Suma del progreso de todas las fases / Total de fases` |
| Criterios de salida aprobados | `Cobertura minima cumplida AND Aprobacion minima cumplida AND Defectos criticos dentro del limite` |

## Lectura rapida

| Formula | Para que sirve |
|---|---|
| Cobertura de requisitos | Mide si los requisitos tienen casos de prueba relacionados. |
| Avance de ejecucion | Mide cuanto del conjunto de pruebas ya fue ejecutado. |
| Tasa de aprobacion | Mide cuantas ejecuciones reales terminaron aprobadas. |
| Densidad de defectos | Mide cuantos defectos aparecen por caso ejecutado. |
| Tasa de evidencia | Mide si las ejecuciones tienen soporte documental o captura. |
| Tasa de revision docente | Mide si las ejecuciones fueron revisadas formalmente. |
| Tasa de ejecucion de requisitos | Mide si los requisitos ya tienen resultados de prueba. |
| Tasa de trazabilidad de defectos | Mide si los defectos pueden rastrearse hasta una ejecucion. |
| Tasa de deteccion de defectos | Mide la frecuencia de defectos frente a las ejecuciones. |
| Tasa de correccion de defectos | Mide cuantos defectos ya fueron cerrados. |
| Indice global de trazabilidad | Resume cobertura, ejecucion, evidencia, revision y defectos trazados. |
| Progreso de fase STLC | Mide el avance de cada fase segun sus criterios cumplidos. |
| Progreso general de fases | Resume el avance total del ciclo STLC. |
| Criterios de salida aprobados | Decide si el ciclo de pruebas puede cerrarse segun el plan. |

## De donde salen estas formulas

Estas formulas no fueron copiadas literalmente de ISTQB como ecuaciones obligatorias. Salen de dos fuentes:

1. Del codigo del sistema, porque la plataforma necesita convertir datos registrados en porcentajes, tasas, conteos y decisiones de cierre.
2. De conceptos ISTQB, porque ISTQB si recomienda medir cobertura, progreso de pruebas, defectos, riesgos, criterios de salida, reportes de progreso y trazabilidad.

Por eso, la idea de medir esas areas esta alineada con ISTQB. La forma exacta de calcularlas, por ejemplo el indice global de trazabilidad, fue una decision de implementacion del proyecto.

## Relacion con ISTQB

| Formula del sistema | Relacion con ISTQB |
|---|---|
| Cobertura de requisitos | ISTQB trata la cobertura como un criterio medible y menciona cobertura de requisitos. |
| Avance de ejecucion | ISTQB menciona metricas de progreso, casos ejecutados, no ejecutados, aprobados y fallidos. |
| Tasa de aprobacion | Se deriva de las metricas de ejecucion aprobada/fallida usadas para monitorear el estado de pruebas. |
| Densidad de defectos | ISTQB menciona defect density como metrica de defectos. |
| Tasa de evidencia | Es una decision del proyecto para soportar auditoria y reporte; se relaciona con testware, resultados y reportes. |
| Tasa de revision docente | Es propia del contexto academico del sistema; no es una formula ISTQB estandar. |
| Tasa de ejecucion de requisitos | Se deriva de trazabilidad entre requisitos, casos y resultados. |
| Tasa de trazabilidad de defectos | Se deriva de la trazabilidad entre resultados, defectos y elementos de prueba. |
| Tasa de deteccion de defectos | Se relaciona con metricas de defectos y defect detection percentage. |
| Tasa de correccion de defectos | Se relaciona con defectos encontrados y corregidos. |
| Indice global de trazabilidad | Es una formula propia del proyecto para resumir varias metricas. |
| Progreso de fase STLC | Es una decision de implementacion para representar avance por fases del ciclo de pruebas. |
| Criterios de salida aprobados | ISTQB define criterios de salida como condiciones para declarar completada una actividad. |

Fuentes base consultadas:

- ISTQB CTFL Syllabus v4.0.1, secciones 1.4.4, 5.1.3, 5.2.3 y 5.3.1.
- Codigo del proyecto: `src/apps/reports/views.py`, `src/apps/phases/views.py`, `src/apps/executions/views.py`, `src/apps/incidents/models.py`.
