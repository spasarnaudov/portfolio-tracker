# Database Design

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

Stores quantities of owned tracked assets, currently used for Tavex products.

Columns:
- user_id: reference to users and part of the primary key
- asset_id: reference to assets and part of the primary key
- quantity: owned quantity
- include_in_chart: controls whether the holding contributes to the portfolio chart

Notes:
- If quantity is zero or lower, the holding is deleted by the application.
- Latest asset prices are used for the current value.
- Historical portfolio value uses average asset prices for the selected chart interval before multiplying by quantity.
- Only holdings selected with `include_in_chart` contribute to the portfolio chart.
- Holdings are scoped per user, so the same asset can have different quantities for different users.

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
- The application uses a session cookie after successful login.
- Only one active session per user is allowed.
- Inactivity timeout is configured through `SESSION_TIMEOUT_MINUTES`.
- Users can be created from the registration page or from the terminal helper script.
- Logged-in users can change their own password from the application.
- The special admin account can access Users and Logs.
- User accounts see their own portfolio data.
- The special `admin` user is limited to user and login-history management.
- Roles are read-only in the application, and only one account can have the `admin` role.
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
- The Users admin table displays the latest login and total login count.
- Login history and the username remain available after a user is deleted.
- The user filter includes current users and deleted users that have login history.
- Regular users can deactivate their own account after confirmation; the account and its data remain stored.
- The special admin account is protected, and admins cannot reactivate a self-deleted account.
