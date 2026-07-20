# Metricas implementadas STLC/ISTQB

Este documento muestra solo las formulas que se ejecutan en el codigo de la plataforma.

Regla comun usada en reportes:

| Funcion | Archivo | Formula |
|---|---|---|
| `_percentage(part, total)` | `src/apps/reports/views.py` | `si total > 0: round((part / total) * 100); si no: 0` |
| `_ratio(part, total)` | `src/apps/reports/views.py` | `si total > 0: round(part / total, 2); si no: 0` |

## Tabla de formulas

| # | Metrica | Formula ejecutada | Archivo / funcion |
|---|---|---|---|
| 1 | Cobertura de requisitos | `coverage = round((covered_requirements / total_requirements) * 100)` | `src/apps/reports/views.py` -> `_build_coverage_content`; `src/apps/traceability/views.py` -> `traceability_matrix_view`; `src/apps/requirements/views.py` -> `requirement_list_view` |
| 2 | Requisito cubierto | `coverage = 100 si linked_cases > 0; si no coverage = 0` | `src/apps/requirements/views.py` -> `requirement_list_view`; `src/apps/traceability/views.py` -> `traceability_matrix_view` |
| 3 | Casos vinculados a un requisito | `linked_cases = max(direct_cases, traced_cases)` | `src/apps/requirements/views.py` -> `requirement_list_view` |
| 4 | Requisitos sin cobertura | `uncovered_requirements = total_requirements - covered_requirements` | `src/apps/reports/views.py` -> `_build_coverage_content` |
| 5 | Casos de prueba vinculados | `linked_test_cases = count(TC donde TC.requirement != null OR TC.traceability_links != null)` | `src/apps/reports/views.py` -> `_build_coverage_content` |
| 6 | Requisitos automatizados | `automated_requirements = count(requisitos con casos que tienen automated_rules.is_active = True)` | `src/apps/reports/views.py` -> `_build_coverage_content` |
| 7 | Requisitos solo manuales | `manual_only_requirements = max(covered_requirements - automated_requirements, 0)` | `src/apps/reports/views.py` -> `_build_coverage_content` |
| 8 | Avance de ejecucion | `execution_progress = round((executed_cases / total_test_cases) * 100)` | `src/apps/reports/views.py` -> `_build_execution_content`; `src/apps/reports/views.py` -> `_build_summary_content` |
| 9 | Casos ejecutados | `executed_cases = count(distinct test_case donde execution.result != NOT_RUN)` | `src/apps/reports/views.py` -> `_build_execution_content`, `_build_summary_content`, `_build_defects_content`, `_build_final_content` |
| 10 | Progreso del proyecto | `progress = round((passed_cases / total_cases) * 100)` | `src/apps/dashboard/views/dashboard_views.py` -> `get_project_progress`; `src/apps/projects/views.py` -> `build_project_card`, `project_detail_view` |
| 11 | Ejecuciones aprobadas | `passed = count(executions donde result = PASSED)` | `src/apps/reports/views.py` -> `_build_execution_content` |
| 12 | Ejecuciones fallidas | `failed = count(executions donde result = FAILED)` | `src/apps/reports/views.py` -> `_build_execution_content` |
| 13 | Ejecuciones bloqueadas | `blocked = count(executions donde result = BLOCKED)` | `src/apps/reports/views.py` -> `_build_execution_content` |
| 14 | Ejecuciones con error | `errors = count(executions donde result = ERROR)` | `src/apps/reports/views.py` -> `_build_execution_content` |
| 15 | Ejecuciones no realizadas | `not_run = count(executions donde result = NOT_RUN)` | `src/apps/reports/views.py` -> `_build_execution_content` |
| 16 | Porcentaje por estado de ejecucion | `percent_status = round((count_status / total_executions) * 100)` | `src/apps/reports/views.py` -> `_execution_status_distribution` |
| 17 | Tasa de aprobacion | `success_rate = round((passed / (total_executions - not_run)) * 100)` | `src/apps/reports/views.py` -> `_build_execution_content` |
| 18 | Exito historico de un caso | `success_percent = round((passed_count / execution_total) * 100)` | `src/apps/executions/views.py` -> `execution_workspace_view`, `execution_history_view` |
| 19 | Resultado manual por pasos | `si algun paso = FAILED -> FAILED; si no, si algun paso = BLOCKED -> BLOCKED; si no -> PASSED` | `src/apps/executions/views.py` -> `aggregate_step_result` |
| 20 | Resultado semi-automatizado | `FAILED > ERROR > BLOCKED > PASSED; si no hay reglas validas -> BLOCKED` | `src/apps/executions/services/automated_runner.py` -> `aggregate_automated_status` |
| 21 | Duracion semi-automatizada | `duration_seconds = Decimal((finished_at - started_at) / 1 segundo).quantize(0.001)` | `src/apps/executions/services/automated_runner.py` -> `run_automated_execution` |
| 22 | Ejecuciones con evidencia | `executions_with_evidence = count(distinct execution donde evidence != "" OR automated_results.screenshot != "")` | `src/apps/reports/views.py` -> `_build_execution_content` |
| 23 | Tasa de evidencia | `evidence_rate = round((executions_with_evidence / total_executions) * 100)` | `src/apps/reports/views.py` -> `_build_final_content` |
| 24 | Revision docente | `reviewed_executions = validated + rejected + needs_fix` | `src/apps/reports/views.py` -> `_build_final_content` |
| 25 | Tasa de revision docente | `review_rate = round((reviewed_executions / total_executions) * 100)` | `src/apps/reports/views.py` -> `_build_final_content` |
| 26 | Requisitos ejecutados | `executed_requirements = count(requisito donde existe latest_execution en sus casos)` | `src/apps/reports/views.py` -> `_requirement_execution_metrics` |
| 27 | Requisito fallido | `failed_requirement = existe latest_result = FAILED` | `src/apps/reports/views.py` -> `_requirement_execution_metrics` |
| 28 | Requisito bloqueado | `blocked_requirement = existe latest_result en {BLOCKED, ERROR}` | `src/apps/reports/views.py` -> `_requirement_execution_metrics` |
| 29 | Requisito aprobado | `passed_requirement = todos los latest_result = PASSED` | `src/apps/reports/views.py` -> `_requirement_execution_metrics` |
| 30 | Tasa de ejecucion de requisitos | `requirement_execution_rate = round((executed_requirements / total_requirements) * 100)` | `src/apps/reports/views.py` -> `_build_final_content` |
| 31 | Defectos totales | `defects = count(defects)` | `src/apps/reports/views.py` -> `_build_defects_content` |
| 32 | Defectos abiertos | `open_defects = count(defects donde status = OPEN)` | `src/apps/reports/views.py` -> `_build_defects_content` |
| 33 | Defectos en progreso | `in_progress_defects = count(defects donde status = IN_PROGRESS)` | `src/apps/reports/views.py` -> `_build_defects_content` |
| 34 | Defectos en analisis | `analysis_defects = count(defects donde status = ANALYSIS)` | `src/apps/reports/views.py` -> `_build_defects_content` |
| 35 | Defectos pendientes de confirmacion | `pending_confirmation_defects = count(defects donde status = PENDING_CONFIRMATION)` | `src/apps/reports/views.py` -> `_build_defects_content` |
| 36 | Defectos cerrados | `closed_defects = count(defects donde status = CLOSED)` | `src/apps/reports/views.py` -> `_build_defects_content` |
| 37 | Defectos por severidad | `defects_severity = count(defects donde severity = CRITICAL/HIGH/MEDIUM/LOW)` | `src/apps/reports/views.py` -> `_build_defects_content`, `_defect_severity_rows` |
| 38 | Defectos por estado | `defects_status = count(defects donde status = estado)` | `src/apps/reports/views.py` -> `_defect_status_rows` |
| 39 | Densidad de defectos | `defect_density = round(total_defects / executed_cases, 2)` | `src/apps/reports/views.py` -> `_build_defects_content`, `_build_execution_content`, `_build_summary_content` |
| 40 | Defectos trazados a ejecucion | `defects_with_execution = count(defects donde execution != null)` | `src/apps/reports/views.py` -> `_build_defects_content`, `_build_final_content` |
| 41 | Tasa de trazabilidad de defectos | `si total_defects > 0: round((defects_with_execution / total_defects) * 100); si no: 100` | `src/apps/reports/views.py` -> `_build_final_content` |
| 42 | Tasa de deteccion de defectos | `detection_rate = round((total_defects / total_executions) * 100)` | `src/apps/reports/views.py` -> `_build_final_content` |
| 43 | Tasa de correccion de defectos | `correction_rate = round((closed_defects / total_defects) * 100)` | `src/apps/reports/views.py` -> `_build_final_content` |
| 44 | Riesgos altos | `high_risks = count(risk donde risk.risk_level = "Alto")` | `src/apps/reports/views.py` -> `_high_risk_count`; `src/apps/traceability/views.py` -> `traceability_matrix_view` |
| 45 | Nivel de riesgo alto | `Alto = (probability = HIGH AND impact in {MEDIUM, HIGH}) OR (impact = HIGH AND probability in {MEDIUM, HIGH})` | `src/apps/incidents/models.py` -> `risk_level` |
| 46 | Nivel de riesgo bajo | `Bajo = (probability = LOW AND impact in {LOW, MEDIUM}) OR (probability = MEDIUM AND impact = LOW)` | `src/apps/incidents/models.py` -> `risk_level` |
| 47 | Nivel de riesgo medio | `Medio = cualquier combinacion que no sea Alto ni Bajo` | `src/apps/incidents/models.py` -> `risk_level` |
| 48 | Matriz de riesgos | `risk_cell = count(risks donde probability = p AND impact = i)` | `src/apps/reports/views.py` -> `_risk_matrix_rows` |
| 49 | Indice global de trazabilidad | `traceability_index = round((coverage + requirement_execution_rate + evidence_rate + review_rate + defect_traceability_rate) / 5)` | `src/apps/reports/views.py` -> `_build_final_content` |
| 50 | Progreso de fase | `phase_progress = round((completed_checks / total_checks) * 100)` | `src/apps/phases/views.py` -> `phase_criteria_status` |
| 51 | Tareas pendientes de fase | `pending_tasks = total_checks - completed_checks` | `src/apps/phases/views.py` -> `phase_criteria_status` |
| 52 | Progreso general de fases | `general_progress = round(sum(phase.progress) / phase_count)` | `src/apps/phases/views.py` -> `phase_list_view` |
| 53 | Fase completable | `can_complete = total_checks > 0 AND pending_tasks = 0` | `src/apps/phases/views.py` -> `phase_criteria_status` |
| 54 | Criterio de cobertura minima | `coverage >= plan.minimum_coverage_percentage` | `src/apps/reports/views.py` -> `_exit_criteria` |
| 55 | Criterio de aprobacion minima | `success_rate >= plan.minimum_pass_percentage` | `src/apps/reports/views.py` -> `_exit_criteria` |
| 56 | Criterio de defectos criticos | `critical_defects <= plan.maximum_critical_defects` | `src/apps/reports/views.py` -> `_exit_criteria` |
| 57 | Criterios de salida aprobados | `exit_passed = criterio_coverage AND criterio_success AND criterio_critical_defects` | `src/apps/reports/views.py` -> `_exit_criteria` |
| 58 | Veredicto aprobado | `APROBADO = exit_passed AND critical_defects = 0 AND open_defects = 0 AND high_risks = 0 AND pending_review_executions = 0` | `src/apps/reports/views.py` -> `_exit_criteria`, `_build_final_content` |
| 59 | Veredicto con observaciones | `APROBADO CON OBSERVACIONES = exit_passed OR coverage >= minimum_coverage_percentage` | `src/apps/reports/views.py` -> `_exit_criteria`, `_build_final_content` |
| 60 | Veredicto no aprobado | `NO APROBADO = no se cumplen las condiciones anteriores` | `src/apps/reports/views.py` -> `_exit_criteria` |

