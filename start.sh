#!/usr/bin/env bash
set -euo pipefail

# Start script for Render: apply migrations, collect static files, then start Gunicorn.
# This is safe to run on boot and helpful if you prefer migrations at startup.

echo "[start.sh] Running database migrations..."
python manage.py migrate --noinput

echo "[start.sh] Collecting static files..."
python manage.py collectstatic --noinput

# Respect the PORT environment variable provided by Railway or other PaaS.
PORT=${PORT:-8000}
echo "[start.sh] Starting Gunicorn on 0.0.0.0:${PORT}..."
exec gunicorn unibooks.wsgi --log-file - --workers 3 --threads 2 --bind 0.0.0.0:${PORT}
