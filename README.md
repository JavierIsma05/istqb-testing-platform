# Plataforma Web ISTQB Testing Lifecycle

Proyecto Django para gestionar el ciclo de vida de pruebas de software con enfoque ISTQB: proyectos, requisitos, planes, casos de prueba, ejecuciones, defectos, incidentes, trazabilidad, reportes, notificaciones, auditoria y fases.

---

## Stack tecnologico

- **Python** 3.12
- **Django** 6
- **PostgreSQL** 16 (produccion/desarrollo)
- **SQLite** 3 (testing local rapido)
- **Templates** Django + Bootstrap 5
- **Playwright** + Chromium (pruebas automatizadas)
- **Docker** + Docker Compose (despliegue contenerizado)

---

## Estructura del proyecto

```
D:\PYTHON\iSTQB_Testing_Platform\
├── .env                         # Variables de entorno (NO subir al repo)
├── .env.example                 # Plantilla para .env
├── docker-compose.yml            # Orquestacion Docker (PostgreSQL + Django)
├── docker/
│   └── Dockerfile               # Imagen Docker para Django
├── requirements/
│   ├── base.txt                 # Dependencias base
│   ├── dev.txt                  # Dependencias desarrollo
│   └── prod.txt                 # Dependencias produccion
├── src/
│   ├── manage.py                # Entry point de Django
│   ├── config/
│   │   └── settings/
│   │       ├── base.py          # Configuracion base (usa .env para BD)
│   │       ├── development.py   # Desarrollo (PostgreSQL)
│   │       ├── testing.py       # Testing (SQLite)
│   │       └── production.py    # Produccion
│   └── apps/                    # Modulos de la plataforma
│       ├── authentication/
│       ├── users/
│       ├── dashboard/
│       ├── projects/
│       ├── requirements/
│       ├── testplans/
│       ├── testcases/
│       ├── executions/
│       ├── defects/
│       ├── incidents/
│       ├── traceability/
│       ├── reports/
│       ├── notifications/
│       ├── audit/
│       ├── phases/
│       └── core/
├── static/                      # Archivos estaticos
├── media/                       # Archivos subidos por usuarios
└── templates/                   # Templates HTML
```

---

# MANUAL DE INSTALACION

## 1. Prerrequisitos

| Requisito | Version minima | Donde descargar |
|-----------|---------------|-----------------|
| Python | 3.12 | https://www.python.org/downloads/ |
| pip | 24.0 | Se instala con Python |
| Git | Cualquiera | https://git-scm.com/downloads/win |
| PostgreSQL (opcional) | 16 | https://www.postgresql.org/download/windows/ |
| Docker Desktop (opcional) | 4.x | https://www.docker.com/products/docker-desktop/ |

**Importante:** Al instalar Python marcar la opcion **"Add Python to PATH"**.

## 2. Clonar o abrir el proyecto

```bash
cd D:\PYTHON\iSTQB_Testing_Platform
```

## 3. Crear entorno virtual (venv)

```bash
python -m venv venv
```

## 4. Activar el entorno virtual

**PowerShell:**
```powershell
venv\Scripts\Activate.ps1
```
Si da error de permisos, ejecutar antes:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

**CMD:**
```cmd
venv\Scripts\activate.bat
```

**Git Bash:**
```bash
source venv/Scripts/activate
```

Verificas que se activo cuando aparece `(venv)` al inicio de la linea de comandos.

## 5. Instalar dependencias

```bash
pip install -r requirements\base.txt
```

Si vas a desarrollar:
```bash
pip install -r requirements\dev.txt
```

## 6. Instalar Playwright (para pruebas automatizadas)

```bash
python -m playwright install chromium
```

---

# MANUAL DE EJECUCION

## OPCION A: Ejecucion local con SQLite (Mas rapida, sin PostgreSQL)

SQLite no requiere instalacion de base de datos. Ideal para pruebas rapidas o cuando no tienes PostgreSQL instalado.

### Paso a paso:

