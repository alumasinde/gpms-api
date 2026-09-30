#!/usr/bin/env bash
set -euo pipefail

export SECRET_KEY="${SECRET_KEY:-phase1-verification-secret}"
export PLATFORM_DATABASE_URL="${PLATFORM_DATABASE_URL:-mysql+aiomysql://gatepass:gatepass@localhost:3306/gatepass_platform}"
export REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"
export CORS_ORIGINS="${CORS_ORIGINS:-[\"http://localhost:3000\",\"http://localhost:5173\"]}"

python -m compileall -q app alembic tests
alembic upgrade head --sql >/tmp/gatepass-phase1-migration.sql
pytest -q tests/unit

echo "Source compilation: OK"
echo "Alembic MySQL offline SQL generation: OK"
echo "Unit tests: OK"
echo "For live database verification: RUN_DB_TESTS=1 pytest -q"
