import os
import sys
from datetime import date, timedelta
from decimal import Decimal

sys.path.insert(0, "src")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

import django

django.setup()

from django.utils import timezone

from apps.defects.history import record_defect_history
from apps.defects.models import Defect
from apps.executions.models import TestExecution, TestStepExecution
from apps.incidents.models import Incident
from apps.phases.models import TestingPhase
from apps.projects.models import Project
from apps.reports.models import Report
from apps.requirements.models import Requirement, RequirementVersion
from apps.testcases.models import TestCase
from apps.testplans.models import TestPlan, TestPlanVersion
from apps.traceability.models import TraceabilityLink
from apps.users.models import User


STUDENT_EMAIL = "juan.castillo@unl.edu.ec"
TUTOR_EMAIL = "wilman.chamba@unl.edu.ec"
CODIRECTOR_EMAIL = "pablo.ordonez@unl.edu.ec"
PROJECT_CODE = "PRJ-004"
SOURCE_DOCUMENT = "JuanFrancisco_CastilloEstrella.pdf"


def get_user(email, role):
    user, _ = User.objects.get_or_create(
        email=email,
        defaults={"role": role, "is_active": True},
    )
    user.role = role
    user.is_active = True
    user.save()
    return user


def upsert_requirement(project, user, code, title, description, req_type, priority="HIGH"):
    requirement, _ = Requirement.objects.update_or_create(
        project=project,
        code=code,
        defaults={
            "title": title,
            "description": description,
            "requirement_type": req_type,
            "priority": priority,
            "status": Requirement.Status.APPROVED,
            "created_by": user,
        },
    )
    RequirementVersion.objects.update_or_create(
        requirement=requirement,
        version_number=1,
        defaults={
            "title": title,
            "description": description,
            "requirement_type": req_type,
            "priority": priority,
            "status": Requirement.Status.APPROVED,
            "changed_by": user,
            "change_reason": "Carga inicial desde TIC de Juan Francisco Castillo Estrella.",
            "snapshot": {
                "source": SOURCE_DOCUMENT,
                "standard": "RAD, IEEE 829, TAM",
            },
        },
    )
    return requirement


def upsert_test_case(plan, requirement, user, code, title, steps, expected, technique):
    steps_data = [
        {
            "action": step.strip(),
            "expected": expected,
        }
        for step in steps.split("\n")
        if step.strip()
    ]
    test_case, _ = TestCase.objects.update_or_create(
        test_plan=plan,
        code=code,
        defaults={
            "requirement": requirement,
            "title": title,
            "description": f"Caso derivado de {requirement.code} del TIC de Juan Castillo.",
            "technique": technique,
            "level": TestCase.Level.SYSTEM,
            "preconditions": "Aplicacion web desplegada, usuario disponible y datos de prueba preparados.",
            "test_data": "Datos documentados en pruebas unitarias Jest, pruebas funcionales Cypress y anexos del TIC.",
            "steps": steps,
            "steps_data": steps_data,
            "expected_result": expected,
            "version": "1.0",
            "priority": TestCase.Priority.HIGH,
            "status": TestCase.Status.PENDING,
            "created_by": user,
        },
    )
    TraceabilityLink.objects.get_or_create(
        requirement=requirement,
        test_case=test_case,
        defaults={"rationale": "Cobertura directa requisito-caso segun ERS, casos de uso y anexos de pruebas."},
    )
    return test_case


def reset_project_runtime_data(project):
    TestExecution.objects.filter(test_case__test_plan__project=project).delete()
    TestCase.objects.filter(test_plan__project=project).delete()
    Defect.objects.filter(project=project).delete()
    Incident.objects.filter(project=project).delete()
    Report.objects.filter(project=project).delete()


