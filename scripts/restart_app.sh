#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

"$PROJECT_DIR/scripts/stop_app.sh"
"$PROJECT_DIR/scripts/start_app.sh"
