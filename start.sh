#!/usr/bin/env bash
set -euo pipefail

# Start script for Render: apply migrations, collect static files, then start Gunicorn.
# This is safe to run on boot and helpful if you prefer migrations at startup.

echo "[start.sh] Running database migrations..."
python manage.py migrate --noinput

echo "[start.sh] Collecting static files..."
python manage.py collectstatic --noinput

echo "[start.sh] Starting Gunicorn..."
exec gunicorn unibooks.wsgi --log-file - --workers 3 --threads 2
