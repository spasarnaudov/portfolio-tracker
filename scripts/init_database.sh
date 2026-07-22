#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$PROJECT_DIR/.env"

if [[ -f "$ENV_FILE" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +a
fi

: "${DATABASE_URL:?DATABASE_URL must be set in .env}"

# shellcheck disable=SC1091
source "$PROJECT_DIR/scripts/lib/docker_postgres.sh"

SCHEMA_FILE="$PROJECT_DIR/database/postgresql/schema/001_init_schema.sql"
SEED_FILE="$PROJECT_DIR/database/postgresql/seed/001_seed_basic_data.sql"

echo "Initializing database from:"
echo "  $SCHEMA_FILE"
echo "  $SEED_FILE"
echo

require_postgres_container

EXISTING_TABLE_COUNT="$(docker exec "$POSTGRES_CONTAINER_NAME" psql "$DATABASE_URL" --tuples-only --no-align --command \
    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")"

if [[ "$EXISTING_TABLE_COUNT" -ne 0 ]]; then
    echo "ERROR: The database already has $EXISTING_TABLE_COUNT table(s) in the public schema."
    echo "init_database.sh only runs against an empty database, to avoid clobbering existing data."
    echo "To restore an existing backup instead, use scripts/restore_database.sh."
    exit 1
fi

echo "Applying schema..."
docker exec -i "$POSTGRES_CONTAINER_NAME" psql "$DATABASE_URL" --set ON_ERROR_STOP=1 < "$SCHEMA_FILE"

echo "Applying seed data..."
docker exec -i "$POSTGRES_CONTAINER_NAME" psql "$DATABASE_URL" --set ON_ERROR_STOP=1 < "$SEED_FILE"

echo
echo "Database initialized."
