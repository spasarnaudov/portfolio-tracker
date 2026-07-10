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
- user_id: reference to users and part of the primary key
- asset_id: reference to assets and primary key
- quantity: owned quantity

Notes:
- If quantity is zero or lower, the holding is deleted by the application.
- Latest asset prices are used for the current value.
- Historical portfolio value uses average asset prices for the selected chart interval before multiplying by quantity.
- Holdings are scoped per user, so the same asset can have different quantities for different users.

### portfolio_manual_items

Stores manually entered items such as jewelry.

Columns:
- id: unique manual item ID
- user_id: reference to users
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
- user_id: reference to users
- name: entry name
- amount: current amount

Notes:
- Cash entries are added to the portfolio total and chart as a static value.
- Cash entries are scoped per user.

### users

Stores application users used for login.

Columns:
- id: unique user ID
- username: unique login username
- password_hash: hashed password, never the plain password
- role: application role, one of admin, user, or demo
- is_active: controls whether the user can log in
- active_session_token: token for the currently active browser session
- active_session_expires_at: timestamp when the active session expires
- created_at: timestamp when the user was created

Notes:
- Passwords are hashed by the Flask application before they are stored.
- The application uses a session cookie after successful login.
- Only one active session per user is allowed.
- Inactivity timeout is configured through `SESSION_TIMEOUT_MINUTES`.
- Users can be created from the registration page or from the terminal helper script.
- Logged-in users can change their own password from the application, except demo users.
- Admin users can access global management tabs.
- User and demo accounts see their own portfolio data.
- The special `admin` user is limited to role management.
- The `demo` user's role is locked in the application.
- Inactive users cannot log in.
