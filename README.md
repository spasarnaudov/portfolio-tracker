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
- Interactive portfolio value chart
- Tavex product and price import
- Hourly Tavex price import and manual-item price snapshots through cron
- Dashboard switch for enabling or disabling automatic Tavex imports
- Portfolio page with owned Tavex quantities
- Jewelry and manual items with Tavex gold buyback price helpers
- Portfolio value chart with selectable Tavex and manual gold items
- User login and registration with password hashing
- Successful login history with last-login and usage counts
- Self-service account deactivation with preserved user and portfolio data
- User roles: admin and user
- Database maintenance scripts

## Local Runtime Files

Some application state is intentionally stored locally and is not committed:

- `.env.development`, `.env.test`, `.env.staging`, and `.env.production`
  store environment-specific settings and secrets.
- `runtime/auto_tavex_import.enabled` controls the Tavex part of the cron import.
  Manual-item price snapshots continue to run every hour.
- `logs/tavex_import.log` stores automatic import output.
- `logs/database_backup.log` stores automatic database backup output.
- `logs/env_backup.log` stores automatic env backup output.
- `backups/database/*.dump` stores PostgreSQL backup files.
- `backups/env/*.backup` stores env backup files with secrets.

## Useful Commands

Create a local environment file from an example:

```bash
cp .env.development.example .env.development
```

Run the Flask development server from the project root:

```bash
APP_ENV=development apps/flask/.venv/bin/python apps/flask/app.py
```

Run the app against the test environment:

```bash
APP_ENV=test apps/flask/.venv/bin/python apps/flask/app.py
```

Run a manual Tavex import:

```bash
APP_ENV=development apps/flask/.venv/bin/python scripts/import_tavex_prices.py
```

Load an environment file before running database commands:

```bash
set -a
. .env.development
set +a
```

Initialize an empty database schema:

```bash
psql "$DATABASE_URL" -f database/postgresql/schema/001_init_schema.sql
psql "$DATABASE_URL" -f database/postgresql/seed/001_seed_basic_data.sql
```

Create or update an application user from the terminal:

```bash
apps/flask/.venv/bin/python scripts/create_user.py username
```

Create or update the role-management account:

```bash
apps/flask/.venv/bin/python scripts/create_user.py "$ROLE_MANAGER_USERNAME" --password "$ROLE_MANAGER_PASSWORD"
```

## Admin dashboards

Users with the `admin` role can access the `Users` and `Logs` dashboards from
the main navigation. Both pages require an authenticated admin account. The
The Users dashboard displays fixed roles and allows account-status management.

The Logs dashboard reads regular `.log` files directly from the project-level
`logs/` directory and displays at most the last 500 lines of each file. Log
files are runtime data and are excluded from Git by `.gitignore`.

## Environments

The same application code is used in every environment. Differences come from
environment variables loaded from one of these local files:

- `.env.development`
- `.env.test`
- `.env.staging`
- `.env.production`

The real files are ignored by git. Use the committed examples as templates:

```bash
cp .env.development.example .env.development
cp .env.test.example .env.test
cp .env.staging.example .env.staging
cp .env.production.example .env.production
```

Each file must point to its own database through `DATABASE_URL`:

- development: `portfolio_tracker_development`
- test: `portfolio_tracker_test`
- staging: `portfolio_tracker_staging`
- production: `portfolio_tracker_production`

## Docker

Build one image:

```bash
docker build -t portfolio-tracker:1.0.0 .
```

Run the same image with different environment files:

```bash
docker run --env-file .env.staging -p 5002:5000 portfolio-tracker:1.0.0
docker run --env-file .env.production -p 5003:5000 portfolio-tracker:1.0.0
```

Staging and production use Gunicorn from the Docker image default command.
Development can use the Flask debug server:

```bash
APP_ENV=development apps/flask/.venv/bin/python apps/flask/app.py
```

Docker Compose profiles:

```bash
docker compose --profile development up --build
docker compose --profile test up --build
docker compose --profile staging up --build
docker compose --profile production up --build
```

Start commands by environment:

```bash
# development
APP_ENV=development apps/flask/.venv/bin/python apps/flask/app.py

# test
APP_ENV=test apps/flask/.venv/bin/python apps/flask/app.py

# staging
docker run --env-file .env.staging -p 5002:5000 portfolio-tracker:1.0.0

# production
docker run --env-file .env.production -p 5003:5000 portfolio-tracker:1.0.0
```

Role behavior:

- `admin`: reserved for the single configured role-management account.
- `user`: assigned to every other account and sees its own portfolio data.

The special `admin` account is intended only for role management. It can open
the Users and Password tabs, but it cannot browse portfolio or market-data tabs.
Roles cannot be changed from the application. The database permits only one
account with the `admin` role.
Users can be activated or deactivated from the Users page. The currently logged-in
user and the special `admin` account cannot be deactivated from that page.

Sessions use `SESSION_TIMEOUT_MINUTES` from the active environment file. When there is no
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
