#!/usr/bin/env bash
set -euo pipefail

# Start script: ensure dependencies, apply migrations, collect static files, then start Gunicorn.
# This script is defensive so it fails with clear messages on missing env or deps.

PYTHON=${PYTHON:-python3}

echo "[start.sh] Checking for Django..."
if ! $PYTHON -c "import django" >/dev/null 2>&1; then
	echo "[start.sh] Django not found. Installing requirements from requirements.txt..."
	if [ -f requirements.txt ]; then
		# Use python -m pip to ensure we call the pip corresponding to the chosen Python
		echo "[start.sh] Upgrading pip, setuptools and wheel using ${PYTHON} -m pip..."
		$PYTHON -m pip install --upgrade pip setuptools wheel
		echo "[start.sh] Installing requirements.txt using ${PYTHON} -m pip..."
		$PYTHON -m pip install -r requirements.txt
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
echo "[start.sh] Debug: raw DJANGO_ALLOWED_HOSTS env var: '${DJANGO_ALLOWED_HOSTS:-}'"
# Try to print the effective Django settings.ALLOWED_HOSTS if Django can be imported.
# Don't fail the script if this check can't run; it's purely diagnostic.
$PYTHON - <<'PY' || true
import os
print('[start.sh] Debug: attempting to import Django settings to show effective ALLOWED_HOSTS')
try:
	from django.conf import settings
	# Use repr() so we can spot stray quotes or whitespace in values
	print('[start.sh] Debug: settings.ALLOWED_HOSTS =', repr(getattr(settings, 'ALLOWED_HOSTS', None)))
except Exception as e:
	print('[start.sh] Debug: could not read Django settings.ALLOWED_HOSTS:', repr(e))
PY
echo "[start.sh] Starting Gunicorn on 0.0.0.0:${PORT} using ${PYTHON} -m gunicorn..."
# Use python -m gunicorn to ensure the gunicorn runner matches the active Python interpreter
exec $PYTHON -m gunicorn unibooks.wsgi --log-file - --workers 3 --threads 2 --bind 0.0.0.0:${PORT}
