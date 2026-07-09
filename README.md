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
- Database maintenance scripts

## Local Runtime Files

Some application state is intentionally stored locally and is not committed:

- `apps/flask/.env` stores database credentials.
- `runtime/chart_filters.json` stores the selected chart layout and filters.
- `runtime/auto_tavex_import.enabled` controls whether the cron import is active.
- `logs/tavex_import.log` stores automatic import output.

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

Run schema migration for timestamp prices on an existing database:

```bash
psql -h localhost -p 5432 -U casaos -d portfolio_tracker -f database/postgresql/schema/002_price_date_to_timestamp.sql
```

Run newer portfolio migrations on an existing database:

```bash
psql -h localhost -p 5432 -U casaos -d portfolio_tracker -f database/postgresql/schema/003_create_portfolio_holdings.sql
psql -h localhost -p 5432 -U casaos -d portfolio_tracker -f database/postgresql/schema/004_create_portfolio_manual_items.sql
psql -h localhost -p 5432 -U casaos -d portfolio_tracker -f database/postgresql/schema/005_create_portfolio_cash_items.sql
psql -h localhost -p 5432 -U casaos -d portfolio_tracker -f database/postgresql/schema/006_create_users.sql
```

Create or update an application user from the terminal:

```bash
apps/flask/.venv/bin/python scripts/create_user.py spas
```

Assign existing portfolio data to the initial `Spas` user:

```bash
apps/flask/.venv/bin/python scripts/create_user.py Spas --password spas
psql -h localhost -p 5432 -U casaos -d portfolio_tracker -f database/postgresql/schema/007_scope_portfolio_data_by_user.sql
```

## Next Steps

- Improve deployment setup for the HomeLab server
