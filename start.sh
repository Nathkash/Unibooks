#!/usr/bin/env bash
set -euo pipefail

# Start script: ensure dependencies, apply migrations, collect static files, then start Gunicorn.
# This script is defensive so it fails with clear messages on missing env or deps.

PYTHON=${PYTHON:-python3}
PIP=${PIP:-pip3}

echo "[start.sh] Checking for Django..."
if ! $PYTHON -c "import django" >/dev/null 2>&1; then
	echo "[start.sh] Django not found. Installing requirements from requirements.txt..."
	if [ -f requirements.txt ]; then
		# Upgrade pip first to reduce wheel build issues, then install requirements.
		$PIP install --upgrade pip setuptools wheel
		$PIP install -r requirements.txt
	else
		echo "[start.sh] ERROR: requirements.txt not found, cannot install dependencies." >&2
		exit 1
	fi
else
	echo "[start.sh] Django is present."
fi

# Default to the production settings module unless another is provided.
export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-unibooks.settings_production}
echo "[start.sh] Using settings module: ${DJANGO_SETTINGS_MODULE}"

# If we're using production settings, require a SECRET_KEY to be set so we fail loudly
if [ "${DJANGO_SETTINGS_MODULE}" = "unibooks.settings_production" ]; then
	if [ -z "${DJANGO_SECRET_KEY:-}" ]; then
		echo "[start.sh] ERROR: DJANGO_SECRET_KEY must be set when using production settings." >&2
		exit 1
	fi
fi

echo "[start.sh] Running database migrations..."
$PYTHON manage.py migrate --noinput

echo "[start.sh] Collecting static files..."
$PYTHON manage.py collectstatic --noinput

# Respect the PORT environment variable provided by Railway or other PaaS.
PORT=${PORT:-8000}
echo "[start.sh] Starting Gunicorn on 0.0.0.0:${PORT}..."
exec gunicorn unibooks.wsgi --log-file - --workers 3 --threads 2 --bind 0.0.0.0:${PORT}
