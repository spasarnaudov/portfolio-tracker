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
