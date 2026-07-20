import os
import sys
from datetime import date, timedelta
from decimal import Decimal

sys.path.insert(0, "src")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

import django

django.setup()

from django.utils import timezone

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


STUDENT_EMAIL = "cristian.capa@unl.edu.ec"
TUTOR_EMAIL = "francisco@unl.edu.ec"
PROJECT_CODE = "PRJ-003"


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
            "change_reason": "Carga inicial desde ERS IEEE 830 del proyecto de Cristian Capa.",
            "snapshot": {
                "source": "Cristian Ramiro_Capa Rodriguez.pdf",
                "standard": "IEEE 830",
            },
        },
    )
    return requirement


def upsert_test_case(plan, requirement, user, code, title, steps, expected, technique=TestCase.Technique.USE_CASE):
    test_case, _ = TestCase.objects.update_or_create(
        test_plan=plan,
        code=code,
        defaults={
            "requirement": requirement,
            "title": title,
            "description": f"Caso derivado del requisito {requirement.code} documentado en el TIC de Cristian Capa.",
            "technique": technique,
            "level": TestCase.Level.SYSTEM,
            "preconditions": "Usuario autenticado y proyecto disponible en el sistema.",
            "test_data": "Datos de prueba documentados o inferidos desde los anexos de pruebas unitarias y K6.",
            "steps": steps,
            "steps_data": [
                {"action": step.strip(), "expected": expected}
                for step in steps.split("\n")
                if step.strip()
            ],
            "expected_result": expected,
            "version": "1.0",
            "priority": TestCase.Priority.HIGH,
            "status": TestCase.Status.PASSED,
            "created_by": user,
        },
    )
    TraceabilityLink.objects.get_or_create(
        requirement=requirement,
        test_case=test_case,
        defaults={"rationale": "Cobertura directa requisito-caso segun ERS y anexos de pruebas."},
    )
    return test_case


def create_passed_execution(test_case, user, actual_result, days_offset):
    executed_at = timezone.now() - timedelta(days=days_offset)
    execution, _ = TestExecution.objects.update_or_create(
        test_case=test_case,
        execution_type=TestExecution.ExecutionType.NORMAL,
        defaults={
            "execution_mode": TestExecution.ExecutionMode.MANUAL,
            "planned_date": date(2025, 1, 22),
            "executed_by": user,
            "executed_at": executed_at,
            "started_at": executed_at,
            "finished_at": executed_at + timedelta(minutes=3),
            "duration_seconds": Decimal("180.000"),
            "result": TestExecution.Result.PASSED,
            "actual_result": actual_result,
            "test_data": test_case.test_data,
            "environment": "Backend Strapi, frontend React, entorno controlado de pruebas academicas.",
            "browser": "No aplica / API",
            "step_results": [
                {
                    "step_number": idx + 1,
                    "action": item.get("action", ""),
                    "expected": item.get("expected", ""),
                    "obtained": actual_result,
                    "status": TestExecution.Result.PASSED,
                }
                for idx, item in enumerate(test_case.steps_data or [])
            ],
            "notes": "Ejecucion cargada a partir de resultados documentados en anexos del TIC. No se ejecuto el software original localmente.",
            "review_status": TestExecution.ReviewStatus.VALIDATED,
            "reviewed_by": user,
            "reviewed_at": executed_at + timedelta(minutes=4),
            "review_notes": "Resultado aprobado segun evidencia documental.",
        },
    )
    execution.step_executions.all().delete()
    for idx, item in enumerate(test_case.steps_data or [], start=1):
        TestStepExecution.objects.create(
            test_execution=execution,
            step_number=idx,
            action=item.get("action", ""),
            expected_result=item.get("expected", ""),
            obtained_result=actual_result,
            status=TestExecution.Result.PASSED,
            comment="Paso aprobado desde evidencia documental.",
            started_at=executed_at,
            finished_at=executed_at + timedelta(minutes=1),
        )
    return execution


