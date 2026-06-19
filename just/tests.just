# ============================================================
# Test commands
# ============================================================

# Run all tests
test:
    ENV=test \
    CONFIG_PATH=backend/shared/settings/config.test.yaml \
    uv run pytest backend/tests/ -v

# Run tests with coverage report
test-cov:
    ENV=test \
    CONFIG_PATH=backend/shared/settings/config.test.yaml \
    uv run pytest backend/tests/ -v \
    --cov=backend \
    --cov-report=term-missing \
    --cov-report=html:htmlcov

# Run only smoke tests (fast subset)
test-smoke:
    ENV=test \
    CONFIG_PATH=backend/shared/settings/config.test.yaml \
    uv run pytest backend/tests/ -v -m smoke

# Run tests in parallel (pytest-xdist)
test-parallel:
    ENV=test \
    CONFIG_PATH=backend/shared/settings/config.test.yaml \
    uv run pytest backend/tests/ -v -n auto

# Run specific test file
# Usage: just test-file backend/tests/example_domain/test_create_example.py
test-file file:
    ENV=test \
    CONFIG_PATH=backend/shared/settings/config.test.yaml \
    uv run pytest {{file}} -v

# ============================================================
# CI commands (DATABASE_URL must be set in environment)
# ============================================================

# Apply migrations in CI
ci-migrate:
    uv run alembic -c alembic.ini upgrade head

# Run tests with coverage in CI
ci-test:
    CONFIG_PATH=backend/shared/settings/config.test.yaml \
    uv run pytest backend/tests/ \
    --cov=backend \
    --cov-report=term-missing \
    --tb=short
