#!/usr/bin/env bash
set -euo pipefail

# Helper script to build and run the production docker-compose locally,
# wait for Postgres to be ready, run migrations, and show logs.

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
COMPOSE_FILE="$ROOT_DIR/deploy/docker-compose.prod.yml"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker not found. Please install Docker Desktop or docker engine and try again."
  exit 1
fi

echo "Building and starting containers..."
docker compose -f "$COMPOSE_FILE" up -d --build

# Wait for Postgres
echo "Waiting for Postgres to accept connections..."
RETRIES=30
until docker compose -f "$COMPOSE_FILE" exec -T db pg_isready -U "${POSTGRES_USER:-postgres}" >/dev/null 2>&1; do
  sleep 1
  RETRIES=$((RETRIES-1))
  if [ "$RETRIES" -le 0 ]; then
    echo "Postgres did not become ready in time. Check 'docker compose logs db' for errors."
    exit 1
  fi
done

# Run migrations inside the web container
echo "Running database migrations inside web container..."
docker compose -f "$COMPOSE_FILE" exec -T web .venv/bin/python -m flask db upgrade

# Tail logs
echo "Tailing web logs. Press Ctrl-C to exit."
docker compose -f "$COMPOSE_FILE" logs -f web
