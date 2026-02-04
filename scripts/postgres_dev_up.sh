#!/usr/bin/env bash
set -euo pipefail

# Simple helper to start a local Postgres via docker-compose and run migrations
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "[postgres_dev_up] Starting Postgres (docker-compose)..."
docker compose up -d db

echo "[postgres_dev_up] Waiting for Postgres to become ready (pg_isready)..."
CONTAINER_ID="$(docker compose ps -q db)"
for i in {1..60}; do
  if docker exec "$CONTAINER_ID" pg_isready -U unibooks >/dev/null 2>&1; then
    echo "[postgres_dev_up] Postgres is ready"
    break
  fi
  echo "[postgres_dev_up] waiting... ($i)"
  sleep 1
done

export DATABASE_URL=postgres://unibooks:unibooks@127.0.0.1:5432/unibooks

echo "[postgres_dev_up] Running migrations..."
python manage.py migrate

echo "[postgres_dev_up] Collecting static files..."
python manage.py collectstatic --noinput

echo "[postgres_dev_up] Done. App ready to run (use: ./start.sh or python manage.py runserver)
" 
