# Scripts

## Import Tavex Prices

Run a single Tavex import:

```bash
apps/flask/.venv/bin/python scripts/import_tavex_prices.py
```

The script stores prices with the current round hour, for example `14:00:00`.

The script imports prices only when automatic Tavex import is enabled from the Dashboard.
Use the Dashboard button to enable or disable the automatic import without editing cron.

Manual imports from the web interface use the current time. The cron script uses the current round hour.

## Run Every Hour

Open the crontab editor:

```bash
crontab -e
```

Add this line:

```cron
0 * * * * cd /home/spas/Projects/portfolio-tracker && apps/flask/.venv/bin/python scripts/import_tavex_prices.py >> /home/spas/Projects/portfolio-tracker/logs/tavex_import.log 2>&1
```

This runs the import on every round hour.

Logs are written to:

```text
logs/tavex_import.log
```

The latest log lines are visible on the Dashboard.
