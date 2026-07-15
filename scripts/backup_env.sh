#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_ENV="${APP_ENV:-development}"
DEFAULT_ENV_FILE="$PROJECT_DIR/.env.$APP_ENV"
ENV_FILE="${ENV_FILE:-$DEFAULT_ENV_FILE}"

if [[ -f "$ENV_FILE" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +a
fi

ENV_BACKUP_DIR="${ENV_BACKUP_DIR:-$PROJECT_DIR/backups/env}"
RETENTION_DAYS="${ENV_BACKUP_RETENTION_DAYS:-${BACKUP_RETENTION_DAYS:-30}}"

TIMESTAMP="$(date '+%Y-%m-%d_%H-%M-%S')"
BACKUP_FILE="$ENV_BACKUP_DIR/env_${TIMESTAMP}.backup"

if [[ ! -f "$ENV_FILE" ]]; then
    echo "ERROR: Env file does not exist:"
    echo "$ENV_FILE"
    exit 1
fi

if [[ ! -s "$ENV_FILE" ]]; then
    echo "ERROR: Env file is empty:"
    echo "$ENV_FILE"
    exit 1
fi

mkdir -p "$ENV_BACKUP_DIR"

echo "Starting env backup..."
echo "Source:"
echo "$ENV_FILE"

install -m 600 "$ENV_FILE" "$BACKUP_FILE"

if [[ ! -s "$BACKUP_FILE" ]]; then
    echo "Env backup failed or created an empty file."
    rm -f "$BACKUP_FILE"
    exit 1
fi

echo "Env backup created:"
echo "$BACKUP_FILE"

find "$ENV_BACKUP_DIR" \
    -maxdepth 1 \
    -type f \
    -name "env_*.backup" \
    -mtime "+$RETENTION_DAYS" \
    -delete

echo "Env backups older than $RETENTION_DAYS days were removed."
