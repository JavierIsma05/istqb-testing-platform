# Reporte de pruebas automatizadas

Fecha de ejecucion: 2026-06-01

Proyecto: Plataforma Web ISTQB Testing Lifecycle

## Resumen ejecutivo

Se ejecuto la suite automatizada con `pytest`, `pytest-django` y `pytest-cov`.

Resultado general:

```text
30 pruebas ejecutadas
30 pruebas pasadas
0 pruebas fallidas
Cobertura total: 74%
```

Interpretacion general:

- La base probada del sistema esta funcionando correctamente.
- Las pruebas actuales cubren modelos, formularios, relaciones principales, autenticacion basica, proteccion de algunas vistas y un flujo completo del ciclo ISTQB.
- La cobertura muestra que el siguiente punto a reforzar son las vistas (`views.py`), donde todavia hay rutas y acciones que no se ejecutan en pruebas.

## Comando utilizado

Desde la raiz del proyecto:

```powershell
python -m pytest
```

Este comando ejecuta todas las pruebas configuradas en el proyecto y genera el reporte de cobertura en consola.

## Que significa la tabla de cobertura

Ejemplo de la salida:

```text
Name                                          Stmts   Miss  Cover   Missing
src\apps\projects\views.py                       79     55    30%   27-40, 54-104, 122-132
```

Significado de cada columna:

| Columna | Significado |
| --- | --- |
| `Name` | Archivo analizado por coverage. |
| `Stmts` | Cantidad de sentencias o lineas ejecutables detectadas en el archivo. |
| `Miss` | Cantidad de sentencias que no fueron ejecutadas por ninguna prueba. |
| `Cover` | Porcentaje del archivo cubierto por pruebas. |
| `Missing` | Numeros de linea que no fueron ejecutados durante las pruebas. |

Ejemplo interpretado:

```text
src\apps\projects\views.py   Stmts: 79   Miss: 55   Cover: 30%
```

Esto significa:

- El archivo tiene 79 sentencias ejecutables.
- Las pruebas no ejecutaron 55 de esas sentencias.
- Solo el 30% de ese archivo fue cubierto.
- Las lineas indicadas en `Missing` son candidatas para nuevas pruebas.

## Resultado de cobertura actual

Cobertura total:

```text
TOTAL: 74%
```

Archivos con cobertura baja o pendiente de reforzar:

| Archivo | Cobertura | Observacion |
| --- | ---: | --- |
| `src/apps/core/module_views.py` | 0% | No hay pruebas para vistas genericas/modulares. |
| `src/apps/requirements/views.py` | 26% | Faltan pruebas de listado y creacion de requisitos por vista. |
| `src/apps/testcases/views.py` | 26% | Faltan pruebas de vistas de casos de prueba. |
| `src/apps/traceability/views.py` | 27% | Faltan pruebas de matriz de trazabilidad. |
| `src/apps/projects/views.py` | 30% | Faltan pruebas de CRUD, detalle y eliminacion. |
| `src/apps/defects/views.py` | 31% | Faltan pruebas de creacion/listado de defectos desde vista. |
| `src/apps/executions/views.py` | 32% | Faltan pruebas de ejecucion de casos desde vista. |
| `src/apps/reports/views.py` | 34% | Faltan pruebas de generacion, detalle y descarga de reportes. |
| `src/apps/phases/views.py` | 35% | Faltan pruebas de visualizacion de fases. |
| `src/apps/incidents/views.py` | 39% | Faltan pruebas de creacion/listado de incidencias. |
| `src/apps/notifications/views.py` | 39% | Faltan pruebas de lectura, envio y marcado de notificaciones. |

## Pruebas automatizadas incluidas

### Usuarios

- `test_usuario_se_crea_con_email_como_identificador`
- `test_usuario_no_se_crea_sin_email`
- `test_superusuario_se_crea_con_permisos_de_administrador`

Validan que el modelo de usuario use email, rechace usuarios sin correo y cree superusuarios con permisos administrativos.

### Autenticacion

- `test_pagina_de_login_responde_correctamente`
- `test_pagina_de_registro_responde_correctamente`

Validan que las pantallas publicas de login y registro respondan correctamente.

### Dashboard

- `test_dashboard_redirige_a_login_si_no_hay_sesion`

Valida que el dashboard no permita acceso anonimo.

### Proyectos

- `test_proyecto_guarda_codigo_nombre_y_estado_por_defecto`
- `test_formulario_de_proyecto_es_valido_con_datos_minimos`
- `test_lista_de_proyectos_redirige_a_login_si_no_hay_sesion`

