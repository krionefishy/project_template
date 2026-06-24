import 'just/api.just'
import 'just/db.just'
import 'just/tests.just'

default:
    @just --list

infra-up:
    docker compose -f deploy/docker-compose.local.yml up -d
    @echo "Waiting for services to be healthy..."
    @sleep 5
    @just infra-status

infra-down:
    docker compose -f deploy/docker-compose.local.yml down

infra-status:
    docker compose -f deploy/docker-compose.local.yml ps

dev: infra-up db-migrate api

ci: lint mypy test

install:
    uv sync

add pkg:
    uv add {{pkg}}

add-dev pkg:
    uv add --dev {{pkg}}

docker-build image_tag="local":
    docker build -f deploy/Dockerfile -t app:{{image_tag}} .

deploy-up:
    docker compose -f deploy/compose.yaml --env-file .env up -d

deploy-down:
    docker compose -f deploy/compose.yaml down

deploy-logs service="backend":
    docker compose -f deploy/compose.yaml logs -f {{service}}

deploy-migrate:
    docker compose -f deploy/compose.yaml exec backend \
        alembic upgrade head
