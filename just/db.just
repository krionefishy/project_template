# ============================================================
# Database commands (Alembic migrations)
# ============================================================

# Apply all pending migrations
db-migrate:
    uv run alembic -c alembic.ini upgrade head

# Rollback last migration
db-rollback:
    uv run alembic -c alembic.ini downgrade -1

# Create a new migration (auto-detect from ORM changes)
# Usage: just db-create-migration "add users table"
db-create-migration name:
    uv run alembic -c alembic.ini revision --autogenerate -m "{{name}}"

# Show current migration state
db-status:
    uv run alembic -c alembic.ini current

# Show migration history
db-history:
    uv run alembic -c alembic.ini history --verbose

# Apply migrations to test DB
db-migrate-test:
    DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/app_test_db \
    uv run alembic -c alembic.ini upgrade head
