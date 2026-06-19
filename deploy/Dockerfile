# ============================================================
# Backend Dockerfile — uses uv for dependency management
# ============================================================

FROM python:3.12-slim AS builder

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# System deps for asyncpg, cryptography
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install dependencies using uv (respects uv.lock for reproducibility)
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev --no-install-project


FROM python:3.12-slim AS runner

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy uv and installed venv from builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/
COPY --from=builder /app/.venv /app/.venv

# Copy project source
COPY . .

# Use the venv from the build stage
ENV PATH="/app/.venv/bin:$PATH"

# RSA keys directory (mount as secret in production)
RUN mkdir -p /app/keys && \
    chmod +x deploy/docker/entrypoint.sh

# Run as non-root
RUN useradd -m -u 1000 appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

# entrypoint.sh runs "alembic upgrade head" before starting the server
ENTRYPOINT ["deploy/docker/entrypoint.sh"]
CMD ["uvicorn", "backend.app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4"]
