# Portfolio Tracker

Portfolio Tracker is a personal project for tracking investment assets and their historical prices.

## Goals

- Learn PostgreSQL database design
- Build a web application
- Visualize portfolio data with charts
- Host the application on a personal HomeLab server

## Technologies

- PostgreSQL 17
- pgAdmin 4
- Docker
- Ubuntu 24.04
- CasaOS
- Python
- Flask

## Project Structure

```text
portfolio-tracker/
├── apps/
│   └── flask/
│       ├── app.py
│       ├── repository.py
│       ├── static/
│       └── templates/
├── database/
│   └── postgresql/
│       ├── maintenance/
│       ├── schema/
│       └── seed/
├── docs/
├── scripts/
├── README.md
└── .gitignore
```

## Current Version

The current version includes:

- Asset categories
- Assets
- Historical asset prices with timestamp support
- Flask web interface
- Dashboard summary
- Asset, category, and price tables
- Interactive charts
- Multiple configurable charts on the same page
- Per-chart asset, period, and price display settings
- Saved chart filter settings in local runtime state
- Tavex product and price import
- Optional hourly Tavex price import through cron
- Dashboard switch for enabling or disabling automatic Tavex imports
- Portfolio page with owned Tavex quantities
- Jewelry and manual items with Tavex gold buyback price helpers
- Cash and savings entries
- Portfolio value chart with hourly, daily, and weekly aggregation
- User login and registration with password hashing
- User roles: admin, user, and demo
- Database maintenance scripts

## Local Runtime Files

Some application state is intentionally stored locally and is not committed:

- `apps/flask/.env` stores database credentials.
- `runtime/chart_filters.json` stores the selected chart layout and filters.
- `runtime/auto_tavex_import.enabled` controls whether the cron import is active.
- `logs/tavex_import.log` stores automatic import output.
- `logs/database_backup.log` stores automatic database backup output.
- `logs/env_backup.log` stores automatic env backup output.
- `backups/database/*.dump` stores PostgreSQL backup files.
- `backups/env/*.backup` stores env backup files with secrets.

## Useful Commands

Run the Flask app from the project root:

```bash
cd apps/flask
.venv/bin/python app.py
```

Run a manual Tavex import:

```bash
apps/flask/.venv/bin/python scripts/import_tavex_prices.py
```

Load local environment variables before running database commands:

```bash
set -a
. apps/flask/.env
set +a
```

Run schema migration for timestamp prices on an existing database:

```bash
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f database/postgresql/schema/002_price_date_to_timestamp.sql
```

Run newer portfolio migrations on an existing database:

```bash
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f database/postgresql/schema/003_create_portfolio_holdings.sql
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f database/postgresql/schema/004_create_portfolio_manual_items.sql
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f database/postgresql/schema/005_create_portfolio_cash_items.sql
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f database/postgresql/schema/006_create_users.sql
```

Create or update an application user from the terminal:

```bash
apps/flask/.venv/bin/python scripts/create_user.py "$INITIAL_ADMIN_USERNAME"
```

Assign existing portfolio data to the initial user:

```bash
apps/flask/.venv/bin/python scripts/create_user.py "$INITIAL_ADMIN_USERNAME" --password "$INITIAL_ADMIN_PASSWORD" --role admin
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f database/postgresql/schema/007_scope_portfolio_data_by_user.sql
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f database/postgresql/schema/008_add_user_roles.sql
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f database/postgresql/schema/009_rename_demo_user.sql
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f database/postgresql/schema/010_add_user_session_tracking.sql
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f database/postgresql/schema/011_rename_spas_user.sql
```

Create a demo user and seed demo portfolio data:

```bash
apps/flask/.venv/bin/python scripts/create_user.py "$DEMO_USERNAME" --password "$DEMO_PASSWORD" --role demo
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f database/postgresql/seed/002_seed_demo_portfolio.sql
```

Create or update the role-management account:

```bash
apps/flask/.venv/bin/python scripts/create_user.py "$ROLE_MANAGER_USERNAME" --password "$ROLE_MANAGER_PASSWORD" --role admin
```

Role behavior:

- `admin`: sees all application tabs, imports, and global data tables.
- `user`: sees own portfolio and chart data.
- `demo`: behaves like `user`, but can be preloaded with demonstration data.

The special `admin` account is intended only for role management. It can open
the Users and Password tabs, but it cannot browse portfolio or market-data tabs.
The `demo` account role is locked, cannot change its password, and cannot be
changed from the Users page.
Users can be activated or deactivated from the Users page. The `demo` account,
the currently logged-in user, and the special `admin` account cannot be
deactivated from that page.

Sessions use `SESSION_TIMEOUT_MINUTES` from `apps/flask/.env`. When there is no
user activity for that many minutes, the user is logged out. A user can have
only one active session in the same environment; a new login asks whether to log
out the existing session first.

When running two environments on the same host with different ports, the app
uses a project-path-based default `SESSION_COOKIE_NAME`. Browsers separate
cookies by host, not reliably by port, so separate cookie names prevent local
environments from overwriting each other's login cookie. Set
`SESSION_COOKIE_NAME` in `.env` only when you want an explicit stable cookie
name for a deployment.

## Next Steps

- Improve deployment setup for the HomeLab server
