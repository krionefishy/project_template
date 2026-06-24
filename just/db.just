db-migrate:
    uv run alembic upgrade head

db-rollback:
    uv run alembic downgrade -1

db-create-migration name:
    uv run alembic revision --autogenerate -m "{{name}}"

db-status:
    uv run alembic current

db-history:
    uv run alembic history --verbose

db-migrate-test:
    DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/app_test_db \
    uv run alembic upgrade head
