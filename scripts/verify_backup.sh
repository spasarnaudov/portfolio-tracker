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

require_postgres_container

# The dump only exists on the host, so pg_restore (which runs inside the
# container — see docker_postgres.sh) needs its own copy of it first.
VERIFY_RESULT_FILE="$(mktemp)"
CONTAINER_DUMP="/tmp/verify_$(basename "$BACKUP_FILE")"

cleanup() {
    rm -f "$VERIFY_RESULT_FILE"
    docker exec "$POSTGRES_CONTAINER_NAME" rm -f "$CONTAINER_DUMP" &> /dev/null || true
}

trap cleanup EXIT


# Verify with pg_restore

echo
echo "Checking dump structure..."

docker cp "$BACKUP_FILE" "$POSTGRES_CONTAINER_NAME:$CONTAINER_DUMP"

if docker exec "$POSTGRES_CONTAINER_NAME" pg_restore --list "$CONTAINER_DUMP" > "$VERIFY_RESULT_FILE"; then
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
