# Database Maintenance

## Delete Portfolio and Market Data

Load local environment variables and run this command from the project root:

```bash
set -a
. .env.development
set +a
psql "$DATABASE_URL" -f database/postgresql/maintenance/001_truncate_all_data.sql
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

## Delete Only Prices

Run this command from the project root:

```bash
set -a
. .env.development
set +a
psql "$DATABASE_URL" -f database/postgresql/maintenance/002_truncate_prices.sql
```

This deletes all rows from `asset_prices` and `portfolio_manual_item_prices` only.
