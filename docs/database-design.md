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

### portfolio_holdings

Stores quantities of owned tracked assets, currently used for Tavex products.

Columns:
- asset_id: reference to assets and primary key
- quantity: owned quantity

Notes:
- If quantity is zero or lower, the holding is deleted by the application.
- Latest asset prices are used for the current value.
- Historical portfolio value uses average asset prices for the selected chart interval before multiplying by quantity.

### portfolio_manual_items

Stores manually entered items such as jewelry.

Columns:
- id: unique manual item ID
- name: item name
- quantity: item quantity or weight
- unit_price: current unit price

Notes:
- Jewelry can use fractional quantity values, for example grams.
- Tavex buyback prices by karat can be used to fill the unit price.
- Manual items are added to the portfolio chart as a static value.

### portfolio_cash_items

Stores cash and bank savings entries.

Columns:
- id: unique cash item ID
- name: entry name
- amount: current amount

Notes:
- Cash entries are added to the portfolio total and chart as a static value.
