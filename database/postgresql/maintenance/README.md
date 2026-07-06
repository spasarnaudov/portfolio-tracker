# Database Maintenance

## Delete All Data

Run this command from the project root:

```bash
psql -h localhost -p 5432 -U casaos -d portfolio_tracker -f database/postgresql/maintenance/001_truncate_all_data.sql
```

This deletes all rows from:

- `asset_prices`
- `assets`
- `asset_categories`

It keeps the table structure and restarts the ID counters.

## Delete Only Prices

Run this command from the project root:

```bash
psql -h localhost -p 5432 -U casaos -d portfolio_tracker -f database/postgresql/maintenance/002_truncate_prices.sql
```

This deletes all rows from `asset_prices` only.
