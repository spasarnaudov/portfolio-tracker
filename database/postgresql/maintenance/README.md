# Database Maintenance

PostgreSQL runs only in Docker (see
[scripts/README.md](../../../scripts/README.md#postgresql-runs-in-docker)), so
these commands pipe the `.sql` file into `psql` running inside the
`postgresql` container rather than calling a local `psql`.

## Delete Portfolio and Market Data

Load local environment variables and run this command from the project root:

```bash
set -a
. .env
set +a
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

## Delete Only Prices

Run this command from the project root:

```bash
set -a
. .env
set +a
docker exec -i postgresql psql "$DATABASE_URL" --set ON_ERROR_STOP=1 < database/postgresql/maintenance/002_truncate_prices.sql
```

This deletes all rows from `asset_prices` and `portfolio_manual_item_prices` only.
