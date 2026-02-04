#!/usr/bin/env bash
set -euo pipefail

# Start script for Render: apply migrations, collect static files, then start Gunicorn.
# This is safe to run on boot and helpful if you prefer migrations at startup.

echo "[start.sh] Running database migrations..."
python manage.py migrate --noinput

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
