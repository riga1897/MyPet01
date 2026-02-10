#!/bin/bash
set -e

echo "=== Running database migrations ==="
python manage.py migrate --noinput

echo "=== Collecting static files ==="
python manage.py collectstatic --noinput

echo "=== Loading initial structure ==="
python manage.py loaddata blog/fixtures/initial_structure.json

if [ "${LOAD_DEMO_DATA}" = "true" ]; then
    echo "=== Copying demo media files ==="
    cp -rn blog/fixtures/demo_media/* media/ 2>/dev/null || true

    echo "=== Loading demo content ==="
    python manage.py loaddata blog/fixtures/demo_content.json
fi

echo "=== Creating superuser (if not exists) ==="
python manage.py createsuperuser --noinput 2>/dev/null || true

echo "=== Starting Gunicorn ==="
exec "$@"