## Variables principales

| Variable | Significado en el codigo |
|---|---|
| `total_requirements` | Total de requisitos del proyecto |
| `covered_requirements` | Requisitos con al menos un caso de prueba directo o trazado |
| `direct_cases` | Casos asociados por `TestCase.requirement` |
| `traced_cases` | Casos asociados por `TraceabilityLink` |
| `total_test_cases` / `test_cases.count()` | Total de casos de prueba |
| `executed_cases` | Casos con al menos una ejecucion distinta de `NOT_RUN` |
| `total_executions` | Total de ejecuciones registradas |
| `passed`, `failed`, `blocked`, `errors`, `not_run` | Conteos por resultado de ejecucion |
| `executions_with_evidence` | Ejecuciones con evidencia o captura automatizada |
| `reviewed_executions` | Ejecuciones validadas, rechazadas o marcadas para correccion |
| `total_defects` / `defects.count()` | Total de defectos |
| `closed_defects` | Defectos cerrados |
| `critical_defects` | Defectos con severidad critica |
| `high_risks` | Riesgos cuyo nivel calculado es Alto |
| `completed_checks` | Criterios completados en una fase |
| `total_checks` | Total de criterios evaluados en una fase |

## Formulas compuestas clave

### Cobertura de requisitos

```text
covered_requirements = requisitos con caso directo OR enlace de trazabilidad
coverage = round((covered_requirements / total_requirements) * 100)
```

### Avance de ejecucion

```text
executed_cases = count(distinct test_case donde result != NOT_RUN)
execution_progress = round((executed_cases / total_test_cases) * 100)
```

### Tasa de aprobacion

```text
executed = total_executions - not_run
success_rate = round((passed / executed) * 100)
```

### Densidad de defectos

```text
defect_density = round(total_defects / executed_cases, 2)
```

### Indice global de trazabilidad

```text
traceability_index =
round((coverage + requirement_execution_rate + evidence_rate + review_rate + defect_traceability_rate) / 5)
```

### Criterios de salida

```text
exit_passed =
(coverage >= minimum_coverage_percentage)
AND (success_rate >= minimum_pass_percentage)
AND (critical_defects <= maximum_critical_defects)
```
