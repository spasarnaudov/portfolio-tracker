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

usage() {
    echo "Usage:"
    echo "  $0 [-y] /path/to/backup.dump"
    echo
    echo "Example:"
    echo "  $0 backups/database/portfolio_tracker_YYYY-MM-DD_HH-MM-SS.dump"
    echo
    echo "  -y    Skip the confirmation prompt (for scripted/cron use)."
    echo
    echo "This replaces every table in the target database with the dump's"
    echo "schema and data. Run scripts/init_database.sh first only if you want"
    echo "an empty database in between — this script overwrites it either way."
}

ASSUME_YES=0
while getopts ":y" opt; do
    case "$opt" in
        y) ASSUME_YES=1 ;;
        *) usage; exit 1 ;;
    esac
done
shift $((OPTIND - 1))

if [[ $# -ne 1 ]]; then
    usage
    exit 1
fi

BACKUP_FILE="$1"

if [[ ! -f "$BACKUP_FILE" ]]; then
    echo "ERROR: Backup file does not exist: $BACKUP_FILE"
    exit 1
fi

if [[ ! -s "$BACKUP_FILE" ]]; then
    echo "ERROR: Backup file is empty: $BACKUP_FILE"
    exit 1
fi

echo "Target database: $DATABASE_URL"
echo "Backup file:      $BACKUP_FILE"
echo
echo "This will DROP and recreate every object in the target database,"
echo "replacing its current contents with the backup."

if [[ "$ASSUME_YES" -ne 1 ]]; then
    read -r -p "Continue? [y/N] " CONFIRM
    if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi

echo
echo "Restoring..."

pg_restore \
    --dbname="$DATABASE_URL" \
    --clean \
    --if-exists \
    --no-owner \
    --no-privileges \
    "$BACKUP_FILE"

echo
echo "Restore completed."
