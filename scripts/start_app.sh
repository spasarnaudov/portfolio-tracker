#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DIR="$PROJECT_DIR/apps/flask"
PYTHON="$APP_DIR/.venv/bin/python"
PID_FILE="$PROJECT_DIR/runtime/app.pid"
LOG_FILE="$PROJECT_DIR/logs/app.log"

mkdir -p "$PROJECT_DIR/runtime" "$PROJECT_DIR/logs"

if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo "App is already running (PID $(cat "$PID_FILE"))."
    exit 0
fi

if [[ ! -x "$PYTHON" ]]; then
    echo "ERROR: $PYTHON not found. Create the venv first:"
    echo "  python3 -m venv $APP_DIR/.venv"
    echo "  $APP_DIR/.venv/bin/pip install -r $APP_DIR/requirements.txt"
    exit 1
fi

# On a fresh boot, cron's @reboot line can fire before Docker Desktop (and the
# postgresql container inside it) has finished starting. Wait briefly instead
# of racing it — harmless if Postgres is already up, since pg_isready then
# succeeds on the first try.
if command -v docker &>/dev/null; then
    POSTGRES_CONTAINER_NAME="${POSTGRES_CONTAINER_NAME:-postgresql}"
    if [[ -f "$PROJECT_DIR/.env" ]]; then
        ENV_CONTAINER_NAME="$(grep -m1 '^POSTGRES_CONTAINER_NAME=' "$PROJECT_DIR/.env" | cut -d= -f2- || true)"
        POSTGRES_CONTAINER_NAME="${ENV_CONTAINER_NAME:-$POSTGRES_CONTAINER_NAME}"
    fi
    if docker inspect "$POSTGRES_CONTAINER_NAME" &>/dev/null; then
        echo "Waiting for PostgreSQL container '$POSTGRES_CONTAINER_NAME' to be ready..."
        for _ in $(seq 1 30); do
            docker exec "$POSTGRES_CONTAINER_NAME" pg_isready --quiet 2>/dev/null && break
            sleep 1
        done
    fi
fi

echo "Starting app..."

cd "$APP_DIR"
nohup "$PYTHON" app.py >> "$LOG_FILE" 2>&1 &
APP_PID=$!
disown

echo "$APP_PID" > "$PID_FILE"

# Give it a moment to crash on startup (bad .env, port already in use, etc.)
# before reporting success.
sleep 1

if kill -0 "$APP_PID" 2>/dev/null; then
    echo "App started (PID $APP_PID)."
    echo "Logs: $LOG_FILE"
else
    echo "ERROR: App failed to start. Check $LOG_FILE"
    rm -f "$PID_FILE"
    exit 1
fi
