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

# shellcheck disable=SC1091
source "$PROJECT_DIR/scripts/lib/docker_postgres.sh"

: "${DATABASE_URL:?DATABASE_URL must be set in .env}"
: "${DB_NAME:?DB_NAME must be set in .env}"

BACKUP_DIR="${BACKUP_DIR:-$PROJECT_DIR/backups/database}"
RETENTION_DAYS="${RETENTION_DAYS:-${BACKUP_RETENTION_DAYS:-30}}"

require_postgres_container

mkdir -p "$BACKUP_DIR"

TIMESTAMP="$(date '+%Y-%m-%d_%H-%M-%S')"
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.dump"

# Written to a hidden temp file first, so a failed/interrupted pg_dump can
# never leave an empty or partially-written file at the final backup name.
TMP_FILE="$(mktemp "$BACKUP_DIR/.${DB_NAME}_${TIMESTAMP}.XXXXXX")"

cleanup() {
    rm -f "$TMP_FILE"
}
trap cleanup EXIT

echo "Starting backup of database '$DB_NAME' via container '$POSTGRES_CONTAINER_NAME'..."

docker exec "$POSTGRES_CONTAINER_NAME" pg_dump \
    --dbname="$DATABASE_URL" \
    --format=custom \
    --no-owner \
    --no-privileges \
    > "$TMP_FILE"

if [[ ! -s "$TMP_FILE" ]]; then
    echo "ERROR: Backup failed or created an empty file."
    exit 1
fi

mv "$TMP_FILE" "$BACKUP_FILE"

echo "Backup created:"
echo "$BACKUP_FILE"

# ==========================
# Verify created backup
# ==========================

VERIFY_SCRIPT="$PROJECT_DIR/scripts/verify_backup.sh"

echo
echo "Verifying backup..."

if [ ! -x "$VERIFY_SCRIPT" ]; then
    echo "ERROR: verify_backup.sh not found or not executable"
    exit 1
fi

if "$VERIFY_SCRIPT" "$BACKUP_FILE"; then
    echo "Backup verification passed"
else
    echo "Backup verification failed"
    exit 1
fi

# ==========================
# Remove old backups — only once a fresh backup has been verified, so a
# broken new backup can never cost us the last known-good ones.
# ==========================

find "$BACKUP_DIR" \
    -maxdepth 1 \
    -type f \
    -name "${DB_NAME}_*.dump" \
    -mtime "+$RETENTION_DAYS" \
    -delete

echo "Backups older than $RETENTION_DAYS days were removed."