```bash
# 1. Ir a la carpeta src
cd src

# 2. Ejecutar migraciones con configuracion de testing (SQLite)
python manage.py migrate --settings=config.settings.testing

# 3. Crear superusuario (admin)
python manage.py createsuperuser --settings=config.settings.testing

# 4. Iniciar servidor
python manage.py runserver --settings=config.settings.testing
```

### Acceder:
- Plataforma: http://127.0.0.1:8000
- Admin Django: http://127.0.0.1:8000/admin/

### Nota:
El archivo SQLite se crea como `src/test_db.sqlite3`. Para empezar de cero, solo borra ese archivo y ejecuta `migrate` de nuevo.

---

## OPCION B: Ejecucion local con PostgreSQL

Requiere tener PostgreSQL instalado y corriendo en tu maquina.

### Paso 1: Configurar el archivo .env

Asegurate de que `D:\PYTHON\iSTQB_Testing_Platform\.env` tenga tus credenciales:

```env
SECRET_KEY=django-insecure-istqb-platform-secret-key
DEBUG=True

DB_NAME=istqb_db
DB_USER=postgres
DB_PASSWORD=tu_contraseña_aqui
DB_HOST=localhost
DB_PORT=5432
```

### Paso 2: Crear la base de datos en PostgreSQL

**Opcion A - Usando psql (terminal):**
```bash
psql -U postgres -c "CREATE DATABASE istqb_db WITH ENCODING 'UTF8';"
```

**Opcion B - Usando pgAdmin:**
1. Abrir pgAdmin
2. Click derecho en "Databases" -> "Create" -> "Database..."
3. Nombre: `istqb_db`
4. Encoding: `UTF8`
5. Guardar

### Paso 3: Ejecutar la aplicacion

```bash
# 1. Ir a src
cd src

# 2. Ejecutar migraciones
python manage.py migrate

# 3. Crear superusuario
python manage.py createsuperuser

# 4. Iniciar servidor
python manage.py runserver
```

### Acceder:
- Plataforma: http://127.0.0.1:8000
- Admin Django: http://127.0.0.1:8000/admin/

### Para cambiar a SQLite temporalmente (sin tocar configuracion):

Si tienes problemas con PostgreSQL, puedes usar SQLite sin modificar archivos:

```bash
python manage.py migrate --settings=config.settings.testing
python manage.py runserver --settings=config.settings.testing
```

---

## OPCION C: Ejecucion con Docker (Contenerizada)

No requiere tener Python ni PostgreSQL instalados en tu maquina. Solo Docker Desktop.

### Paso 1: Instalar Docker Desktop

1. Descargar de https://www.docker.com/products/docker-desktop/
2. Ejecutar el instalador
3. **Reiniciar el computador**
4. Abrir Docker Desktop y esperar que inicie (el icono en la bandeja del sistema deja de girar)

### Paso 2: Configurar .env para Docker

El archivo `.env` debe coincidir con las credenciales que usa el contenedor de PostgreSQL:

```env
SECRET_KEY=django-insecure-istqb-platform-secret-key
DEBUG=True

DB_NAME=istqb_db
DB_USER=postgres
DB_PASSWORD=postgres    # Coincide con docker-compose.yml
DB_HOST=localhost        # Docker sobreescribe esto automaticamente a "db"
DB_PORT=5432
```

### Paso 3: Ejecutar

```bash
# Desde la raiz del proyecto
cd D:\PYTHON\iSTQB_Testing_Platform

# Construir y levantar los contenedores
docker compose up --build
```

La primera vez tarda varios minutos descargando imagenes e instalando dependencias.

### Paso 4: En otra terminal (mientras Docker corre)

Abrir una **nueva terminal PowerShell** y ejecutar:

```bash
cd D:\PYTHON\iSTQB_Testing_Platform
```

**Ejecutar migraciones:**
```bash
docker compose exec web python manage.py migrate
```

**Crear superusuario:**
```bash
docker compose exec -it web python manage.py createsuperuser
```

