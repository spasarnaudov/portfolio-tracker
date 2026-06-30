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
- price_date: date of the price
- price: asset price on that date