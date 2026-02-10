#!/bin/bash
set -e

echo "=== Running database migrations ==="
python manage.py migrate --noinput

echo "=== Collecting static files ==="
python manage.py collectstatic --noinput

echo "=== Creating superuser (if not exists) ==="
python manage.py createsuperuser --noinput 2>/dev/null || true

echo "=== Starting Gunicorn ==="
exec "$@"
