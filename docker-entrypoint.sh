#!/bin/bash
set -e

echo "=== Running database migrations ==="
python manage.py migrate --noinput

echo "=== Collecting static files ==="
python manage.py collectstatic --noinput

echo "=== Pre-compressing static files (gzip) ==="
find /app/staticfiles -type f \( -name "*.css" -o -name "*.js" -o -name "*.svg" -o -name "*.html" -o -name "*.json" -o -name "*.xml" -o -name "*.txt" \) -exec gzip -9 -k -f {} \;

echo "=== Loading initial structure ==="
python manage.py loaddata blog/fixtures/initial_structure.json

if [ "${LOAD_DEMO_DATA}" = "true" ]; then
    echo "=== Loading demo content ==="
    python manage.py setup_demo_content
fi

echo "=== Creating superuser (if not exists) ==="
python manage.py createsuperuser --noinput 2>/dev/null || true

echo "=== Starting Gunicorn ==="
exec "$@"
