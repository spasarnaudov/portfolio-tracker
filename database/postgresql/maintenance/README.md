# Database Maintenance

## Delete All Data

Load local environment variables and run this command from the project root:

```bash
set -a
. .env.development
set +a
psql "$DATABASE_URL" -f database/postgresql/maintenance/001_truncate_all_data.sql
```

This deletes all rows from:

- `portfolio_cash_items`
- `portfolio_manual_items`
- `portfolio_holdings`
- `asset_prices`
- `assets`
- `asset_categories`

It keeps the table structure and restarts the ID counters.

## Delete Only Prices

Run this command from the project root:

```bash
set -a
. .env.development
set +a
psql "$DATABASE_URL" -f database/postgresql/maintenance/002_truncate_prices.sql
```

This deletes all rows from `asset_prices` only.
