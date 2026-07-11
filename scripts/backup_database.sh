#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_ENV="${APP_ENV:-development}"
DEFAULT_ENV_FILE="$PROJECT_DIR/.env.$APP_ENV"
LEGACY_ENV_FILE="$PROJECT_DIR/apps/flask/.env"
ENV_FILE="${ENV_FILE:-$DEFAULT_ENV_FILE}"

if [[ ! -f "$ENV_FILE" && "$ENV_FILE" == "$DEFAULT_ENV_FILE" && -f "$LEGACY_ENV_FILE" ]]; then
    ENV_FILE="$LEGACY_ENV_FILE"
fi

if [[ -f "$ENV_FILE" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +a
fi

CONTAINER_NAME="${CONTAINER_NAME:-${DB_CONTAINER_NAME:-postgresql}}"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_DIR/backups/database}"
RETENTION_DAYS="${RETENTION_DAYS:-${BACKUP_RETENTION_DAYS:-30}}"

: "${DB_NAME:?DB_NAME must be set in the active env file}"
: "${DB_USER:?DB_USER must be set in the active env file}"

TIMESTAMP="$(date '+%Y-%m-%d_%H-%M-%S')"
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.dump"

mkdir -p "$BACKUP_DIR"

echo "Starting backup of database '$DB_NAME'..."

docker exec "$CONTAINER_NAME" \
    pg_dump \
    --username="$DB_USER" \
    --dbname="$DB_NAME" \
    --format=custom \
    --no-owner \
    --no-privileges \
    > "$BACKUP_FILE"

if [[ ! -s "$BACKUP_FILE" ]]; then
    echo "Backup failed or created an empty file."
    rm -f "$BACKUP_FILE"
    exit 1
fi

echo "Backup created:"
echo "$BACKUP_FILE"

find "$BACKUP_DIR" \
    -maxdepth 1 \
    -type f \
    -name "${DB_NAME}_*.dump" \
    -mtime "+$RETENTION_DAYS" \
    -delete

echo "Backups older than $RETENTION_DAYS days were removed."

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
