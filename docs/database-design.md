# Database Design

The data model: tables, columns, and constraints. Role behavior, session
rules, and other application-level behavior live in
[README.md → Configuration](../README.md#configuration) — this document
only covers what the database itself enforces.

## Tables

### asset_categories

Stores categories used by imported Tavex products and generated price series,
including Gold, Silver, and Gold buyback.

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

Marks that a user owns a tracked asset (currently Tavex products) and whether
it contributes to the portfolio chart. The owned quantity itself is not
stored here — see `portfolio_asset_purchases`.

Columns:
- user_id: reference to users and part of the primary key
- asset_id: reference to assets and part of the primary key
- include_in_chart: controls whether the holding contributes to the portfolio chart

Notes:
- A row only exists for a user/asset pair that has at least one purchase lot
  in `portfolio_asset_purchases`. The application deletes the row when its
  last lot is deleted.
- Latest asset prices are used for the current value; quantity is the sum of
  that user's purchase lots for the asset.
- Historical portfolio value uses average asset prices for the selected chart
  interval, multiplied by the quantity actually owned as of each historical
  point (the sum of lots purchased on or before that date).
- Only holdings selected with `include_in_chart` contribute to the portfolio chart.
- Holdings are scoped per user, so the same asset can have different quantities for different users.

### portfolio_asset_purchases

Stores individual purchase lots behind a `portfolio_holdings` row — how much
was bought, at what price, and on what date. This is what makes profit
calculations possible; there is currently no equivalent record for sells.

Columns:
- id: unique purchase lot ID
- user_id: reference to users
- asset_id: reference to assets
- quantity: quantity bought in this lot (must be greater than zero)
- purchase_price: price paid per unit (must be zero or greater)
- purchase_date: when the lot was purchased
- receipt_filename: filename of an attached receipt photo (in `uploads/receipts/`
  on disk, not in the database), or null if none was uploaded

Notes:
- A holding's total quantity and cost basis are the sum of its lots'
  quantities and `quantity * purchase_price` respectively; profit is current
  value minus cost basis.
- `receipt_filename` is server-generated, never the client's original
  filename. The file itself is served only through an authenticated,
  ownership-checked route — see
  [database-operations.md → Uploaded Receipt Photos](database-operations.md#uploaded-receipt-photos).
- Deleting a user or asset cascades to their purchase lots.
- Deleting a lot that was the last one for a user/asset pair also deletes the
  corresponding `portfolio_holdings` row.

### portfolio_manual_items

Stores manually entered items such as jewelry.

Columns:
- id: unique manual item ID
- user_id: reference to users
- name: item name
- quantity: item quantity or weight
- unit_price: fixed unit price used when no automatic source is selected
- price_asset_id: optional Gold buyback asset used as the automatic price source
- include_in_chart: controls whether the item contributes to the portfolio chart

Notes:
- Jewelry can use fractional quantity values, for example grams.
- Jewelry can be linked to a Tavex Gold buyback series by karat/fineness.
- Linked jewelry uses the latest asset price for its current value and the asset's
  recorded prices for its historical portfolio value.
- Fixed-price items continue to use their recorded manual price snapshots.

### portfolio_manual_item_prices

Stores the hourly unit-price history for jewelry and manually entered items.

Columns:
- id: unique price record ID
- manual_item_id: reference to the manual item
- price_date: round-hour snapshot timestamp
- price: the item's unit price at that timestamp

Notes:
- Each fixed-price item has at most one price per timestamp.
- Items linked to a Gold buyback asset use `asset_prices` and do not need duplicate
  manual snapshots.
- Price history is deleted automatically when its manual item is deleted.

### users

Stores application users used for login.

Columns:
- id: unique user ID
- username: unique login username
- password_hash: hashed password, never the plain password
- role: application role, either admin or user
- is_deleted: marks a self-deleted account while preserving its data
- active_session_token: token for the currently active browser session
- active_session_expires_at: timestamp when the active session expires
- created_at: timestamp when the user was created

Notes:
- Passwords are hashed by the Flask application before they are stored.
- Users can be created from the registration page or from the terminal helper script.
- Only one account can have the `admin` role, enforced by a unique partial
  index (`uq_users_single_admin_role`) on `role` where `role = 'admin'`. See
  [README.md → Configuration](../README.md#configuration) for role and
  session behavior.
- Users marked as deleted cannot log in.
- Self-deletion sets `is_deleted` without removing the account or its related data.
- A database trigger prevents a deleted account from clearing its deleted state.

### user_login_history

Stores one record for every successful login, including the first session created
after registration.

Columns:
- id: unique login event ID
- user_id: reference to the user
- username: username snapshot kept with the login event
- logged_in_at: timestamp of the successful login

Notes:
- `username` is a snapshot, not a live reference, specifically so login history and
  the username remain available after a user is deleted.
- The user filter includes current users and deleted users that have login history.
- See [README.md → Admin dashboards](../README.md#admin-dashboards) for how this
  data is displayed, and [README.md → Configuration](../README.md#configuration)
  for account deactivation behavior.
