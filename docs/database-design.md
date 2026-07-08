# Database Design

## Tables

### asset_categories

Stores asset categories such as Stocks, ETFs, Crypto, Cash, and Gold.

Columns:
- id: unique category ID
- name: category name

### assets

Stores the assets that are tracked in the portfolio.

Columns:
- id: unique asset ID
- symbol: short asset symbol
- name: full asset name
- category_id: reference to asset_categories

### asset_prices

Stores historical prices for each asset.

Columns:
- id: unique price record ID
- asset_id: reference to assets
- price_date: timestamp of the price record
- price: asset price at that timestamp

Notes:
- `price_date` uses timestamp precision so the application can store multiple prices for the same asset during one day.
- The unique constraint is based on `asset_id` and `price_date`, so one asset can have only one price for the exact same timestamp.
