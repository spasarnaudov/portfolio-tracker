#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="$PROJECT_DIR/runtime/app.pid"

if [[ ! -f "$PID_FILE" ]]; then
    echo "App is not running (no PID file)."
    exit 0
fi

PID="$(cat "$PID_FILE")"

if ! kill -0 "$PID" 2>/dev/null; then
    echo "App is not running (stale PID file removed)."
    rm -f "$PID_FILE"
    exit 0
fi

echo "Stopping app (PID $PID)..."
kill "$PID"

for _ in $(seq 1 10); do
    if ! kill -0 "$PID" 2>/dev/null; then
        break
    fi
    sleep 1
done

if kill -0 "$PID" 2>/dev/null; then
    echo "App did not stop within 10s, forcing it..."
    kill -9 "$PID"
fi

rm -f "$PID_FILE"
echo "App stopped."
