#!/bin/sh
set -e

echo "Applying database migrations..."
alembic -c alembic.ini upgrade head
echo "Migrations applied."

exec "$@"
