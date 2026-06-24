test:
    ENV=test \
    CONFIG_PATH=backend/shared/settings/config.test.yaml \
    uv run pytest backend/tests/ -v

test-cov:
    ENV=test \
    CONFIG_PATH=backend/shared/settings/config.test.yaml \
    uv run pytest backend/tests/ -v \
    --cov=backend \
    --cov-report=term-missing \
    --cov-report=html:htmlcov

test-smoke:
    ENV=test \
    CONFIG_PATH=backend/shared/settings/config.test.yaml \
    uv run pytest backend/tests/ -v -m smoke

test-parallel:
    ENV=test \
    CONFIG_PATH=backend/shared/settings/config.test.yaml \
    uv run pytest backend/tests/ -v -n auto

test-file file:
    ENV=test \
    CONFIG_PATH=backend/shared/settings/config.test.yaml \
    uv run pytest {{file}} -v

ci-migrate:
    uv run alembic upgrade head

ci-test:
    CONFIG_PATH=backend/shared/settings/config.test.yaml \
    uv run pytest backend/tests/ \
    --cov=backend \
    --cov-report=term-missing \
    --tb=short