def create_execution(test_case, user, result, actual_result, days_offset, execution_type=None, related_defect=None, review_status=None):
    executed_at = timezone.now() - timedelta(days=days_offset)
    if execution_type is None:
        execution_type = TestExecution.ExecutionType.NORMAL
    if review_status is None:
        review_status = TestExecution.ReviewStatus.VALIDATED if result == TestExecution.Result.PASSED else TestExecution.ReviewStatus.NEEDS_FIX

    execution = TestExecution.objects.create(
        test_case=test_case,
        execution_mode=TestExecution.ExecutionMode.MANUAL,
        execution_type=execution_type,
        related_defect=related_defect,
        planned_date=date(2024, 12, 6),
        executed_by=user,
        executed_at=executed_at,
        started_at=executed_at,
        finished_at=executed_at + timedelta(minutes=4),
        duration_seconds=Decimal("240.000"),
        result=result,
        actual_result=actual_result,
        test_data=test_case.test_data,
        environment="Frontend React, backend Node/Nest, base de datos PostgreSQL y pruebas Jest/Cypress documentadas.",
        browser="Chrome",
        step_results=[
            {
                "step_number": idx + 1,
                "action": item.get("action", ""),
                "expected": item.get("expected", ""),
                "obtained": actual_result,
                "status": result if idx == len(test_case.steps_data or []) - 1 else TestExecution.Result.PASSED,
            }
            for idx, item in enumerate(test_case.steps_data or [])
        ],
        notes="Ejecucion reconstruida desde el TIC y sus anexos de pruebas. Los defectos representan incidencias corregidas durante iteraciones RAD.",
        review_status=review_status,
        reviewed_by=user,
        reviewed_at=executed_at + timedelta(minutes=8),
        review_notes="Revision documental registrada para trazabilidad academica.",
    )
    for idx, item in enumerate(test_case.steps_data or [], start=1):
        step_status = result if idx == len(test_case.steps_data or []) else TestExecution.Result.PASSED
        TestStepExecution.objects.create(
            test_execution=execution,
            step_number=idx,
            action=item.get("action", ""),
            expected_result=item.get("expected", ""),
            obtained_result=actual_result,
            status=step_status,
            comment="Paso registrado desde evidencia documental.",
            started_at=executed_at,
            finished_at=executed_at + timedelta(minutes=1),
        )
    return execution


def create_defect(project, execution, user, code, title, description, severity, priority, status):
    defect = Defect.objects.create(
        project=project,
        execution=execution,
        code=code,
        title=title,
        description=description,
        steps_to_reproduce=execution.test_case.steps,
        severity=severity,
        priority=priority,
        status=status,
        reported_by=user,
        assigned_to=user,
    )
    record_defect_history(defect, user, "Defecto registrado desde ejecucion fallida documentada.")
    return defect