Validan modelo, formulario y proteccion basica de la lista de proyectos.

### Requisitos

- `test_requisito_se_asocia_a_proyecto_y_tiene_prioridad_media_por_defecto`
- `test_formulario_de_requisito_es_valido_con_datos_obligatorios`

Validan la relacion requisito-proyecto y el formulario de requisitos.

### Planes de prueba

- `test_plan_de_pruebas_se_crea_en_borrador_por_defecto`
- `test_formulario_de_plan_de_pruebas_es_valido_con_objetivo`

Validan estado inicial y formulario de planes de prueba.

### Casos de prueba

- `test_caso_de_prueba_relaciona_plan_y_requisito`
- `test_formulario_de_caso_de_prueba_es_valido_con_pasos_y_resultado`

Validan la relacion entre plan, requisito y caso de prueba.

### Ejecuciones

- `test_ejecucion_registra_resultado_y_responsable`
- `test_formulario_de_resultado_no_permite_estado_no_ejecutado`

Validan resultados de ejecucion y reglas del formulario.

### Defectos

- `test_defecto_se_registra_con_proyecto_ejecucion_y_reportante`
- `test_formulario_de_defecto_es_valido_sin_ejecucion_asociada`

Validan registro de defectos y formulario.

### Incidentes

- `test_incidencia_se_crea_abierta_con_probabilidad_e_impacto_medios`
- `test_formulario_de_incidencia_es_valido_con_datos_minimos`

Validan estado inicial, impacto, probabilidad y formulario.

### Trazabilidad

- `test_trazabilidad_conecta_requisito_con_caso_de_prueba`
- `test_trazabilidad_no_permite_duplicar_requisito_y_caso`

Validan que un requisito pueda vincularse a un caso y que no se duplique el mismo vinculo.

### Reportes

- `test_reporte_guarda_tipo_contenido_y_usuario_generador`
- `test_formulario_de_reporte_es_valido_con_tipo_de_cobertura`

Validan modelo y formulario de reportes.

### Notificaciones

- `test_notificacion_se_crea_como_no_leida`
- `test_usuario_cuenta_notificaciones_no_leidas`

Validan creacion de notificaciones y conteo de no leidas.

### Fases

- `test_fase_de_testing_se_crea_pendiente_y_ordenada`

Valida estado inicial y datos de fase.

### Auditoria

- `test_auditoria_registra_actor_accion_entidad_y_metadata`

Valida registro de acciones auditables.

### Flujo completo ISTQB

- `test_flujo_completo_del_ciclo_de_pruebas_istqb`

Valida un recorrido integrado:

```text
Proyecto
-> Requisito
-> Plan de pruebas
-> Caso de prueba
-> Trazabilidad
-> Ejecucion fallida
-> Defecto
-> Reporte
```

Esta prueba ayuda a confirmar que las entidades principales del ciclo ISTQB pueden trabajar conectadas.

## Como interpretar el 74% de cobertura

El 74% no significa que el sistema este 74% terminado. Significa que, durante las pruebas, se ejecuto el 74% de las sentencias Python medidas.

Una cobertura alta ayuda, pero no garantiza por si sola que todo este correcto. La calidad depende tambien de que las pruebas validen reglas importantes, errores, permisos y flujos reales.

En este momento se puede afirmar:

- La base de modelos y formularios principales funciona.
- Las relaciones centrales del ciclo ISTQB funcionan.
- Hay una prueba integrada que conecta el flujo principal.
- Faltan pruebas mas fuertes sobre vistas, permisos y acciones por navegador.

## Recomendaciones siguientes

Prioridad 1:

- Probar vistas con usuario autenticado.
- Probar creacion por `POST` de proyectos, requisitos, planes, casos, defectos e incidentes.
- Probar permisos por rol: administrador, docente y estudiante.

Prioridad 2:

- Agregar pruebas de errores: codigos duplicados, formularios incompletos y datos invalidos.
- Agregar pruebas de reportes: detalle, descarga y contenido generado.
- Agregar pruebas de notificaciones: marcar como leida, marcar todas, enviar mensaje.

Prioridad 3:

- Usar Playwright para pruebas visuales y de navegador real.
- Validar flujos desde la interfaz, no solo desde el backend.

## Conclusiones

La suite actual es una base solida para validar funcionalidad. Todas las pruebas pasan y el proyecto ya cuenta con medicion de cobertura.

El siguiente avance recomendable es aumentar cobertura en las vistas y permisos, porque ahi se concentran los porcentajes mas bajos y los flujos mas cercanos al uso real del sistema.
