# ============================================================
# Root justfile — project task runner
# Install: brew install just
# Usage: just <command>
# ============================================================

import 'just/api.just'
import 'just/db.just'
import 'just/tests.just'

# Show all available commands
default:
    @just --list

# ============================================================
# Infrastructure
# ============================================================

# Start all local services (PostgreSQL, Redis, Kafka, MinIO)
infra-up:
    docker compose -f deploy/docker-compose.local.yml up -d
    @echo "Waiting for services to be healthy..."
    @sleep 5
    @just infra-status

# Stop all local services
infra-down:
    docker compose -f deploy/docker-compose.local.yml down

# Show service status
infra-status:
    docker compose -f deploy/docker-compose.local.yml ps

# ============================================================
# Development workflow
# ============================================================

# Full local setup: infra + migrations + api
dev: infra-up db-migrate api

# Run everything needed for a PR: lint + type check + tests
ci: lint mypy test

# Install / sync all dependencies (runtime + dev)
install:
    uv sync

# Add a new runtime dependency
# Usage: just add httpx
add pkg:
    uv add {{pkg}}

# Add a new dev-only dependency
# Usage: just add-dev pytest-benchmark
add-dev pkg:
    uv add --dev {{pkg}}

# ============================================================
# Deploy
# ============================================================

# Build production Docker image
docker-build:
    docker build -f deploy/Dockerfile -t app:latest .  # CHANGE: image name

# Start production stack
deploy-up:
    docker compose -f deploy/compose.yaml --env-file .env up -d

# Stop production stack
deploy-down:
    docker compose -f deploy/compose.yaml down

# View production logs
deploy-logs service="backend":
    docker compose -f deploy/compose.yaml logs -f {{service}}

# Run migrations on production
deploy-migrate:
    docker compose -f deploy/compose.yaml exec backend \
        alembic upgrade head
