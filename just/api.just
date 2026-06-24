api:
    uv run uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

api-prod:
    CONFIG_PATH=backend/shared/settings/config.prod.yaml \
    uv run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers 4

generate-keys:
    mkdir -p keys
    openssl genrsa -out keys/private.pem 2048
    openssl rsa -in keys/private.pem -pubout -out keys/public.pem
    @echo "RSA keys generated in keys/"

lint:
    uv run ruff check . --fix

fmt:
    uv run ruff format .

mypy:
    uv run mypy backend/ --ignore-missing-imports
