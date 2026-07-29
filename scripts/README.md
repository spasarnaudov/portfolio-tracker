# Scripts

Every script derives its own project root from its location on disk (nothing
is hardcoded to a specific path or directory name), so cloning this repo
into any directory works without editing any script, and running several
independent checkouts side by side on the same machine (e.g.
`portfolio-tracker`, `portfolio-tracker-alpha`, `portfolio-tracker-beta`) is
fully supported — each checkout only ever touches its own `.env`,
`runtime/`, `logs/`, `backups/`, and its own crontab lines.

Database setup, backups, restore, and maintenance are covered separately in
[Database Operations](../docs/database-operations.md).

## New Server Setup

Before the first checkout on a brand-new machine, run this once
(machine-wide, not per-checkout — written for macOS/Apple Silicon with
Homebrew and Docker Desktop):

```bash
./scripts/setup_server.sh
```

It checks for and installs Homebrew, git, python3, and Docker Desktop;
verifies Tailscale is installed and connected; and creates the shared
`postgresql` container (`postgres:17.4`, matching every other checkout of
this project), prompting interactively for a superuser password it never
stores or generates itself. Safe to re-run — every step checks whether it's
already done before acting.

This machine can then host multiple environments (e.g. `alpha`, `beta`,
`production`) side by side, each in its own checkout, sharing this one
PostgreSQL container — continue with Setting Up a New Environment below for
each one.

## Setting Up a New Environment

1. Clone the repo into its own directory.
2. Create the Python virtualenv and install dependencies:

   ```bash
   python3 -m venv apps/flask/.venv
   apps/flask/.venv/bin/pip install -r apps/flask/requirements.txt
   ```

3. Generate the config interactively:

   ```bash
   ./scripts/init_env.sh
   ```

   Prompts for the environment name, port, database name, and the
   PostgreSQL password set in [New Server Setup](#new-server-setup) above,
   and writes `.env` with a freshly generated `SECRET_KEY`. Alternatively,
   copy `.env.example` to `.env` and edit it by hand — at minimum set a
   `DATABASE_URL`/`DB_NAME` unique to this environment (a distinct database
   inside the shared PostgreSQL container — see
   [PostgreSQL Runs in Docker](../docs/database-operations.md#postgresql-runs-in-docker))
   and a `PORT` not already used by another environment on this machine.

4. Create the empty database itself — the container needs to know about it
   before `init_database.sh` can use it:

   ```bash
   docker exec postgresql createdb -U casaos your_db_name
   ```

5. Initialize the schema — see
   [Database Setup](../docs/database-operations.md#database-setup). This
   also creates the default `admin`/`admin` account:

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
