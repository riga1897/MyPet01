#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
while ! pg_isready -h "${PGHOST:-db}" -p "${PGPORT:-5432}" -U "${PGUSER:-postgres}" > /dev/null 2>&1; do
    sleep 1
done
echo "PostgreSQL is ready!"

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn..."
exec gunicorn --bind 0.0.0.0:8000 --workers 4 --threads 2 mypet_project.wsgi:application
