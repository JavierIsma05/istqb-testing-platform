# Fase 8: CI/CD y despliegue de producción

Esta fase deja preparada la plataforma para validar cambios automáticamente y ejecutar Django detrás de Gunicorn con PostgreSQL persistente. Los secretos no deben almacenarse en Git; el repositorio contiene únicamente `.env.production.example`.

## 1. Preparar variables de producción

Copiar el ejemplo y sustituir todos los valores de ejemplo:

```bash
cp .env.production.example .env.production
chmod 600 .env.production
```

Las variables mínimas son:

| Variable | Propósito |
|---|---|
| `SECRET_KEY` | Clave secreta única y aleatoria de Django. No reutilizar la de desarrollo. |
| `DEBUG` | Debe permanecer en `False`. |
| `ALLOWED_HOSTS` | Hostnames que servirán la aplicación, separados por comas. |
| `CSRF_TRUSTED_ORIGINS` | Orígenes HTTPS autorizados para formularios protegidos por CSRF. |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD` | Credenciales de PostgreSQL. |
| `DB_HOST` y `DB_PORT` | En Compose deben ser `db` y `5432`. |
| `SECURE_SSL_REDIRECT` | Redirige HTTP a HTTPS cuando existe proxy TLS. |
| `SESSION_COOKIE_SECURE` y `CSRF_COOKIE_SECURE` | Impiden enviar cookies por HTTP. |
| `AUTOMATION_ALLOWED_HOSTS` | Dominios permitidos por el runner automatizado; mantener una lista explícita. |
| `GUNICORN_WORKERS`, `GUNICORN_THREADS`, `GUNICORN_TIMEOUT` | Ajustes del servidor WSGI. |

Generar una clave segura, por ejemplo:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

El valor de `ALLOWED_HOSTS` no debe incluir `*`. Si la aplicación se publica como `istqb.example.com`, usar `ALLOWED_HOSTS=istqb.example.com` y `CSRF_TRUSTED_ORIGINS=https://istqb.example.com`.

## 2. Arrancar la topología de producción

El archivo `docker-compose.production.yml` contiene dos servicios:

- `db`: PostgreSQL 16 Alpine, sin puerto publicado al host y con volumen `postgres_data`.
- `web`: imagen Django con Gunicorn, migraciones y `collectstatic` en el entrypoint, además de volúmenes separados para archivos estáticos y multimedia.

Ejecutar desde la raíz del repositorio:

```bash
docker compose --env-file .env.production \
  -f docker-compose.production.yml up -d --build
```

El uso de `--env-file` es importante porque Compose necesita ese archivo tanto para interpolar `${DB_NAME}` y `${WEB_PORT}` como para inyectar variables al contenedor. La aplicación queda en el puerto definido por `WEB_PORT` y escucha internamente en el puerto 8000.

Comprobar el estado:

```bash
docker compose --env-file .env.production \
  -f docker-compose.production.yml ps
curl http://127.0.0.1:8000/health/
docker compose --env-file .env.production \
  -f docker-compose.production.yml logs -f web
```

El endpoint de salud debe devolver `{"status":"ok"}`. La terminación TLS debe realizarse delante de Compose mediante un reverse proxy o un balanceador. Ese proxy debe reenviar `X-Forwarded-Proto: https` y publicar únicamente HTTPS.

## 3. Operación y recuperación

El entrypoint ejecuta `migrate --noinput`, `collectstatic --noinput` y después arranca Gunicorn. Las migraciones se aplican antes de aceptar tráfico. Los volúmenes `postgres_data`, `static_data` y `media_data` sobreviven a la recreación de contenedores.

Para detener sin eliminar datos:

```bash
docker compose --env-file .env.production \
  -f docker-compose.production.yml stop
```

Para actualizar una versión:

```bash
git pull origin main
docker compose --env-file .env.production \
  -f docker-compose.production.yml up -d --build
```

No usar `down -v` en producción salvo que se pretenda eliminar permanentemente la base de datos y los archivos persistentes.

Antes de una actualización importante, realizar un respaldo de PostgreSQL y de los archivos multimedia:

```bash
docker compose --env-file .env.production \
  -f docker-compose.production.yml exec -T db \
  pg_dump -U "$DB_USER" -d "$DB_NAME" > backup-$(date +%Y%m%d-%H%M%S).sql

docker run --rm \
  -v istqb-testing-platform_media_data:/data \
  -v "$PWD":/backup alpine \
  tar czf /backup/media-$(date +%Y%m%d-%H%M%S).tgz -C /data .
```

El comando de backup debe ejecutarse en un contexto donde las variables `DB_USER` y `DB_NAME` estén disponibles. Conservar los respaldos fuera del servidor y probar periódicamente la restauración.

## 4. CI en GitHub Actions

`.github/workflows/ci.yml` se ejecuta en pushes a `main` y Pull Requests hacia `main`. El workflow:

1. Levanta PostgreSQL 16 como servicio de CI.
2. Instala Python 3.12 y las dependencias.
3. Instala Chromium para Playwright.
4. Ejecuta `manage.py check`, migraciones y `pytest`.
5. Construye la imagen Docker después de aprobar las pruebas.

Los secretos de producción no deben ponerse en este workflow. Para un despliegue posterior, agregar un job separado protegido por un entorno de GitHub, con credenciales de registro y del servidor configuradas como secrets.

## 5. Recomendaciones antes de producción real

Configurar HTTPS, DNS, firewall, backups automáticos, rotación de secretos, monitoreo de logs y un procedimiento probado de rollback. El Compose incluido es una base inicial para un único host; para alta disponibilidad se necesitarían un balanceador, almacenamiento externo y una estrategia de despliegue escalable.
