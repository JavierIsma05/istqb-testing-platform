from django.core.management.base import BaseCommand
from django.db.models import Count, Q

from apps.users.models import User


class Command(BaseCommand):
    help = 'Genera una auditoría de usuarios por rol sin exponer contraseñas ni hashes.'

    def handle(self, *args, **options):
        users = User.objects.prefetch_related('projects', 'project_created').order_by(
            'role',
            'email',
        )
        totals = users.aggregate(
            admins=Count('id', filter=Q(role=User.Roles.ADMIN)),
            teachers=Count('id', filter=Q(role=User.Roles.TEACHER)),
            students=Count('id', filter=Q(role=User.Roles.STUDENT)),
        )

        self.stdout.write('AUDITORIA DE USUARIOS')
        self.stdout.write('====================')
        self.stdout.write(f"Administradores: {totals['admins']}")
        self.stdout.write(f"Docentes: {totals['teachers']}")
        self.stdout.write(f"Estudiantes: {totals['students']}")
        self.stdout.write('')

        for user in users:
            member_projects = list(user.projects.all())
            created_projects = list(user.project_created.all())
            project_names = sorted({project.name for project in member_projects + created_projects})
            tutor_names = sorted(
                {
                    member.get_full_name() or member.email
                    for project in member_projects + created_projects
                    for member in project.members.all()
                    if member.role == User.Roles.TEACHER
                }
            )

            self.stdout.write(f'Usuario: {user.email}')
            self.stdout.write(f'  Rol: {user.get_role_display()}')
            self.stdout.write(f'  Activo: {"Si" if user.is_active else "No"}')
            self.stdout.write(f'  Staff: {"Si" if user.is_staff else "No"}')
            self.stdout.write(f'  Ultimo acceso: {user.last_login or "Sin acceso registrado"}')
            self.stdout.write(f'  Proyecto asociado: {", ".join(project_names) if project_names else "Sin proyecto"}')
            self.stdout.write(f'  Tutor asociado: {", ".join(tutor_names) if tutor_names else "Sin tutor"}')
            self.stdout.write('')
