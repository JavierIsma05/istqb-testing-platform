#!/usr/bin/env sh
set -eu

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec gunicorn config.wsgi:application \
  --bind "${GUNICORN_BIND:-0.0.0.0:8000}" \
  --workers "${GUNICORN_WORKERS:-3}" \
  --threads "${GUNICORN_THREADS:-2}" \
  --timeout "${GUNICORN_TIMEOUT:-120}" \
  --access-logfile - \
  --error-logfile -
