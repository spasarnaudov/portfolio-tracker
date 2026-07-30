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
APP_PID_FILE="$PROJECT_DIR/runtime/app.pid"
START_APP_SCRIPT="$PROJECT_DIR/scripts/start_app.sh"

require_postgres_container

ensure_app_server_running() {
    if [[ -f "$APP_PID_FILE" ]] && kill -0 "$(cat "$APP_PID_FILE")" 2>/dev/null; then
        echo "App server is already running (PID $(cat "$APP_PID_FILE"))."
        return 0
    fi

    echo "App server is not running."

    if [[ -t 0 ]]; then
        read -r -p "Start it now? [Y/n] " START_REPLY
        case "${START_REPLY:-Y}" in
            [Yy]|[Yy][Ee][Ss]|"")
                ;;
            *)
                echo "Skipping app startup."
                echo "You can start it later with:"
                echo "  ./scripts/start_app.sh"
                return 0
                ;;
        esac
    else
        echo "No interactive terminal detected; starting it automatically."
    fi

    if [[ ! -x "$START_APP_SCRIPT" ]]; then
        echo "ERROR: $START_APP_SCRIPT is not available or not executable."
        echo "Start it manually later with:"
        echo "  ./scripts/start_app.sh"
        return 1
    fi

    if "$START_APP_SCRIPT"; then
        echo "App server started successfully."
        return 0
    fi

    echo "App server could not be started automatically."
    echo "Start it manually later with:"
    echo "  ./scripts/start_app.sh"
    return 1
}

ensure_app_server_running || true

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

VERIFY_SCRIPT="$PROJECT_DIR/scripts/database/verify_backup.sh"

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
