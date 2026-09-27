from datetime import date

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.defects.models import Defect
from apps.executions.models import TestExecution
from apps.incidents.models import Incident
from apps.phases.views import ensure_default_phases
from apps.projects.models import Project
from apps.requirements.models import Requirement
from apps.testcases.models import TestCase
from apps.testplans.models import TestPlan
from apps.traceability.models import TraceabilityLink
from apps.users.models import User


class Command(BaseCommand):
    help = 'Crea datos demo ISTQB vinculados a un usuario existente sin borrar información.'

    def add_arguments(self, parser):
        parser.add_argument('--email', required=True, help='Correo del usuario propietario de los datos demo.')
        parser.add_argument('--project-code', default='DEMO-ISTQB-001', help='Código único del proyecto demo.')

    @transaction.atomic
    def handle(self, *args, **options):
        email = options['email'].strip().lower()
        project_code = options['project_code'].strip().upper()
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            raise CommandError(
                f'No existe el usuario {email}. Créalo primero o verifica el correo; no se creó ningún dato.'
            )
        if not project_code:
            raise CommandError('El código del proyecto no puede estar vacío.')

        project, _ = Project.objects.update_or_create(
            code=project_code,
            defaults={
                'name': 'Proyecto demo - Plataforma académica',
                'description': 'Proyecto de demostración para revisar el flujo completo ISTQB.',
                'status': Project.Status.ACTIVE,
                'start_date': date.today(),
                'created_by': user,
                'tutor': user if user.is_teacher_role else None,
            },
        )
        project.members.add(user)

        req_login, _ = Requirement.objects.update_or_create(
            project=project,
            code='REQ-DEMO-001',
            defaults={
                'title': 'Inicio de sesión institucional',
                'description': 'El usuario debe poder iniciar sesión con su correo institucional y contraseña válida.',
                'acceptance_criteria': 'Con credenciales válidas se muestra el dashboard; con credenciales inválidas se muestra un error.',
                'requirement_type': Requirement.RequirementType.FUNCTIONAL,
                'priority': Requirement.Priority.HIGH,
                'status': Requirement.Status.APPROVED,
                'created_by': user,
            },
        )
        req_profile, _ = Requirement.objects.update_or_create(
            project=project,
            code='REQ-DEMO-002',
            defaults={
                'title': 'Edición del perfil de usuario',
                'description': 'El usuario debe poder actualizar sus nombres, biografía y foto de perfil.',
                'acceptance_criteria': 'Los datos se guardan y la foto aparece en el perfil y en el navbar.',
                'requirement_type': Requirement.RequirementType.FUNCTIONAL,
                'priority': Requirement.Priority.MEDIUM,
                'status': Requirement.Status.APPROVED,
                'created_by': user,
            },
        )

        plan, _ = TestPlan.objects.update_or_create(
            project=project,
            name='Plan demo de pruebas funcionales',
            defaults={
                'version': '1.0',
                'description': 'Plan mínimo para validar el flujo de acceso y perfil.',
                'objective': 'Comprobar los principales flujos funcionales de la plataforma.',
                'scope': 'Autenticación, dashboard y perfil.',
                'strategy': 'Pruebas funcionales manuales de caja negra.',
                'test_types': ['FUNCTIONAL', 'REGRESSION'],
                'entry_criteria': 'Requisitos aprobados y ambiente disponible.',
                'exit_criteria': 'Casos ejecutados y defectos registrados.',
                'status': TestPlan.Status.APPROVED,
                'created_by': user,
            },
        )

        case_login, _ = TestCase.objects.update_or_create(
            test_plan=plan,
            code='TC-DEMO-001',
            defaults={
                'requirement': req_login,
                'title': 'Inicio de sesión con credenciales válidas',
                'description': 'Validar el acceso de un usuario registrado.',
                'steps': '1. Abrir la pantalla de inicio de sesión.\n2. Escribir correo y contraseña válidos.\n3. Presionar Iniciar sesión.',
                'preconditions': 'El usuario existe y está activo.',
                'test_data': f'Correo: {user.email}',
                'expected_result': 'El sistema redirige al dashboard correspondiente al rol.',
                'priority': TestCase.Priority.HIGH,
                'status': TestCase.Status.PASSED,
                'created_by': user,
            },
        )
        case_profile, _ = TestCase.objects.update_or_create(
            test_plan=plan,
            code='TC-DEMO-002',
            defaults={
                'requirement': req_profile,
                'title': 'Editar datos y foto del perfil',
                'description': 'Validar que el usuario pueda actualizar sus datos personales.',
                'steps': '1. Abrir Perfil.\n2. Cambiar la biografía.\n3. Guardar cambios.\n4. Revisar el avatar del navbar.',
                'preconditions': 'El usuario inició sesión.',
                'test_data': 'Biografía: Usuario demo para pruebas ISTQB.',
                'expected_result': 'La información se guarda y la foto se refleja en el navbar.',
                'priority': TestCase.Priority.MEDIUM,
                'status': TestCase.Status.FAILED,
                'created_by': user,
            },
        )

        executed_at = timezone.now()
        execution_login, _ = TestExecution.objects.update_or_create(
            test_case=case_login,
            executed_by=user,
            execution_type=TestExecution.ExecutionType.NORMAL,
            defaults={
                'execution_mode': TestExecution.ExecutionMode.MANUAL,
                'executed_at': executed_at,
                'result': TestExecution.Result.PASSED,
                'actual_result': 'El usuario ingresó correctamente al dashboard.',
                'environment': 'Django local - navegador de escritorio',
                'notes': 'Ejecución demo aprobada.',
                'review_status': TestExecution.ReviewStatus.VALIDATED,
                'reviewed_by': user if user.is_teacher_role else None,
                'reviewed_at': executed_at if user.is_teacher_role else None,
                'review_notes': 'Flujo correcto. La evidencia funcional es suficiente.',
            },
        )
        execution_profile, _ = TestExecution.objects.update_or_create(
            test_case=case_profile,
            executed_by=user,
            execution_type=TestExecution.ExecutionType.NORMAL,
            defaults={
                'execution_mode': TestExecution.ExecutionMode.MANUAL,
                'executed_at': executed_at,
                'result': TestExecution.Result.FAILED,
                'actual_result': 'La foto se guardó en el perfil, pero se requiere revisar su reflejo en el navbar.',
                'environment': 'Django local - navegador de escritorio',
                'notes': 'Ejecución demo con observación pendiente.',
                'review_status': TestExecution.ReviewStatus.NEEDS_FIX,
                'reviewed_by': user if user.is_teacher_role else None,
                'reviewed_at': executed_at if user.is_teacher_role else None,
                'review_notes': 'Verificar caché del navegador y actualización del avatar superior.',
            },
        )

        defect, _ = Defect.objects.update_or_create(
            project=project,
            code='DEF-DEMO-001',
            defaults={
                'test_case': case_profile,
                'execution': execution_profile,
                'title': 'Avatar superior no se actualiza inmediatamente',
                'description': 'Después de cambiar la foto, el navbar puede conservar las iniciales hasta recargar la página.',
                'steps_to_reproduce': '1. Cambiar la foto en Perfil.\n2. Guardar.\n3. Revisar el avatar del navbar.',
                'severity': Defect.Severity.MEDIUM,
                'priority': Defect.Priority.MEDIUM,
                'status': Defect.Status.OPEN,
                'reported_by': user,
                'assigned_to': user if user.is_teacher_role else None,
            },
        )
        incident, _ = Incident.objects.update_or_create(
            project=project,
            code='INC-DEMO-001',
            defaults={
                'requirement': req_profile,
                'test_plan': plan,
                'title': 'Riesgo de inconsistencia visual del perfil',
                'description': 'La sesión puede mostrar datos antiguos si el navegador mantiene recursos en caché.',
                'mitigation_strategy': 'Renovar la caché de estáticos y probar en una ventana privada.',
                'contingency_plan': 'Mostrar siempre las iniciales si la imagen no está disponible.',
                'probability': Incident.Probability.MEDIUM,
                'impact': Incident.Impact.MEDIUM,
                'status': Incident.Status.OPEN,
                'reported_by': user,
                'owner': user,
                'review_date': date.today(),
            },
        )
        case_profile.covered_risks.add(incident)
        TraceabilityLink.objects.update_or_create(
            requirement=req_login,
            test_case=case_login,
            defaults={'rationale': 'El caso valida directamente el requisito de acceso.'},
        )
        TraceabilityLink.objects.update_or_create(
            requirement=req_profile,
            test_case=case_profile,
            defaults={'rationale': 'El caso cubre la edición y visualización del perfil.'},
        )
        ensure_default_phases(project)

        self.stdout.write(self.style.SUCCESS('Datos demo creados o actualizados correctamente.'))
        self.stdout.write(f'Usuario: {user.email}')
        self.stdout.write(f'Proyecto: {project.code} - {project.name}')
        self.stdout.write(f'Requisitos: {req_login.code}, {req_profile.code}')
        self.stdout.write(f'Plan: {plan.name}')
        self.stdout.write(f'Casos: {case_login.code}, {case_profile.code}')
        self.stdout.write(f'Ejecuciones: {execution_login.pk}, {execution_profile.pk}')
        self.stdout.write(f'Defecto: {defect.code}')
        self.stdout.write(f'Incidente/riesgo: {incident.code}')
        self.stdout.write('No se borraron datos existentes; puedes volver a ejecutar el comando sin duplicar estos registros.')
