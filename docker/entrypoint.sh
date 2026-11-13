#!/bin/sh
set -e

echo "Applying Alembic database migrations..."
cd /app/backend
python -m alembic upgrade head || echo "Migration warning: proceeding with startup..."

echo "Starting SentinelAI Backend on port 8000..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
