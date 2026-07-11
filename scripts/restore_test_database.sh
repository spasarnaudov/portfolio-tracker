#!/usr/bin/env bash

set -Eeuo pipefail

CONTAINER_NAME="postgresql"
DB_USER="casaos"
TARGET_DB="portfolio_tracker_test"

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="$PROJECT_DIR/backups/database"

# Определя дали Docker е достъпен директно или чрез sudo.
if docker info >/dev/null 2>&1; then
    DOCKER_CMD=(docker)
elif sudo -n docker info >/dev/null 2>&1; then
    DOCKER_CMD=(sudo docker)
else
    echo "ERROR: Docker is not accessible."
    echo
    echo "Try running the script with sudo:"
    echo "  sudo $0 /path/to/backup.dump"
    echo
    echo "Or give the current user Docker access and log in again:"
    echo "  sudo usermod -aG docker \"\$USER\""
    exit 1
fi

usage() {
    echo "Usage:"
    echo "  $0 /path/to/backup.dump"
    echo
    echo "Example:"
    echo "  $0 \"$BACKUP_DIR/portfolio_tracker_YYYY-MM-DD_HH-MM-SS.dump\""
}

cleanup() {
    "${DOCKER_CMD[@]}" exec "$CONTAINER_NAME" \
        rm -f "$CONTAINER_DUMP" >/dev/null 2>&1 || true
}

if [[ $# -ne 1 ]]; then
    usage
    exit 1
fi

if ! BACKUP_FILE="$(realpath "$1" 2>/dev/null)"; then
    echo "ERROR: Cannot resolve the supplied backup path."
    exit 1
fi

CONTAINER_DUMP="/tmp/${TARGET_DB}_restore.dump"

echo "========================================"
echo "Portfolio Tracker test restore"
echo "========================================"
echo "Source dump: $BACKUP_FILE"
echo "Target DB:   $TARGET_DB"
echo

# 1. Проверка на dump файла
if [[ ! -f "$BACKUP_FILE" ]]; then
    echo "ERROR: Dump file does not exist."
    exit 1
fi

if [[ ! -s "$BACKUP_FILE" ]]; then
    echo "ERROR: Dump file is empty."
    exit 1
fi

FILE_SIZE="$(du -h "$BACKUP_FILE" | cut -f1)"

echo "Dump file exists."
echo "Dump size: $FILE_SIZE"
echo

# 2. Проверка на PostgreSQL контейнера
echo "1. Checking Docker container..."

if ! "${DOCKER_CMD[@]}" inspect "$CONTAINER_NAME" >/dev/null 2>&1; then
    echo "ERROR: Docker container '$CONTAINER_NAME' was not found."
    exit 1
fi

CONTAINER_RUNNING="$(
    "${DOCKER_CMD[@]}" inspect \
        --format '{{.State.Running}}' \
        "$CONTAINER_NAME"
)"

if [[ "$CONTAINER_RUNNING" != "true" ]]; then
    echo "ERROR: Docker container '$CONTAINER_NAME' is not running."
    exit 1
fi

echo "Docker container is running."
echo

# 3. Копиране и проверка на dump файла
echo "2. Copying dump into the container..."

"${DOCKER_CMD[@]}" cp \
    "$BACKUP_FILE" \
    "$CONTAINER_NAME:$CONTAINER_DUMP"

trap cleanup EXIT

echo "Dump copied successfully."
echo

echo "3. Checking dump structure..."

if ! "${DOCKER_CMD[@]}" exec "$CONTAINER_NAME" \
    pg_restore \
    --list \
    "$CONTAINER_DUMP" >/dev/null; then

    echo "ERROR: The dump is not a valid PostgreSQL custom-format archive."
    exit 1
fi

echo "Dump structure is valid."
echo

# 4. Потвърждение
echo "WARNING:"
echo "The database '$TARGET_DB' will be deleted and recreated."
echo "The production database 'portfolio_tracker' will not be modified."
echo

read -r -p "Continue? Type YES: " CONFIRMATION

if [[ "$CONFIRMATION" != "YES" ]]; then
    echo "Restore cancelled."
    exit 0
fi

echo

# 5. Прекратяване на активните връзки
echo "4. Terminating active database connections..."

"${DOCKER_CMD[@]}" exec "$CONTAINER_NAME" \
    psql \
    --username="$DB_USER" \
    --dbname=postgres \
    --set=ON_ERROR_STOP=1 \
    --command="
        SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE datname = '$TARGET_DB'
          AND pid <> pg_backend_pid();
    " >/dev/null

echo "Active connections terminated."
echo

# 6. Пресъздаване на тестовата база
echo "5. Recreating test database..."

"${DOCKER_CMD[@]}" exec "$CONTAINER_NAME" \
    dropdb \
    --username="$DB_USER" \
    --if-exists \
    "$TARGET_DB"

"${DOCKER_CMD[@]}" exec "$CONTAINER_NAME" \
    createdb \
    --username="$DB_USER" \
    "$TARGET_DB"

echo "Database recreated."
echo

# 7. Restore
echo "6. Restoring dump..."

"${DOCKER_CMD[@]}" exec "$CONTAINER_NAME" \
    pg_restore \
    --username="$DB_USER" \
    --dbname="$TARGET_DB" \
    --no-owner \
    --no-privileges \
    --exit-on-error \
    "$CONTAINER_DUMP"

echo "Restore completed."
echo

# 8. Проверка на възстановените таблици
echo "7. Checking restored tables..."

TABLE_COUNT="$(
    "${DOCKER_CMD[@]}" exec "$CONTAINER_NAME" \
        psql \
        --username="$DB_USER" \
        --dbname="$TARGET_DB" \
        --tuples-only \
        --no-align \
        --set=ON_ERROR_STOP=1 \
        --command="
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_type = 'BASE TABLE';
        "
)"

