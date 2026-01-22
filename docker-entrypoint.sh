#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
while ! pg_isready -h "${POSTGRES_HOST:-db}" -p "${POSTGRES_PORT:-5432}" -U "${POSTGRES_USER:-postgres}" > /dev/null 2>&1; do
    sleep 1
done
echo "PostgreSQL is ready!"

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

if [ "$CREATE_SUPERUSER" = "true" ]; then
    echo "Creating superuser..."
    python manage.py createsuperuser --noinput --username "${DJANGO_SUPERUSER_USERNAME:-admin}" --email "${DJANGO_SUPERUSER_EMAIL:-admin@example.com}" || true
fi

echo "Starting Gunicorn..."
exec gunicorn --bind 0.0.0.0:8000 --workers "${GUNICORN_WORKERS:-4}" --threads "${GUNICORN_THREADS:-2}" mypet_project.wsgi:application