**Cargar datos de prueba (opcional):**
```bash
docker compose exec web python manage.py shell -c "
from apps.users.models import User
User.objects.create_superuser('admin@unl.edu.ec', 'Admin123!', role='ADMIN')
"
```

### Paso 5: Acceder a la plataforma

- **Plataforma:** http://localhost:8000
- **Admin Django:** http://localhost:8000/admin/

### Comandos utiles de Docker

| Comando | Descripcion |
|---------|-------------|
| `docker compose up --build` | Construir y levantar contenedores |
| `docker compose up` | Levantar sin reconstruir |
| `docker compose down` | Detener contenedores (conserva datos) |
| `docker compose down -v` | Detener y borrar datos de BD |
| `docker compose logs -f` | Ver logs en tiempo real |
| `docker compose exec web bash` | Entrar al contenedor web |
| `docker compose ps` | Ver estado de los contenedores |

---

## Resumen rapido de comandos

### Si usas SQLite (sin PostgreSQL):
```bash
cd D:\PYTHON\iSTQB_Testing_Platform
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements\base.txt
cd src
python manage.py migrate --settings=config.settings.testing
python manage.py createsuperuser --settings=config.settings.testing
python manage.py runserver --settings=config.settings.testing
```

### Si usas PostgreSQL local:
```bash
cd D:\PYTHON\iSTQB_Testing_Platform
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements\base.txt
cd src
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Si usas Docker:
```bash
cd D:\PYTHON\iSTQB_Testing_Platform
docker compose up --build
# En otra terminal:
docker compose exec web python manage.py migrate
docker compose exec -it web python manage.py createsuperuser
```

---

## Solucion de problemas comunes

### Error: `pip no se reconoce como un comando`
- Python no esta en PATH. Reinstalar Python marcando "Add Python to PATH".

### Error: `connection to server at "localhost" (127.0.0.1), port 5432 failed`
- PostgreSQL no esta corriendo. Iniciar el servicio desde Services.msc o usar SQLite.

### Error: `FATAL: password authentication failed for user "postgres"`
- La clave en `.env` no coincide con la clave de PostgreSQL. Corregir en `.env`.

### Error: `relation "users_user" does not exist`
- Faltan migraciones: `python manage.py migrate`

### Error: `docker: command not found`
- Docker Desktop no esta instalado o no esta abierto.

### Error: `failed to connect to the docker API`
- Docker Desktop no esta corriendo. Abrir Docker Desktop y esperar.

---

## Roles del sistema

| Rol | Descripcion |
|-----|-------------|
| **Administrador** | Administra usuarios, catalogos y configuracion global |
| **Docente** | Gestiona proyectos academicos, planes, casos y seguimiento |
| **Estudiante** | Ejecuta pruebas, registra evidencias, defectos e incidentes |

---

## Usuarios creados (datos poblados)

Para acceder rapidamente, estos usuarios ya existen en la base de datos poblada:

| Email | Clave | Rol | Proyecto |
|-------|-------|-----|----------|
| javier.aguilar@unl.edu.ec | Istqb2026.Temp! | Estudiante | PRJ-002 |
| cristian.capa@unl.edu.ec | Istqb2026.Temp! | Estudiante | PRJ-003 |
| juan.castillo@unl.edu.ec | Istqb2026.Temp! | Estudiante | PRJ-004 |
| dany.martinez@unl.edu.ec | Istqb2026.Temp! | Estudiante | PRJ-005 |
| bryan.ordonez@unl.edu.ec | Istqb2026.Temp! | Estudiante | PRJ-006 |
| jorge.poma@unl.edu.ec | Istqb2026.Temp! | Estudiante | PRJ-007 |
| edinson.quizphe@unl.edu.ec | Istqb2026.Temp! | Estudiante | PRJ-008 |
| wilman.chamba@unl.edu.ec | Istqb2026.Temp! | Docente | — |
| pablo.ordonez@unl.edu.ec | Istqb2026.Temp! | Docente | — |
| francisco@unl.edu.ec | Istqb2026.Temp! | Docente | — |
