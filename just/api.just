# ============================================================
# API / Application commands
# ============================================================

# Start API in development mode (hot reload)
api:
    CONFIG_PATH=backend/shared/settings/config.yaml \
    uv run uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

# Start API in production mode
api-prod:
    CONFIG_PATH=backend/shared/settings/config.prod.yaml \
    uv run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Generate RSA key pair for frontend password encryption
generate-keys:
    mkdir -p keys
    openssl genrsa -out keys/private.pem 2048
    openssl rsa -in keys/private.pem -pubout -out keys/public.pem
    @echo "RSA keys generated in keys/"

# Lint code
lint:
    uv run ruff check . --fix

# Format code
fmt:
    uv run ruff format .

# Type check
mypy:
    uv run mypy backend/ --ignore-missing-imports
