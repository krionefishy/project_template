# Project Template

FastAPI backend template with Dishka DI, SQLAlchemy async, Kafka, Redis, S3.

## Quick Start

```bash
# 0. Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 1. Copy env and config
cp .env.example .env
cp backend/shared/settings/config.yaml.example backend/shared/settings/config.yaml

# 2. Install all dependencies (creates .venv automatically)
just install        # → uv sync

# 3. Generate RSA keys (for frontend password encryption)
just generate-keys

# 4. Start infrastructure (PostgreSQL, Redis, Kafka, MinIO)
just infra-up

# 5. Apply migrations
just db-migrate

# 6. Start API
just api
# → http://localhost:8000/api/docs
```

## Managing dependencies

```bash
just add httpx           # add runtime dep  → uv add httpx
just add-dev ruff        # add dev dep      → uv add --dev ruff
uv sync                  # install/update everything from uv.lock
uv lock --upgrade        # refresh uv.lock with latest versions
```

## Architecture

```
API Request
  → FastAPI Router (HTTP only)
  → UseCase.execute() (business logic + DB)
  → SQLAlchemy AsyncSession (no raw SQL)
  → Response

File Upload:
  → UseCase → DB(status=PENDING) → Kafka → Consumer → S3 → DB(status=DONE)
```

## Commands

```bash
just              # show all commands
just dev          # full dev setup (infra + migrations + api)
just test         # run tests
just test-cov     # tests with coverage
just lint         # ruff linting
just db-migrate   # apply Alembic migrations
just deploy-up    # production stack
```

## Adding a New Domain

See `.cursor/rules/06-new-domain-checklist.mdc` for the full checklist.

Quick summary:
1. Create `backend/app/<domain>/` with `db_models.py`, `domain.py`, `dto.py`, `api/routes.py`, `usecases/`
2. Import ORM models in `migrations/env.py`, run `just db-create-migration`
3. Create `shared/di/providers/<domain>.py`, add to `provider.py`
4. Add router to `app/api/router.py`
5. Add Builder methods in `tests/builder.py`

## Structure

```
project_template/
├── .cursor/rules/       # Cursor AI rules
├── just/                # Justfile recipes
├── backend/
│   ├── app/             # Domain modules (API + UseCase + Models)
│   │   ├── auth/        # JWT + RSA auth
│   │   └── example_domain/  # Example — rename/copy per domain
│   ├── shared/
│   │   ├── di/          # Dishka providers
│   │   ├── kafka_streams/   # Kafka producer/consumers
│   │   └── settings/    # YAML config
│   ├── storage/         # DB/Redis/S3 clients
│   ├── tests/           # pytest (Builder pattern, mocks)
│   └── migrations/      # Alembic
└── deploy/
    ├── docker-compose.yaml      # Production
    ├── docker-compose.local.yml # Local dev
    └── nginx/
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Web | FastAPI |
| DI | Dishka |
| ORM | SQLAlchemy 2.0 async |
| Migrations | Alembic |
| Messaging | Kafka (aiokafka) |
| Cache / Sessions | Redis |
| Object Storage | S3 (boto3) / MinIO |
| Auth | JWT + RSA |
| Tests | pytest-asyncio + Builder |
| Linting | ruff + mypy |
| Task Runner | just |
