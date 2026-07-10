#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ENV_FILE:-$PROJECT_DIR/apps/flask/.env}"

if [[ -f "$ENV_FILE" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +a
fi

CONTAINER_NAME="${CONTAINER_NAME:-${DB_CONTAINER_NAME:-postgresql}}"
CONTAINER_DUMP_FILE="/tmp/verify_backup_$$.dump"
VERIFY_RESULT_FILE="$(mktemp)"

cleanup() {
    docker exec "$CONTAINER_NAME" rm -f "$CONTAINER_DUMP_FILE" >/dev/null 2>&1 || true
    rm -f "$VERIFY_RESULT_FILE"
}

trap cleanup EXIT

# Check argument
if [ $# -ne 1 ]; then
    echo "Usage:"
    echo "./scripts/verify_backup.sh backups/file.dump"
    exit 1
fi

BACKUP_FILE="$1"

echo "Checking backup:"
echo "$BACKUP_FILE"
echo

# Check file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file does not exist"
    exit 1
fi

# Check file size
if [ ! -s "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file is empty"
    exit 1
fi

SIZE=$(du -h "$BACKUP_FILE" | cut -f1)

echo "File exists"
echo "Size: $SIZE"


# Copy dump into PostgreSQL container

echo
echo "Copying backup to PostgreSQL container..."

docker cp \
    "$BACKUP_FILE" \
    "$CONTAINER_NAME:$CONTAINER_DUMP_FILE"


# Verify with pg_restore

echo
echo "Checking dump structure..."

if docker exec "$CONTAINER_NAME" pg_restore --list "$CONTAINER_DUMP_FILE" > "$VERIFY_RESULT_FILE"; then
    echo "Dump is valid"
else
    echo "ERROR: pg_restore failed"
    exit 1
fi


# Show first objects

echo
echo "Objects found:"
echo "----------------"

head -20 "$VERIFY_RESULT_FILE"


echo
echo "Backup verification completed successfully"
