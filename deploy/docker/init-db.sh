#!/bin/bash
# PostgreSQL initialization script
# Runs automatically on first container start via docker-entrypoint-initdb.d
#
# CHANGE: add more users, schemas, or extensions as needed

set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Add pgcrypto or other extensions if needed
    -- CREATE EXTENSION IF NOT EXISTS pgcrypto;

    -- CHANGE: create a read-only user for reports / analytics
    -- CREATE USER app_reader WITH PASSWORD 'changeme';
    -- GRANT CONNECT ON DATABASE $POSTGRES_DB TO app_reader;
    -- GRANT USAGE ON SCHEMA public TO app_reader;
    -- ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO app_reader;

    \echo 'Database initialized'
EOSQL