def main():
    student = get_user(STUDENT_EMAIL, User.Roles.STUDENT)
    tutor = get_user(TUTOR_EMAIL, User.Roles.TEACHER)

    project, _ = Project.objects.update_or_create(
        code=PROJECT_CODE,
        defaults={
            "name": "Arquitectura Headless para gestion de metadatos en proyectos de integracion curricular",
            "description": (
                "Proyecto de Cristian Ramiro Capa Rodriguez. Aplicacion web para gestionar "
                "metadatos, documentos, comentarios, notificaciones y comparacion de versiones "
                "en proyectos de integracion curricular de la Carrera de Computacion de la UNL."
            ),
            "status": Project.Status.ACTIVE,
            "start_date": date(2024, 11, 12),
            "end_date": date(2025, 1, 22),
            "created_by": student,
        },
    )
    project.members.set([student, tutor])

    req_data = [
        ("RF-01", "Crear proyecto", "Crear un nuevo proyecto especificando titulo, descripcion y docente tutor.", Requirement.RequirementType.FUNCTIONAL),
        ("RF-02", "Subir documento", "Subir documentos al proyecto especificando titulo y archivo.", Requirement.RequirementType.FUNCTIONAL),
        ("RF-03", "Agregar comentarios", "Seleccionar texto en los documentos y agregar comentarios sobre el mismo.", Requirement.RequirementType.FUNCTIONAL),
        ("RF-04", "Recibir notificaciones", "Recibir notificaciones cuando un estudiante sube un nuevo documento.", Requirement.RequirementType.FUNCTIONAL),
        ("RF-05", "Acceso directo al documento", "Permitir al docente acceder directamente al documento nuevo desde la notificacion.", Requirement.RequirementType.FUNCTIONAL),
        ("RF-06", "Filtrar proyectos", "Filtrar proyectos por fecha de creacion, itinerario o autor.", Requirement.RequirementType.FUNCTIONAL),
        ("RF-07", "Generar informe de finalizacion", "Generar un informe detallado con la informacion relevante del proyecto.", Requirement.RequirementType.FUNCTIONAL),
        ("RF-08", "Visualizar proyectos", "Ver el listado de todos los proyectos creados o asociados.", Requirement.RequirementType.FUNCTIONAL),
        ("RF-09", "Visualizar documentos", "Ver el listado de todos los documentos dentro de un proyecto.", Requirement.RequirementType.FUNCTIONAL),
        ("RF-10", "Visualizar comentarios", "Ver todos los comentarios realizados por el tutor en los documentos.", Requirement.RequirementType.FUNCTIONAL),
        ("RF-11", "Comparar documentos", "Comparar diferentes versiones de documentos para identificar cambios.", Requirement.RequirementType.FUNCTIONAL),
        ("RF-12", "Configuracion de correo de envio", "Modificar la direccion de correo utilizada para envios a estudiantes y docentes.", Requirement.RequirementType.FUNCTIONAL),
        ("RNF-01", "Seguridad de acceso", "Autenticar usuarios y permitir acceso solo a recursos autorizados.", Requirement.RequirementType.NON_FUNCTIONAL),
        ("RNF-02", "Soporte de documentos PDF", "Soportar almacenamiento y gestion de documentos en formato PDF.", Requirement.RequirementType.NON_FUNCTIONAL),
        ("RNF-03", "Eficiencia en notificacion", "Enviar notificaciones inmediatas cuando se suba una nueva version del documento.", Requirement.RequirementType.NON_FUNCTIONAL),
        ("RNF-04", "Mantenibilidad de registros", "Mantener registro de documentos y comentarios para actualizaciones futuras.", Requirement.RequirementType.NON_FUNCTIONAL),
        ("RNF-05", "Portabilidad de interfaz", "Adaptar la interfaz a diferentes tamanos de pantalla.", Requirement.RequirementType.NON_FUNCTIONAL),
        ("RNF-06", "Usabilidad", "Ofrecer una interfaz intuitiva y facil de usar.", Requirement.RequirementType.NON_FUNCTIONAL),
        ("RNF-07", "Disponibilidad", "Garantizar al menos 90% de disponibilidad mensual.", Requirement.RequirementType.NON_FUNCTIONAL),
    ]
    requirements = {
        code: upsert_requirement(project, student, code, title, description, req_type)
        for code, title, description, req_type in req_data
    }

    plan, _ = TestPlan.objects.update_or_create(
        project=project,
        name="Plan de pruebas STLC - Proyecto Headless CMS",
        defaults={
            "version": "1.0",
            "description": "Plan adaptado desde la ERS IEEE 830, casos de uso, pruebas unitarias Jest y pruebas de rendimiento K6 documentadas.",
            "objective": "Validar requisitos funcionales, no funcionales, trazabilidad y resultados principales del sistema de gestion de metadatos.",
            "scope": "Gestion de proyectos, documentos, comentarios, notificaciones, comparacion, reportes, seguridad, PDF, usabilidad, portabilidad y rendimiento API.",
            "strategy": "Pruebas de sistema basadas en casos de uso, pruebas de API documentadas como unitarias y pruebas de rendimiento con K6.",
            "test_types": [TestPlan.TestType.FUNCTIONAL, TestPlan.TestType.SYSTEM, TestPlan.TestType.ACCEPTANCE],
            "entry_criteria": "ERS aprobada, casos de uso identificados, endpoints disponibles y datos de prueba definidos.",
            "exit_criteria": "Cobertura minima del 90%, tasa de aprobacion minima del 80% y cero defectos criticos abiertos.",
            "minimum_pass_percentage": 80,
            "maximum_critical_defects": 0,
            "minimum_coverage_percentage": 90,
            "resources": "Cristian Capa, tutor academico, backend Strapi, frontend React, Jest, K6, Grafana, Docker, Vercel, Railway y Supabase.",
            "environment": "Entorno academico controlado documentado en el TIC; resultados cargados por evidencia documental.",
            "responsibilities": "Estudiante ejecuta y documenta pruebas; tutor revisa evidencia y resultados.",
            "estimation": "Ciclo de pruebas documental entre noviembre 2024 y enero 2025.",
            "start_date": date(2024, 11, 12),
            "end_date": date(2025, 1, 22),
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
            "snapshot": {"source": "Cristian Ramiro_Capa Rodriguez.pdf"},
        },
    )

    cases = [
        ("TC-001", "Validar creacion de proyecto", "RF-01", "Ingresar a proyectos\nCrear nuevo proyecto\nRegistrar titulo, descripcion y tutor\nGuardar proyecto", "Proyecto creado y asignado a tutor correctamente."),
        ("TC-002", "Validar subida de documento PDF", "RF-02", "Abrir proyecto\nSeleccionar subir documento\nIngresar titulo y archivo PDF\nConfirmar carga", "Documento almacenado y asociado al proyecto."),
        ("TC-003", "Validar comentario de tutor", "RF-03", "Abrir documento\nSeleccionar contenido\nIngresar comentario\nGuardar comentario", "Comentario registrado sobre el documento."),
        ("TC-004", "Validar notificacion por nuevo documento", "RF-04", "Subir nuevo documento\nConsultar notificaciones del tutor", "Notificacion generada de forma inmediata."),
        ("TC-005", "Validar acceso directo desde notificacion", "RF-05", "Abrir notificacion\nSeleccionar enlace del documento", "El docente accede al documento nuevo."),
        ("TC-006", "Validar filtrado de proyectos", "RF-06", "Abrir listado de proyectos\nAplicar filtro por autor o itinerario", "Listado filtrado correctamente."),
        ("TC-007", "Validar informe final", "RF-07", "Abrir modulo de informes\nGenerar informe del proyecto", "Informe generado con informacion relevante del proyecto."),
        ("TC-008", "Validar visualizacion de proyectos", "RF-08", "Iniciar sesion\nAbrir proyectos", "Se visualizan los proyectos asociados."),
        ("TC-009", "Validar visualizacion de documentos", "RF-09", "Abrir proyecto\nConsultar documentos", "Se listan los documentos del proyecto."),
        ("TC-010", "Validar visualizacion de comentarios", "RF-10", "Abrir documento\nConsultar comentarios", "Se muestran los comentarios del tutor."),
        ("TC-011", "Validar comparacion de documentos", "RF-11", "Seleccionar dos versiones\nEjecutar comparacion", "El sistema informa diferencias o ausencia de cambios."),
        ("TC-012", "Validar configuracion de correo", "RF-12", "Abrir configuracion\nModificar correo de envio\nGuardar cambios", "Correo de envio actualizado."),
        ("TC-013", "Validar seguridad de acceso", "RNF-01", "Intentar acceder sin sesion\nIniciar sesion con usuario autorizado", "Acceso restringido y autenticacion correcta."),
        ("TC-014", "Validar gestion de PDF", "RNF-02", "Subir documento PDF\nConsultar documento almacenado", "PDF aceptado, almacenado y visible."),
        ("TC-015", "Validar eficiencia de notificacion", "RNF-03", "Subir nueva version de documento\nMedir aparicion de notificacion", "Notificacion disponible inmediatamente."),
        ("TC-016", "Validar mantenibilidad de registros", "RNF-04", "Crear documento y comentario\nConsultar historial funcional", "Registros conservados para seguimiento."),
        ("TC-017", "Validar portabilidad de interfaz", "RNF-05", "Abrir interfaz en diferentes tamanos de pantalla", "La interfaz se adapta correctamente."),
        ("TC-018", "Validar usabilidad", "RNF-06", "Ejecutar flujo de crear proyecto y subir documento", "Flujo comprensible y sin bloqueos para el usuario."),
        ("TC-019", "Validar disponibilidad objetivo", "RNF-07", "Revisar despliegue y operacion documentada", "Disponibilidad objetivo del 90% registrada como criterio."),
        ("TC-020", "Validar rendimiento API con K6", "RNF-02", "Ejecutar escenarios de carga normal, pico y sostenida", "Pruebas K6 documentadas sin fallos criticos."),
    ]

    created_cases = []
    for index, (code, title, req_code, steps, expected) in enumerate(cases, start=1):
        technique = TestCase.Technique.USE_CASE if req_code.startswith("RF") else TestCase.Technique.EXPERIENCE
        test_case = upsert_test_case(plan, requirements[req_code], student, code, title, steps, expected, technique)
        created_cases.append(test_case)
        create_passed_execution(
            test_case,
            student,
            "APROBADO segun resultados documentados en pruebas unitarias, casos de uso o pruebas K6.",
            40 - index,
        )

    risks = [
        ("INC-001", "Dependencia de autenticacion externa", "La autenticacion depende de una API de terceros; una falla podria bloquear el acceso.", "Mantener pruebas de autenticacion y plan alterno de acceso.", Incident.Probability.MEDIUM, Incident.Impact.HIGH, "RNF-01"),
        ("INC-002", "Cambios de version en Strapi CMS", "Cambios en Strapi o plugins pueden afectar la integracion frontend-backend.", "Controlar versiones, probar endpoints criticos y documentar dependencias.", Incident.Probability.MEDIUM, Incident.Impact.MEDIUM, "RNF-04"),
        ("INC-003", "Limitaciones en gestion y visualizacion PDF", "El worker o visor de documentos puede afectar subida, vista o comparacion.", "Probar documentos PDF representativos y mantener compatibilidad del visor.", Incident.Probability.MEDIUM, Incident.Impact.MEDIUM, "RNF-02"),
        ("INC-004", "Disponibilidad de servicios desplegados", "Vercel, Railway o Supabase pueden presentar interrupciones.", "Monitorear disponibilidad y conservar estrategia de despliegue reproducible con Docker.", Incident.Probability.LOW, Incident.Impact.HIGH, "RNF-07"),
    ]
    for code, title, description, mitigation, probability, impact, req_code in risks:
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
                "status": Incident.Status.MITIGATED,
                "reported_by": student,
            },
        )

    phase_data = [
        (1, "Analisis de requisitos", "ERS IEEE 830 y requisitos RF/RNF registrados.", "Documento ERS disponible.", "Requisitos aprobados y versionados.", 100, TestingPhase.Status.DONE),
        (2, "Planificacion y riesgos", "Plan de pruebas, alcance, estrategia y riesgos derivados.", "Requisitos aprobados.", "Plan aprobado y riesgos mitigados.", 100, TestingPhase.Status.DONE),
        (3, "Diseno de pruebas", "Casos de prueba derivados de casos de uso y RNF.", "Plan aprobado.", "Casos trazados a requisitos.", 100, TestingPhase.Status.DONE),
        (4, "Preparacion del ambiente", "Entorno React, Strapi, Docker, Jest, K6 y Grafana documentado.", "Casos definidos.", "Ambiente documentado para ejecucion.", 100, TestingPhase.Status.DONE),
        (5, "Ejecucion y gestion de defectos", "Ejecuciones cargadas desde anexos de pruebas con resultado aprobado.", "Ambiente disponible.", "Ejecuciones validadas sin defectos criticos.", 100, TestingPhase.Status.DONE),
        (6, "Cierre e informes", "Resultados consolidados para cobertura, ejecucion, riesgos y trazabilidad.", "Ejecuciones finalizadas.", "Informe final disponible.", 100, TestingPhase.Status.DONE),
    ]
    now = timezone.now()
    for order, name, description, entry, exit_criteria, progress, status in phase_data:
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
                "completed_tasks": 4,
                "pending_tasks": 0,
                "started_at": now - timedelta(days=60 - order),
                "completed_at": now - timedelta(days=54 - order),
                "updated_by": student,
            },
        )

    Defect.objects.filter(project=project).delete()
    Report.objects.update_or_create(
        project=project,
        title="Resumen final documental - Proyecto Cristian Capa",
        report_type=Report.ReportType.FINAL,
        defaults={
            "generated_by": student,
            "content": {
                "source": "Cristian Ramiro_Capa Rodriguez.pdf",
                "requirements": len(requirements),
                "test_cases": len(created_cases),
                "executions": TestExecution.objects.filter(test_case__test_plan=plan).count(),
                "defects": 0,
                "risks": Incident.objects.filter(project=project).count(),
                "summary": "Carga adaptada al ciclo STLC/ISTQB con requisitos, plan, casos, ejecuciones aprobadas, riesgos, fases y trazabilidad.",
            },
        },
    )

    print("Proyecto cargado:", project.code, project.name)
    print("Usuario estudiante:", student.email)
    print("Tutor asignado:", tutor.email)
    print("Requisitos:", Requirement.objects.filter(project=project).count())
    print("Casos de prueba:", TestCase.objects.filter(test_plan=plan).count())
    print("Ejecuciones:", TestExecution.objects.filter(test_case__test_plan=plan).count())
    print("Riesgos/incidentes:", Incident.objects.filter(project=project).count())
    print("Defectos:", Defect.objects.filter(project=project).count())
    print("Fases:", TestingPhase.objects.filter(project=project).count())


if __name__ == "__main__":
    main()
