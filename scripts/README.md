# Scripts

All commands below assume the project is deployed at:

```text
/home/spas/Projects/portfolio-tracker
```

Adjust the path in cron when deploying to another directory.

## Import Hourly Prices

Run a single Tavex import:

```bash
apps/flask/.venv/bin/python scripts/import_tavex_prices.py
```

The script stores Tavex prices and the current prices of all jewelry/manual items
with the current round hour, for example `14:00:00`.

Manual-item prices are stored every time the cron script runs. Tavex product
prices and the gold buyback price per gram for every available karat are stored
together at the same round-hour timestamp when automatic Tavex import is enabled.
Enable the Tavex part of the cron import with:

```bash
mkdir -p runtime
touch runtime/auto_tavex_import.enabled
```

Disable it by removing `runtime/auto_tavex_import.enabled`. Manual-item snapshots
continue even when the Tavex part is disabled.

Both manual script runs and cron use the current round hour.

## Run Every Hour

Open the crontab editor:

```bash
crontab -e
```

Add this line:

```cron
0 * * * * cd /home/spas/Projects/portfolio-tracker && apps/flask/.venv/bin/python scripts/import_tavex_prices.py >> /home/spas/Projects/portfolio-tracker/logs/tavex_import.log 2>&1
```

This stores manual-item prices and runs the enabled Tavex import on every round hour.

Logs are written to:

```text
logs/tavex_import.log
```

## Database Backups

Create and verify a PostgreSQL backup manually:

```bash
./scripts/backup_database.sh
```

The backup script:

- creates a custom-format PostgreSQL dump in `backups/database/`
- removes database backups older than `RETENTION_DAYS`
- runs `scripts/verify_backup.sh` against the created dump
- loads deploy settings from `.env.development` by default, or from `ENV_FILE`

Backup files are runtime artifacts and must not be committed to git.

The relevant `.env` values are:

```bash
DB_CONTAINER_NAME=your_postgresql_container_name
DB_NAME=your_database_name
DB_USER=your_database_user
BACKUP_DIR=/absolute/path/to/database/backups
BACKUP_RETENTION_DAYS=30
```

You can override them from the shell or from cron:

```bash
DB_CONTAINER_NAME=your_postgresql_container_name BACKUP_RETENTION_DAYS=30 ./scripts/backup_database.sh
```

## Verify Existing Backup

Verify a dump file manually:

```bash
./scripts/verify_backup.sh backups/database/portfolio_tracker_YYYY-MM-DD_HH-MM-SS.dump
```

The verification script checks that:

- the file exists
- the file is not empty
- `pg_restore --list` can read the dump structure inside the PostgreSQL container

## Env Backups

Create a backup of the active environment file manually:

```bash
./scripts/backup_env.sh
```

The env backup script:

- loads settings from `.env.development` by default, or from `ENV_FILE`
- copies the env file to `backups/env/`
- stores the backup with file permissions `600`
- removes env backups older than `ENV_BACKUP_RETENTION_DAYS`

The relevant `.env` values are:

```bash
ENV_BACKUP_DIR=/absolute/path/to/env/backups
ENV_BACKUP_RETENTION_DAYS=30
```

Env backup files contain secrets and must not be committed to git.

To back up a different environment file, pass `APP_ENV` or `ENV_FILE`:

```bash
APP_ENV=staging ./scripts/backup_env.sh
ENV_FILE=/home/spas/Projects/portfolio-tracker/.env.production ./scripts/backup_env.sh
```

## Backup Cron

Open the crontab editor:

```bash
crontab -e
```

Run the database backup every night at 03:00:

```cron
0 3 * * * cd /home/spas/Projects/portfolio-tracker && ./scripts/backup_database.sh >> /home/spas/Projects/portfolio-tracker/logs/database_backup.log 2>&1
```

With explicit deploy settings:

```cron
0 3 * * * cd /home/spas/Projects/portfolio-tracker && ENV_FILE=/home/spas/Projects/portfolio-tracker/.env.production ./scripts/backup_database.sh >> /home/spas/Projects/portfolio-tracker/logs/database_backup.log 2>&1
```

Logs are written to:

```text
logs/database_backup.log
```

Run the env backup every night at 03:00:

```cron
0 3 * * * cd /home/spas/Projects/portfolio-tracker && ./scripts/backup_env.sh >> /home/spas/Projects/portfolio-tracker/logs/env_backup.log 2>&1
```

With explicit deploy settings:

```cron
0 3 * * * cd /home/spas/Projects/portfolio-tracker && ENV_FILE=/home/spas/Projects/portfolio-tracker/.env.production ./scripts/backup_env.sh >> /home/spas/Projects/portfolio-tracker/logs/env_backup.log 2>&1
```

Env backup logs are written to:

```text
logs/env_backup.log
```

`logs/*.log`, `backups/database/*.dump`, and `backups/env/*.backup` are ignored by git.
