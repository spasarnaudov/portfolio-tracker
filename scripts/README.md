# Scripts

All commands below assume the project is deployed at:

```text
/home/spas/Projects/portfolio-tracker
```

Adjust the path in cron when deploying to another directory.

## Import Hourly Prices

Run the hourly import job once:

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

Disable it with:

```bash
rm runtime/auto_tavex_import.enabled
```

Manual-item snapshots continue even when the Tavex part is disabled.

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

## PostgreSQL Runs in Docker

All database scripts (`init_database.sh`, `backup_database.sh`,
`verify_backup.sh`, `restore_database.sh`) run `pg_dump`/`psql`/`pg_restore`
**inside the PostgreSQL container** via `docker exec`/`docker cp`, instead of
requiring `postgresql-client` on the host. This means:

- the host never needs PostgreSQL client tools installed — only the `docker`
  CLI and permission to use it
- the tool version always matches the server exactly, since both come from
  the same container image

They expect a running container named `postgresql` (`docker ps` should show
it). If yours is named differently, set it in `.env`:

```bash
POSTGRES_CONTAINER_NAME=your_container_name
```

`DATABASE_URL` still works exactly as before — it's passed straight through
to `pg_dump`/`psql` inside the container, and since the container's own
PostgreSQL listens on `localhost` internally too, a `DATABASE_URL` pointing
at `localhost` resolves correctly from inside the container as well.

## Database Setup

Requires an empty PostgreSQL database that already exists (create it with
`docker exec postgresql createdb ...` or however the container provisions
databases) and a `.env` with `DATABASE_URL` pointing at it. Then, from the
project root:

```bash
./scripts/init_database.sh
```

This applies `database/postgresql/schema/001_init_schema.sql` followed by
`database/postgresql/seed/001_seed_basic_data.sql`. Running it against a
database that already has tables is refused, so it never overwrites existing
data — use `scripts/restore_database.sh` instead if you want to load a
backup. Running this against a fresh database on every environment
(development, test, production) is what keeps their schemas identical.

## Database Backups

Create and verify a PostgreSQL backup manually:

```bash
./scripts/backup_database.sh
```

The backup script:

- checks Docker is available, the `postgresql` container is running, and
  PostgreSQL inside it is accepting connections, before doing anything else
- runs `pg_dump` inside the container and writes its output to a hidden temp
  file first, only renaming it to the final `.dump` name once the dump is
  confirmed non-empty — a failed/interrupted run can never leave an empty or
  partial file at that name
- runs `scripts/verify_backup.sh` against the new backup
- only once verification passes, removes backups older than
  `RETENTION_DAYS` — a broken new backup can never cost you the last
  known-good ones
- loads deploy settings from `.env`

Backup files are runtime artifacts and must not be committed to git.

The relevant `.env` values are:

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/database_name
DB_NAME=your_database_name
BACKUP_DIR=/absolute/path/to/database/backups
BACKUP_RETENTION_DAYS=30
POSTGRES_CONTAINER_NAME=postgresql
```

You can override them from the shell or from cron:

```bash
BACKUP_RETENTION_DAYS=30 ./scripts/backup_database.sh
```

## Verify Existing Backup

Verify a dump file manually:

```bash
./scripts/verify_backup.sh backups/database/portfolio_tracker_YYYY-MM-DD_HH-MM-SS.dump
```

The verification script checks that:

- the file exists
- the file is not empty
- `pg_restore --list`, run inside the PostgreSQL container against a
  temporary copy of the file (`docker cp`), can read the dump structure

## Restore Database

Restore a backup (schema and data) into the database `DATABASE_URL` points
at:

```bash
./scripts/restore_database.sh backups/database/portfolio_tracker_YYYY-MM-DD_HH-MM-SS.dump
```

This drops and recreates the `public` schema and then restores the dump into
it, so it replaces whatever is currently in the target database — it does
not need `scripts/init_database.sh` to have run first. (It deliberately
doesn't use `pg_restore --clean`: that command can fail partway through on a
database with foreign keys, because it doesn't always drop tables in a safe
dependency order — dropping the whole schema first sidesteps that.) You'll
be asked to confirm; pass `-y` to skip the prompt for scripted/cron use.

## Env Backups

Create a backup of `.env` manually:

```bash
./scripts/backup_env.sh
```

The env backup script:

- loads settings from `.env`
- copies the env file to `backups/env/`
- stores the backup with file permissions `600`
- removes env backups older than `ENV_BACKUP_RETENTION_DAYS`

The relevant `.env` values are:

```bash
ENV_BACKUP_DIR=/absolute/path/to/env/backups
ENV_BACKUP_RETENTION_DAYS=30
```

Env backup files contain secrets and must not be committed to git.

## Backup Cron

Open the crontab editor:

```bash
crontab -e
```

Run the database backup every night at 03:00:

```cron
0 3 * * * cd /home/spas/Projects/portfolio-tracker && ./scripts/backup_database.sh >> /home/spas/Projects/portfolio-tracker/logs/database_backup.log 2>&1
```

Logs are written to:

```text
logs/database_backup.log
```

Run the env backup every night at 03:00:

```cron
0 3 * * * cd /home/spas/Projects/portfolio-tracker && ./scripts/backup_env.sh >> /home/spas/Projects/portfolio-tracker/logs/env_backup.log 2>&1
```

Env backup logs are written to:

```text
logs/env_backup.log
```

`logs/*.log`, `backups/database/*.dump`, and `backups/env/*.backup` are ignored by git.
