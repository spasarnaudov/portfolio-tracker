#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Adds one crontab line for the current user, doing nothing if that exact
# line is already present — safe to run repeatedly and safe to run once per
# environment checkout, since every line below is built from this script's
# own PROJECT_DIR and never touches another checkout's entries.
install_cron_line() {
    local line="$1"
    if crontab -l 2>/dev/null | grep -Fq "$line"; then
        echo "Already installed: $line"
        return
    fi
    (crontab -l 2>/dev/null; echo "$line") | crontab -
    echo "Installed: $line"
}

install_cron_line "@reboot cd $PROJECT_DIR && ./scripts/start_app.sh >> $PROJECT_DIR/logs/app.log 2>&1"
install_cron_line "0 * * * * cd $PROJECT_DIR && apps/flask/.venv/bin/python scripts/import_tavex_prices.py >> $PROJECT_DIR/logs/tavex_import.log 2>&1"
install_cron_line "0 3 * * * cd $PROJECT_DIR && ./scripts/backup_database.sh >> $PROJECT_DIR/logs/database_backup.log 2>&1"
install_cron_line "0 3 * * * cd $PROJECT_DIR && ./scripts/backup_env.sh >> $PROJECT_DIR/logs/env_backup.log 2>&1"

echo
echo "Current crontab:"
crontab -l
