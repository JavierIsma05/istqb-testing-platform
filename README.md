# Plataforma Web ISTQB Testing Lifecycle

Proyecto Django para gestionar el ciclo de vida de pruebas de software con enfoque ISTQB: proyectos, requisitos, planes, casos de prueba, ejecuciones, defectos, incidentes, trazabilidad, reportes, notificaciones, auditoria y fases.

## Stack

- Python 3.12
- Django 6
- PostgreSQL
- Templates Django + Bootstrap
- Arquitectura modular por apps

## Estructura

```text
src/
  apps/
    authentication/
    users/
    dashboard/
    projects/
    requirements/
    testplans/
    testcases/
    executions/
    defects/
    incidents/
    traceability/
    reports/
    notifications/
    audit/
    phases/
    core/
  config/
  templates/
  static/
  media/
  docs/
```

## Arranque local

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements/base.txt
cd src
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## PostgreSQL con Docker

```powershell
docker compose up --build
```

La configuracion se toma desde `.env`. Usa `.env.example` como plantilla y no subas credenciales reales al repositorio.

Si usas PostgreSQL instalado localmente en Windows, crea primero la base definida en `.env`:

```sql
CREATE DATABASE istqb_db WITH ENCODING 'UTF8';
```

Luego ejecuta:

```powershell
cd src
python manage.py migrate
python manage.py runserver
```

Para trabajar temporalmente sin PostgreSQL puedes usar el entorno de testing:

```powershell
cd src
python manage.py migrate --settings=config.settings.testing
python manage.py runserver --settings=config.settings.testing
```

## Roles iniciales

- Administrador: administra usuarios, catalogos y configuracion.
- Docente: gestiona proyectos academicos, planes, casos y seguimiento.
- Estudiante: ejecuta pruebas, registra evidencias, defectos e incidentes.

## Siguiente incremento

El siguiente paso recomendado es implementar formularios CRUD por modulo, permisos por rol y validaciones no funcionales de seguridad, mantenibilidad, auditoria y rendimiento.
