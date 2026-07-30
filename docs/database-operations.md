# Database Operations

How to set up, back up, restore, and maintain the PostgreSQL database for this
app. For the data model itself (tables/columns/constraints), see
[database-design.md](database-design.md).

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
[Setting Up a New Environment](../scripts/README.md#setting-up-a-new-environment)
in `scripts/README.md`).

## Database Setup

Requires an empty PostgreSQL database that already exists (create it with
`docker exec postgresql createdb -U casaos your_db_name`) and a `.env` with
`DATABASE_URL` pointing at it. Then, from the project root:

```bash
./scripts/setup/init_database.sh
```

This applies `database/postgresql/schema/001_init_schema.sql` followed by
`database/postgresql/seed/001_seed_basic_data.sql`. Running it against a
database that already has tables is refused, so it never overwrites existing
data — use `scripts/database/restore_database.sh` instead if you want to load a
backup. Running this against a fresh database on every environment
(development, test, production) is what keeps their schemas identical.

It then creates the default admin account — username `admin`, password
`admin` — by running `scripts/create_user.py` through
`apps/flask/.venv/bin/python`, so the venv (see
[Setting Up a New Environment](../scripts/README.md#setting-up-a-new-environment))
must already exist; if it doesn't, this step is skipped with a message
telling you the command to run manually afterward. Change the password after
first login if the environment is reachable by anyone other than you.

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
- runs `scripts/database/verify_backup.sh` against the new backup
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
BACKUP_RETENTION_DAYS=30 ./scripts/database/backup_database.sh
```

The nightly cron job for this is installed by
[`install_cron.sh`](../scripts/README.md#install-cron-jobs). Logs are written to:

```text
logs/database_backup.log
```

## Verify Existing Backup

Verify a dump file manually:

```bash
./scripts/database/verify_backup.sh backups/database/portfolio_tracker_YYYY-MM-DD_HH-MM-SS.dump
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
./scripts/database/restore_database.sh backups/database/portfolio_tracker_YYYY-MM-DD_HH-MM-SS.dump
```

This drops and recreates the `public` schema and then restores the dump into
it, so it replaces whatever is currently in the target database — it does
not need `scripts/setup/init_database.sh` to have run first. (It deliberately
doesn't use `pg_restore --clean`: that command can fail partway through on a
database with foreign keys, because it doesn't always drop tables in a safe
dependency order — dropping the whole schema first sidesteps that.) You'll
be asked to confirm; pass `-y` to skip the prompt for scripted/cron use.

## Maintenance

Destructive, hand-run SQL for clearing data during development. Load local
environment variables and run from the project root:

```bash
set -a
. .env
set +a
```

**Delete Portfolio and Market Data:**

```bash
docker exec -i postgresql psql "$DATABASE_URL" --set ON_ERROR_STOP=1 < database/postgresql/maintenance/001_truncate_all_data.sql
```

This deletes all rows from:

- `portfolio_manual_items`
- `portfolio_manual_item_prices`
- `portfolio_holdings`
- `asset_prices`
- `assets`
- `asset_categories`

It keeps users, login history, and the table structure. It restarts the ID
counters for the truncated portfolio and market-data tables.

**Delete Only Prices:**

```bash
docker exec -i postgresql psql "$DATABASE_URL" --set ON_ERROR_STOP=1 < database/postgresql/maintenance/002_truncate_prices.sql
```

This deletes all rows from `asset_prices` and `portfolio_manual_item_prices` only.
