#!/usr/bin/env bash
set -euo pipefail

# Start script for Render: apply migrations, collect static files, then start Gunicorn.
# This is safe to run on boot and helpful if you prefer migrations at startup.

echo "[start.sh] Running database migrations..."
# Try running migrations with a retry loop. This handles cases where the
# database service is not immediately reachable (common on PaaS startups).
MAX_MIGRATE_ATTEMPTS=${DB_MIGRATE_ATTEMPTS:-12}
SLEEP_SECONDS=${DB_MIGRATE_SLEEP_SECONDS:-5}
attempt=0
# Print a short, safe DB host/port hint (no credentials) to help debug env vars.
echo "[start.sh] Inspecting DATABASE_URL..."
python - <<'PY' || true
import os
from urllib.parse import urlparse
u = os.getenv('DATABASE_URL')
if not u:
	print('DATABASE_URL: <not set>')
else:
	try:
		p = urlparse(u)
		print('DATABASE_URL host:', p.hostname, 'port:', p.port)
	except Exception as e:
		print('DATABASE_URL parse error:', e)
PY
until python manage.py migrate --noinput; do
	attempt=$((attempt+1))
	if [ "$attempt" -ge "$MAX_MIGRATE_ATTEMPTS" ]; then
		echo "[start.sh] ERROR: migrations failed after $attempt attempts. Exiting."
		# Print a short hint for platform logs to help debugging
		echo "[start.sh] HINT: check DATABASE_URL env var and that the Postgres service is available."
		exit 1
	fi
	echo "[start.sh] migrate failed (attempt $attempt/$MAX_MIGRATE_ATTEMPTS). Sleeping ${SLEEP_SECONDS}s before retry..."
	sleep $SLEEP_SECONDS
done

echo "[start.sh] Collecting static files..."
python manage.py collectstatic --noinput

# If DJANGO_SUPERUSER_USERNAME is set, ensure a superuser exists or update its password.
# Uses DJANGO_SUPERUSER_EMAIL (optional) and DJANGO_SUPERUSER_PASSWORD (required to create or update password).
if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ]; then
  echo "[start.sh] Ensuring superuser exists for ${DJANGO_SUPERUSER_USERNAME} (won't print passwords)..."
  # Run a small Django script that never fails (exits 0) to avoid breaking startup.
  python manage.py shell <<'PY' || true
import os, sys
from django.contrib.auth import get_user_model
User = get_user_model()
username = os.getenv('DJANGO_SUPUSER_USERNAME')
email = os.getenv('DJANGO_SUPUSER_EMAIL', 'admin@example.com')
password = os.getenv('DJANGO_SUPUSER_PASSWORD')
try:
	if not username:
		print('NO_USERNAME')
		sys.exit(0)
	u = User.objects.filter(username=username).first()
	if u:
		if password:
			u.set_password(password)
			u.save()
			print('SUPERUSER_UPDATED')
		else:
			print('SUPERUSER_EXISTS_NO_PW_CHANGE')
	else:
		if not password:
			print('NO_PASSWORD_PROVIDED_CANNOT_CREATE')
			sys.exit(0)
		User.objects.create_superuser(username, email, password)
		print('SUPERUSER_CREATED')
except Exception as e:
	# Print the error for logs but exit 0 so start doesn't fail.
	print('SUPERUSER_STEP_ERROR', str(e))
	sys.exit(0)
PY
fi

# Respect the PORT environment variable provided by Railway or other PaaS.
PORT=${PORT:-8000}
echo "[start.sh] Starting Gunicorn on 0.0.0.0:${PORT}..."
exec gunicorn unibooks.wsgi --log-file - --workers 3 --threads 2 --bind 0.0.0.0:${PORT}