TABLE_COUNT="$(echo "$TABLE_COUNT" | tr -d '[:space:]')"

if [[ ! "$TABLE_COUNT" =~ ^[0-9]+$ ]]; then
    echo "ERROR: Could not determine the number of restored tables."
    exit 1
fi

if (( TABLE_COUNT == 0 )); then
    echo "ERROR: Restore completed, but no public tables were found."
    exit 1
fi

echo "Restored public tables: $TABLE_COUNT"
echo

"${DOCKER_CMD[@]}" exec "$CONTAINER_NAME" \
    psql \
    --username="$DB_USER" \
    --dbname="$TARGET_DB" \
    --command="\dt"

echo
echo "8. Checking important table row counts..."

TABLES=(
    "asset_categories"
    "assets"
    "asset_prices"
    "users"
)

for TABLE in "${TABLES[@]}"; do
    TABLE_EXISTS="$(
        "${DOCKER_CMD[@]}" exec "$CONTAINER_NAME" \
            psql \
            --username="$DB_USER" \
            --dbname="$TARGET_DB" \
            --tuples-only \
            --no-align \
            --set=ON_ERROR_STOP=1 \
            --command="
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                      AND table_name = '$TABLE'
                );
            "
    )"

    TABLE_EXISTS="$(echo "$TABLE_EXISTS" | tr -d '[:space:]')"

    if [[ "$TABLE_EXISTS" == "t" ]]; then
        ROW_COUNT="$(
            "${DOCKER_CMD[@]}" exec "$CONTAINER_NAME" \
                psql \
                --username="$DB_USER" \
                --dbname="$TARGET_DB" \
                --tuples-only \
                --no-align \
                --set=ON_ERROR_STOP=1 \
                --command="SELECT COUNT(*) FROM \"$TABLE\";"
        )"

        ROW_COUNT="$(echo "$ROW_COUNT" | tr -d '[:space:]')"

        echo "$TABLE: $ROW_COUNT rows"
    else
        echo "$TABLE: not present"
    fi
done

echo
echo "========================================"
echo "Restore completed successfully."
echo "Database: $TARGET_DB"
echo "========================================"