def main():
    student = get_user(STUDENT_EMAIL, User.Roles.STUDENT)
    tutor = get_user(TUTOR_EMAIL, User.Roles.TEACHER)
    codirector = get_user(CODIRECTOR_EMAIL, User.Roles.TEACHER)

    project, _ = Project.objects.update_or_create(
        code=PROJECT_CODE,
        defaults={
            "name": "Software para el diseno de casos de prueba funcionales a partir de casos de uso",
            "description": (
                "Trabajo de Integracion Curricular de Juan Francisco Castillo Estrella. "
                "Herramienta web que usa una API de IA para generar casos de prueba funcionales "
                "desde casos de uso, desarrollada con metodologia RAD y evaluada con TAM."
            ),
            "status": Project.Status.ACTIVE,
            "start_date": date(2024, 10, 8),
            "end_date": date(2025, 3, 14),
            "created_by": student,
        },
    )
    project.members.set([student, tutor, codirector])
    reset_project_runtime_data(project)

    req_data = [
        ("RF001", "Autenticar usuario", "Permitir iniciar sesion mediante validacion de correo y contrasena.", Requirement.RequirementType.FUNCTIONAL, "HIGH"),
        ("RF002", "Registrarse", "Permitir registro con correo unico, nombre, apellido y contrasena, con rol Tester por defecto.", Requirement.RequirementType.FUNCTIONAL, "HIGH"),
        ("RF003", "Recuperar contrasena", "Permitir recuperacion de contrasena mediante OTP.", Requirement.RequirementType.FUNCTIONAL, "HIGH"),
        ("RF004", "Actualizar perfil de usuario", "Permitir modificar nombre, apellido e imagen del perfil.", Requirement.RequirementType.FUNCTIONAL, "MEDIUM"),
        ("RF005", "Actualizar roles de usuario", "Permitir que un administrador actualice roles de usuarios.", Requirement.RequirementType.FUNCTIONAL, "HIGH"),
        ("RF006", "Buscar usuarios por correo", "Permitir buscar usuarios mediante correo electronico.", Requirement.RequirementType.FUNCTIONAL, "MEDIUM"),
        ("RF007", "Desactivar usuarios", "Permitir desactivar usuarios registrados.", Requirement.RequirementType.FUNCTIONAL, "HIGH"),
        ("RF008", "Crear proyectos", "Permitir registrar proyectos con nombre, descripcion e imagen.", Requirement.RequirementType.FUNCTIONAL, "HIGH"),
        ("RF009", "Actualizar proyectos", "Permitir actualizar nombre, descripcion e imagen de proyectos.", Requirement.RequirementType.FUNCTIONAL, "HIGH"),
        ("RF010", "Buscar proyectos por nombre", "Permitir visualizar y buscar proyectos por nombre.", Requirement.RequirementType.FUNCTIONAL, "MEDIUM"),
        ("RF011", "Eliminar proyectos", "Permitir eliminar proyectos del sistema.", Requirement.RequirementType.FUNCTIONAL, "HIGH"),
        ("RF012", "Compartir proyectos", "Permitir colaborar compartiendo proyectos con otros testers mediante invitacion.", Requirement.RequirementType.FUNCTIONAL, "MEDIUM"),
        ("RF013", "Limitar proyectos por usuario", "Controlar que un usuario Tester cree como maximo 10 proyectos.", Requirement.RequirementType.FUNCTIONAL, "MEDIUM"),
        ("RF014", "Crear casos de uso", "Registrar casos de uso con nombre, descripcion, entradas, precondiciones, postcondiciones y flujos.", Requirement.RequirementType.FUNCTIONAL, "HIGH"),
        ("RF015", "Actualizar casos de uso", "Actualizar informacion de casos de uso de un proyecto.", Requirement.RequirementType.FUNCTIONAL, "HIGH"),
        ("RF016", "Buscar casos de uso", "Visualizar informacion de casos de uso de un proyecto.", Requirement.RequirementType.FUNCTIONAL, "MEDIUM"),
        ("RF017", "Eliminar casos de uso", "Permitir eliminar casos de uso de un proyecto.", Requirement.RequirementType.FUNCTIONAL, "HIGH"),
        ("RF018", "Generar casos de prueba funcionales", "Generar casos de prueba funcionales a partir de un caso de uso.", Requirement.RequirementType.FUNCTIONAL, "HIGH"),
        ("RF019", "Actualizar casos de prueba funcionales", "Actualizar nombre, descripcion, pasos, entradas y resultado esperado.", Requirement.RequirementType.FUNCTIONAL, "HIGH"),
        ("RF020", "Eliminar casos de prueba funcionales", "Permitir eliminar un caso de prueba funcional de un caso de uso.", Requirement.RequirementType.FUNCTIONAL, "HIGH"),
        ("RF021", "Buscar casos de prueba funcionales", "Visualizar casos de prueba funcionales por nombre.", Requirement.RequirementType.FUNCTIONAL, "MEDIUM"),
        ("RF022", "Generar reportes IEEE 829 en PDF", "Exportar reportes de proyectos en formato IEEE 829 y PDF.", Requirement.RequirementType.FUNCTIONAL, "MEDIUM"),
        ("RNF001", "Cierre automatico de sesion", "Cerrar sesion tras 15 minutos de inactividad.", Requirement.RequirementType.NON_FUNCTIONAL, "HIGH"),
        ("RNF002", "Cifrado de claves", "Cifrar claves de cuentas de usuario.", Requirement.RequirementType.NON_FUNCTIONAL, "CRITICAL"),
        ("RNF003", "Diseno responsive", "Adaptar el sistema a diferentes tamanos de pantalla.", Requirement.RequirementType.NON_FUNCTIONAL, "HIGH"),
        ("RNF004", "Guia de uso", "Mostrar una guia para crear casos de prueba funcionales con la herramienta.", Requirement.RequirementType.NON_FUNCTIONAL, "MEDIUM"),
        ("RNF005", "Interfaces intuitivas", "Proveer interfaces amigables para realizar el proceso de diseno de pruebas.", Requirement.RequirementType.NON_FUNCTIONAL, "HIGH"),
        ("RNF006", "Modo claro y oscuro", "Permitir cambio entre modo oscuro y claro.", Requirement.RequirementType.NON_FUNCTIONAL, "MEDIUM"),
        ("RNF007", "Eficiencia operativa", "Ejecutar operaciones comunes en menos de 5 segundos.", Requirement.RequirementType.NON_FUNCTIONAL, "HIGH"),
        ("RNF008", "Disponibilidad en laboratorio", "Mantener disponibilidad mientras la infraestructura de servidores de la carrera este operativa.", Requirement.RequirementType.NON_FUNCTIONAL, "HIGH"),
    ]
    requirements = {
        code: upsert_requirement(project, student, code, title, description, req_type, priority)
        for code, title, description, req_type, priority in req_data
    }

    plan, _ = TestPlan.objects.update_or_create(
        project=project,
        name="Plan de pruebas STLC - Generador de casos desde casos de uso",
        defaults={
            "version": "1.0",
            "description": "Plan basado en ERS, casos de uso, pruebas unitarias Jest, pruebas funcionales Cypress, despliegue Docker y evaluacion TAM.",
            "objective": "Validar autenticacion, gestion de proyectos, casos de uso, generacion con IA, casos de prueba funcionales, reportes, seguridad y usabilidad.",
            "scope": "Modulos de usuarios, proyectos, casos de uso, generacion de casos de prueba, exportacion IEEE 829/PDF, seguridad, rendimiento y disponibilidad.",
            "strategy": "Pruebas de sistema orientadas a requisitos, pruebas unitarias de servicios, pruebas funcionales end-to-end y pruebas de confirmacion para defectos corregidos.",
            "test_types": [TestPlan.TestType.FUNCTIONAL, TestPlan.TestType.SYSTEM, TestPlan.TestType.ACCEPTANCE],
            "entry_criteria": "Requisitos aprobados, casos de uso modelados, ambiente Docker definido y datos de prueba preparados.",
            "exit_criteria": "Cobertura minima del 90%, aprobacion minima del 80%, defectos criticos cerrados y evidencia documental revisada.",
            "minimum_pass_percentage": 80,
            "maximum_critical_defects": 0,
            "minimum_coverage_percentage": 90,
            "resources": "Juan Castillo, director Wilman Chamba, codirector Pablo Ordonez, React, Node/Nest, PostgreSQL, Docker, Jest, Cypress y API de IA.",
            "environment": "Ambiente academico controlado con despliegue dockerizado y ejecuciones reconstruidas desde anexos del TIC.",
            "responsibilities": "Estudiante registra pruebas y defectos; directores revisan resultados y criterios de salida.",
            "estimation": "Iteraciones RAD entre octubre y diciembre de 2024, cierre documental en marzo de 2025.",
            "start_date": date(2024, 10, 8),
            "end_date": date(2025, 3, 14),
            "status": TestPlan.Status.APPROVED,
            "created_by": student,
        },
    )
    TestPlanVersion.objects.update_or_create(
        test_plan=plan,
        version_number=1,
        defaults={
            "version_label": "1.0",
            "name": plan.name,
            "objective": plan.objective,
            "status": TestPlan.Status.APPROVED,
            "changed_by": student,
            "change_reason": "Carga inicial desde PDF de tesis.",
            "snapshot": {"source": SOURCE_DOCUMENT},
        },
    )

    case_data = [
        ("TC-001", "Autenticacion con credenciales validas", "RF001", "Abrir pagina de login\nIngresar correo y contrasena validos\nPulsar iniciar sesion", "El sistema autentica al usuario y abre el panel principal.", TestCase.Technique.USE_CASE),
        ("TC-002", "Autenticacion con credenciales invalidas", "RF001", "Abrir pagina de login\nIngresar credenciales invalidas\nPulsar iniciar sesion", "El sistema rechaza el acceso y muestra mensaje de cuenta no encontrada.", TestCase.Technique.NEGATIVE if hasattr(TestCase.Technique, "NEGATIVE") else TestCase.Technique.BLACK_BOX),
        ("TC-003", "Recuperacion de contrasena con OTP", "RF003", "Solicitar recuperacion\nRecibir OTP\nValidar OTP\nRegistrar nueva contrasena", "El sistema valida el OTP y permite cambiar la contrasena.", TestCase.Technique.USE_CASE),
        ("TC-004", "Registro de usuario tester", "RF002", "Abrir registro\nIngresar nombre, apellido, correo y contrasena\nEnviar formulario", "Usuario registrado correctamente con rol Tester.", TestCase.Technique.USE_CASE),
        ("TC-005", "Cambio de rol por administrador", "RF005", "Iniciar como administrador\nBuscar usuario\nCambiar rol\nGuardar", "Rol actualizado y visible en gestion de usuarios.", TestCase.Technique.USE_CASE),
        ("TC-006", "Desactivacion de usuario", "RF007", "Buscar usuario activo\nSeleccionar desactivar\nConfirmar accion", "Usuario cambia a estado inactivo.", TestCase.Technique.USE_CASE),
        ("TC-007", "Creacion de proyecto", "RF008", "Abrir proyectos\nCrear proyecto\nIngresar nombre descripcion e imagen\nGuardar", "Proyecto creado correctamente.", TestCase.Technique.USE_CASE),
        ("TC-008", "Actualizacion de proyecto", "RF009", "Abrir opciones de proyecto\nEditar datos\nGuardar cambios", "Proyecto actualizado correctamente.", TestCase.Technique.USE_CASE),
        ("TC-009", "Busqueda de proyectos", "RF010", "Abrir listado de proyectos\nIngresar nombre en busqueda\nRevisar resultados", "El listado muestra proyectos coincidentes.", TestCase.Technique.BLACK_BOX),
        ("TC-010", "Eliminacion de proyecto", "RF011", "Seleccionar proyecto\nElegir eliminar\nConfirmar eliminacion", "Proyecto eliminado logicamente.", TestCase.Technique.USE_CASE),
        ("TC-011", "Compartir proyecto con tester", "RF012", "Abrir proyecto\nIngresar correo de invitado\nEnviar invitacion", "Invitacion enviada y colaborador puede unirse al proyecto.", TestCase.Technique.USE_CASE),
        ("TC-012", "Limite de diez proyectos", "RF013", "Crear proyectos hasta llegar a diez\nIntentar crear proyecto adicional", "El sistema bloquea la creacion adicional.", TestCase.Technique.BOUNDARY),
        ("TC-013", "Creacion de caso de uso", "RF014", "Abrir proyecto\nCrear caso de uso\nCompletar entradas, precondiciones, postcondiciones y flujos\nGuardar", "Caso de uso creado correctamente.", TestCase.Technique.USE_CASE),
        ("TC-014", "Actualizacion de caso de uso", "RF015", "Abrir caso de uso\nEditar informacion\nGuardar", "Caso de uso actualizado correctamente.", TestCase.Technique.USE_CASE),
        ("TC-015", "Busqueda de casos de uso", "RF016", "Abrir proyecto\nConsultar casos de uso\nFiltrar por nombre", "Se visualizan los casos de uso del proyecto.", TestCase.Technique.BLACK_BOX),
        ("TC-016", "Eliminacion de caso de uso", "RF017", "Seleccionar caso de uso\nEliminar\nConfirmar", "Caso de uso eliminado correctamente.", TestCase.Technique.USE_CASE),
        ("TC-017", "Generacion de casos funcionales con IA", "RF018", "Seleccionar caso de uso\nPulsar generar casos de prueba\nRevisar lista generada", "Se generan N casos de prueba funcionales alineados al caso de uso.", TestCase.Technique.USE_CASE),
        ("TC-018", "Actualizacion de caso de prueba funcional", "RF019", "Abrir caso de prueba\nEditar pasos, entradas y esperado\nGuardar", "Caso de prueba funcional actualizado correctamente.", TestCase.Technique.USE_CASE),
        ("TC-019", "Eliminacion de caso de prueba funcional", "RF020", "Seleccionar caso de prueba funcional\nEliminar\nConfirmar", "Caso de prueba eliminado correctamente.", TestCase.Technique.USE_CASE),
        ("TC-020", "Busqueda de casos de prueba funcionales", "RF021", "Abrir listado de casos de prueba\nBuscar por nombre", "Se muestran casos de prueba coincidentes.", TestCase.Technique.BLACK_BOX),
        ("TC-021", "Reporte IEEE 829 en PDF", "RF022", "Abrir proyecto\nGenerar reporte IEEE 829\nExportar PDF", "Reporte PDF generado con informacion del proyecto.", TestCase.Technique.USE_CASE),
        ("TC-022", "Seguridad de claves", "RNF002", "Registrar usuario\nRevisar almacenamiento de clave\nIntentar autenticar", "La clave se almacena cifrada y la autenticacion funciona.", TestCase.Technique.WHITE_BOX),
        ("TC-023", "Responsive y modo visual", "RNF003", "Abrir la aplicacion en movil y escritorio\nCambiar modo claro/oscuro", "La interfaz se adapta y conserva legibilidad.", TestCase.Technique.EXPERIENCE),
        ("TC-024", "Rendimiento de operaciones comunes", "RNF007", "Ejecutar login, listar proyectos y generar casos\nMedir tiempos", "Operaciones comunes responden en menos de 5 segundos.", TestCase.Technique.EXPERIENCE),
    ]

    cases = {}
    for item in case_data:
        code, title, req_code, steps, expected, technique = item
        cases[code] = upsert_test_case(plan, requirements[req_code], student, code, title, steps, expected, technique)

    failing_cases = {"TC-012", "TC-017", "TC-021", "TC-022", "TC-024"}
    blocked_cases = {"TC-011"}
    executions = {}
    for index, (code, test_case) in enumerate(cases.items(), start=1):
        if code in failing_cases:
            result = TestExecution.Result.FAILED
            actual = "La ejecucion inicial detecto una desviacion funcional corregible en la iteracion correspondiente."
        elif code in blocked_cases:
            result = TestExecution.Result.BLOCKED
            actual = "La ejecucion quedo bloqueada por dependencia de invitacion/correo en ambiente de prueba."
        else:
            result = TestExecution.Result.PASSED
            actual = "APROBADO segun evidencia de pruebas unitarias, funcionales o validacion documental."
        executions[code] = create_execution(test_case, student, result, actual, 75 - index)

    defects = [
        ("DEF-001", "Validacion de limite de proyectos no bloquea el undecimo registro", "El limite de 10 proyectos por Tester no impidio un intento adicional en la prueba de frontera.", "TC-012", Defect.Severity.MEDIUM, Defect.Priority.HIGH, Defect.Status.CLOSED),
        ("DEF-002", "Generacion IA devuelve casos incompletos ante flujo alterno", "La generacion inicial omitio escenarios alternos del caso de uso seleccionado.", "TC-017", Defect.Severity.HIGH, Defect.Priority.HIGH, Defect.Status.CLOSED),
        ("DEF-003", "Reporte IEEE 829 omite seccion de riesgos", "El PDF generado no incluyo riesgos/incidentes del proyecto en la primera verificacion.", "TC-021", Defect.Severity.MEDIUM, Defect.Priority.MEDIUM, Defect.Status.PENDING_CONFIRMATION),
        ("DEF-004", "Clave de usuario visible en traza de depuracion", "Durante la validacion de seguridad se detecto informacion sensible en logs de depuracion.", "TC-022", Defect.Severity.CRITICAL, Defect.Priority.CRITICAL, Defect.Status.CLOSED),
        ("DEF-005", "Operacion de generacion supera cinco segundos", "La generacion de casos funcionales supero el umbral de rendimiento bajo carga documental.", "TC-024", Defect.Severity.MEDIUM, Defect.Priority.HIGH, Defect.Status.IN_PROGRESS),
        ("DEF-006", "Invitacion de proyecto depende de correo no configurado", "La prueba de compartir proyecto quedo bloqueada por configuracion de envio de correo.", "TC-011", Defect.Severity.LOW, Defect.Priority.MEDIUM, Defect.Status.ANALYSIS),
    ]
    created_defects = {}
    for code, title, description, case_code, severity, priority, status in defects:
        created_defects[code] = create_defect(project, executions[case_code], student, code, title, description, severity, priority, status)

    confirmation_map = [
        ("TC-012", "DEF-001", TestExecution.Result.PASSED, "Confirmacion aprobada: el limite de diez proyectos queda controlado."),
        ("TC-017", "DEF-002", TestExecution.Result.PASSED, "Confirmacion aprobada: la generacion cubre flujo normal y alternos."),
        ("TC-021", "DEF-003", TestExecution.Result.FAILED, "Confirmacion fallida: el reporte aun requiere validar la seccion de riesgos."),
        ("TC-022", "DEF-004", TestExecution.Result.PASSED, "Confirmacion aprobada: la traza ya no expone informacion sensible."),
    ]
    for index, (case_code, defect_code, result, actual) in enumerate(confirmation_map, start=1):
        create_execution(
            cases[case_code],
            student,
            result,
            actual,
            25 - index,
            execution_type=TestExecution.ExecutionType.CONFIRMATION,
            related_defect=created_defects[defect_code],
        )

    create_execution(
        cases["TC-017"],
        student,
        TestExecution.Result.PASSED,
        "Regresion aprobada: la correccion de generacion no afecta actualizacion ni busqueda de casos de prueba.",
        16,
        execution_type=TestExecution.ExecutionType.REGRESSION,
        related_defect=created_defects["DEF-002"],
    )

    for code, title, description, mitigation, probability, impact, req_code, status in [
        ("INC-001", "Dependencia de API de IA", "La generacion de casos depende de disponibilidad y calidad de la API externa.", "Registrar reintentos, validar respuesta y permitir edicion manual.", Incident.Probability.MEDIUM, Incident.Impact.HIGH, "RF018", Incident.Status.MITIGATED),
        ("INC-002", "Disponibilidad de infraestructura", "El sistema depende de servidores del laboratorio de software.", "Mantener despliegue dockerizado reproducible y monitoreo basico.", Incident.Probability.MEDIUM, Incident.Impact.HIGH, "RNF008", Incident.Status.OPEN),
        ("INC-003", "Rendimiento de generacion", "La generacion con IA puede superar el limite de cinco segundos.", "Optimizar prompt, cachear resultados y medir tiempos por escenario.", Incident.Probability.HIGH, Incident.Impact.MEDIUM, "RNF007", Incident.Status.ANALYSIS),
        ("INC-004", "Calidad de casos generados", "Los casos generados pueden requerir correccion manual si el caso de uso esta incompleto.", "Agregar guia de uso, validaciones y revision del tester.", Incident.Probability.MEDIUM, Incident.Impact.MEDIUM, "RNF004", Incident.Status.MITIGATED),
    ]:
        Incident.objects.update_or_create(
            project=project,
            code=code,
            defaults={
                "requirement": requirements[req_code],
                "test_plan": plan,
                "title": title,
                "description": description,
                "mitigation_strategy": mitigation,
                "probability": probability,
                "impact": impact,
                "status": status,
                "reported_by": student,
            },
        )

    now = timezone.now()
    phase_data = [
        (1, "Analisis de requisitos", "Brainstorming, ERS y requisitos RF/RNF del generador de casos.", "Tema y alcance aprobados.", "22 RF y 8 RNF aprobados y versionados.", 100, TestingPhase.Status.DONE, 6, 0),
        (2, "Planificacion y riesgos", "Plan STLC, estrategia, criterios y riesgos sobre IA, seguridad y disponibilidad.", "Requisitos aprobados.", "Plan aprobado con riesgos registrados.", 100, TestingPhase.Status.DONE, 5, 0),
        (3, "Diseno de pruebas", "Casos derivados de casos de uso principales y RNF.", "Plan aprobado.", "Casos trazados a requisitos.", 100, TestingPhase.Status.DONE, 7, 0),
        (4, "Preparacion del ambiente", "Ambiente React/Node/PostgreSQL, Docker, Jest y Cypress documentado.", "Casos definidos.", "Ambiente listo para ejecucion.", 90, TestingPhase.Status.DONE, 5, 1),
        (5, "Ejecucion y gestion de defectos", "Ejecuciones normales, bloqueadas, fallidas, confirmacion y regresion.", "Ambiente disponible.", "Defectos criticos cerrados y pendientes no criticos trazados.", 85, TestingPhase.Status.IN_PROGRESS, 8, 2),
        (6, "Cierre e informes", "Resumen final con metricas de cobertura, ejecucion, defectos, riesgos y TAM.", "Ejecuciones principales finalizadas.", "Informe final y reporte IEEE 829 revisados.", 75, TestingPhase.Status.IN_PROGRESS, 4, 2),
    ]
    for order, name, description, entry, exit_criteria, progress, status, done, pending in phase_data:
        TestingPhase.objects.update_or_create(
            project=project,
            order=order,
            defaults={
                "name": name,
                "status": status,
                "description": description,
                "entry_criteria": entry,
                "exit_criteria": exit_criteria,
                "progress": progress,
                "completed_tasks": done,
                "pending_tasks": pending,
                "started_at": now - timedelta(days=95 - order),
                "completed_at": now - timedelta(days=88 - order) if status == TestingPhase.Status.DONE else None,
                "updated_by": student,
            },
        )

    Report.objects.update_or_create(
        project=project,
        title="Resumen final documental - Proyecto Juan Castillo",
        report_type=Report.ReportType.FINAL,
        defaults={
            "generated_by": student,
            "content": {
                "source": SOURCE_DOCUMENT,
                "methodology": "RAD + STLC/ISTQB",
                "evaluation": "TAM con percepcion de utilidad media/alta documentada en 86.464%",
                "requirements": Requirement.objects.filter(project=project).count(),
                "test_cases": TestCase.objects.filter(test_plan=plan).count(),
                "executions": TestExecution.objects.filter(test_case__test_plan=plan).count(),
                "defects": Defect.objects.filter(project=project).count(),
                "open_defects": Defect.objects.filter(project=project).exclude(status=Defect.Status.CLOSED).count(),
                "risks": Incident.objects.filter(project=project).count(),
                "phases": TestingPhase.objects.filter(project=project).count(),
                "summary": "Carga adaptada a STLC/ISTQB con requisitos, plan, casos, ejecuciones, defectos, riesgos, fases y trazabilidad desde el TIC.",
            },
        },
    )

    for test_case in cases.values():
        latest = test_case.executions.order_by("-executed_at").first()
        if latest:
            test_case.status = {
                TestExecution.Result.PASSED: TestCase.Status.PASSED,
                TestExecution.Result.FAILED: TestCase.Status.FAILED,
                TestExecution.Result.BLOCKED: TestCase.Status.BLOCKED,
            }.get(latest.result, TestCase.Status.PENDING)
            test_case.save(update_fields=["status", "updated_at"])

    print("Proyecto cargado:", project.code, project.name)
    print("Usuario estudiante:", student.email)
    print("Directores asignados:", tutor.email, codirector.email)
    print("Requisitos:", Requirement.objects.filter(project=project).count())
    print("Casos de prueba:", TestCase.objects.filter(test_plan=plan).count())
    print("Ejecuciones:", TestExecution.objects.filter(test_case__test_plan=plan).count())
    print("Defectos:", Defect.objects.filter(project=project).count())
    print("Riesgos/incidentes:", Incident.objects.filter(project=project).count())
    print("Fases:", TestingPhase.objects.filter(project=project).count())


if __name__ == "__main__":
    main()
