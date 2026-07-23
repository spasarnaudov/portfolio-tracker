# Scripts

Every script derives its own project root from its location on disk (nothing
is hardcoded to a specific path or directory name), so cloning this repo
into any directory works without editing any script, and running several
independent checkouts side by side on the same machine (e.g.
`portfolio-tracker`, `portfolio-tracker-alpha`, `portfolio-tracker-beta`) is
fully supported — each checkout only ever touches its own `.env`,
`runtime/`, `logs/`, `backups/`, and its own crontab lines.

## Setting Up a New Environment

1. Clone the repo into its own directory.
2. Create the Python virtualenv and install dependencies:

   ```bash
   python3 -m venv apps/flask/.venv
   apps/flask/.venv/bin/pip install -r apps/flask/requirements.txt
   ```

3. Create the config from the template, then edit it:

   ```bash
   cp .env.example .env
   ```

   At minimum, set a `DATABASE_URL`/`DB_NAME` unique to this environment (a
   distinct database inside the shared PostgreSQL container — see
   [PostgreSQL Runs in Docker](#postgresql-runs-in-docker)) and a `PORT` not
   already used by another environment on this machine.

4. Create the empty database itself — the container needs to know about it
   before `init_database.sh` can use it:

   ```bash
   docker exec postgresql createdb -U casaos your_db_name
   ```

5. Initialize the schema — see [Database Setup](#database-setup):

   ```bash
   ./scripts/init_database.sh
   ```

6. Install this environment's cron jobs (autostart on reboot, hourly import,
   nightly backups) — see [Install Cron Jobs](#install-cron-jobs):

   ```bash
   ./scripts/install_cron.sh
   ```

7. Start the app:

   ```bash
   ./scripts/start_app.sh
   ```

## Run the App

Start, stop, or restart the Flask app as a background process:

```bash
./scripts/start_app.sh
./scripts/stop_app.sh
./scripts/restart_app.sh
```

`start_app.sh` refuses to start a second copy if one is already running (it
tracks the process in `runtime/app.pid`), and reports a clear error instead
of silently doing nothing if the app crashes immediately (for example, the
port from `.env` is already in use). App output goes to `logs/app.log`.

This runs `python apps/flask/app.py` in the background — it's a starting
point, not a substitute for a real process supervisor (systemd, etc.): if
the app crashes after startup, nothing currently restarts it automatically.
To start it automatically after a reboot, see
[Install Cron Jobs](#install-cron-jobs).

## Install Cron Jobs

Install every standard cron job for this checkout in one step:

```bash
./scripts/install_cron.sh
```

Safe to run more than once — it checks each line before adding, so nothing
is ever duplicated, and it never touches another checkout's crontab lines
(every line is built from this script's own project directory). It installs
exactly these four lines (paths shown here for a checkout at
`/home/spas/Projects/portfolio-tracker`; adjust automatically to wherever
you actually cloned it):

```cron
@reboot cd /home/spas/Projects/portfolio-tracker && ./scripts/start_app.sh >> /home/spas/Projects/portfolio-tracker/logs/app.log 2>&1
0 * * * * cd /home/spas/Projects/portfolio-tracker && apps/flask/.venv/bin/python scripts/import_tavex_prices.py >> /home/spas/Projects/portfolio-tracker/logs/tavex_import.log 2>&1
0 3 * * * cd /home/spas/Projects/portfolio-tracker && ./scripts/backup_database.sh >> /home/spas/Projects/portfolio-tracker/logs/database_backup.log 2>&1
0 3 * * * cd /home/spas/Projects/portfolio-tracker && ./scripts/backup_env.sh >> /home/spas/Projects/portfolio-tracker/logs/env_backup.log 2>&1
```

Prefer editing the crontab by hand? Run `crontab -e` and add the lines
above yourself (with the path adjusted) — `install_cron.sh` is just a
reliable way to do the same thing without copy-paste mistakes.

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

Both manual script runs and cron use the current round hour. The cron job
that runs this hourly is installed by
[`install_cron.sh`](#install-cron-jobs). Logs are written to:

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

This also means multiple environments can all share the same PostgreSQL
container, as long as each one's `.env` has its own `DATABASE_URL`/`DB_NAME`
pointing at its own database inside that container (see
[Setting Up a New Environment](#setting-up-a-new-environment)).

## Database Setup

Requires an empty PostgreSQL database that already exists (create it with
`docker exec postgresql createdb -U casaos your_db_name`) and a `.env` with
`DATABASE_URL` pointing at it. Then, from the project root:

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

The nightly cron job for this is installed by
[`install_cron.sh`](#install-cron-jobs). Logs are written to:

```text
logs/database_backup.log
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

Env backup files contain secrets and must not be committed to git. The
nightly cron job for this is installed by
[`install_cron.sh`](#install-cron-jobs). Logs are written to:

```text
logs/env_backup.log
```
