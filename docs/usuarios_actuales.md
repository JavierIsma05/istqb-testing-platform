# Usuarios actuales de la aplicacion

Auditoria generada desde la base de datos de desarrollo.

## Resumen

- Total de usuarios: 6
- Administradores por rol: 0
- Docentes: 3
- Estudiantes: 3

Nota sobre claves: Django no guarda las contrasenas en texto plano, solo hashes. Por eso no es posible listar la clave real de cada usuario desde la base de datos. Si se necesita acceso, se debe restablecer una nueva clave comun con `python manage.py changepassword correo@dominio.com` o mediante un script administrativo.

## Listado

| Usuario | Rol | Activo | Staff | Ultimo acceso | Proyecto asociado | Tutor asociado | Clave |
| --- | --- | --- | --- | --- | --- | --- | --- |
| admin@example.com | Estudiante | Si | Si | Sin acceso registrado | Sin proyecto | Sin tutor | No recuperable en texto plano |
| javier.aguilar@unl.edu.ec | Estudiante | Si | Si | 2026-07-16 16:01:43 UTC | Plataforma Web para la Gestion del Ciclo de Vida de Pruebas basada en ISTQB | Francisco Alvarez | No recuperable en texto plano |
| qa@example.com | Estudiante | Si | No | 2026-06-17 20:31:33 UTC | E2E ISTQB Portal Academico 20260615-082955 | QA Tester | No recuperable en texto plano |
| demo.teacher@example.com | Docente | Si | No | 2026-06-05 17:17:39 UTC | Sin proyecto | Sin tutor | No recuperable en texto plano |
| francisco@unl.edu.ec | Docente | Si | No | 2026-07-16 14:03:02 UTC | Plataforma Web para la Gestion del Ciclo de Vida de Pruebas basada en ISTQB | Francisco Alvarez | No recuperable en texto plano |
| project.qa@example.com | Docente | Si | No | 2026-06-15 13:45:44 UTC | E2E ISTQB Portal Academico 20260615-082955 | QA Tester | No recuperable en texto plano |

## Observacion

Aunque aparecen `admin@example.com` y `javier.aguilar@unl.edu.ec` como usuarios `Staff`, su rol registrado es `Estudiante`, por eso el conteo de administradores por rol es 0.
