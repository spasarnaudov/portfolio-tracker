# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A native Android client (Kotlin, Jetpack Compose, Material 3) for a Portfolio Tracker
`/api/v1` REST API. `API.md` at the repository root is documented as the source of
truth for the API contract, but it does not currently exist in this checkout — treat
any API-shape assumptions with the caution described in "Known limitations" below and
in `docs/API_INTEGRATION.md`.

## Commands

```bash
./gradlew test                       # JVM unit tests (repositories, validators, interceptors, error parsing)
./gradlew test --tests "*.PortfolioValidatorTest"   # single test class
./gradlew test --tests "*.PortfolioValidatorTest.someMethodName"  # single test method
./gradlew connectedAndroidTest       # Compose UI tests — needs a connected device/emulator
./gradlew assembleDebug              # debug APK -> app/build/outputs/apk/debug/app-debug.apk
./gradlew assembleRelease            # release APK (no signing config configured yet)
./gradlew :app:compileDebugKotlin    # fast compile-only check, no test/packaging
```

Unit tests live under `app/src/test`; Compose UI tests live under `app/src/androidTest`.
Both use hand-built fakes (`testutil/FakeTokenStorage`, `testutil/TestApiServiceFactory`)
and `MockWebServer` instead of the real API — ViewModels/repositories are constructed
directly in tests, no Hilt required, no network/backend needed.
`connectedAndroidTest` compiles but was never executed against a real device/emulator —
don't assume it's a validated merge gate.

Requires JDK 21, Android SDK Platform 36. Gradle wrapper handles the Gradle version
itself (no separate Gradle install needed).

## Architecture

Strict one-way MVVM data flow:

```
Composable screen  →  ViewModel (StateFlow<UiState>)  →  Repository  →  ApiService (Retrofit)
      ↑ observes state                    ↓ ApiResult<T>          ↓ Response<DTO>
```

Screens/ViewModels never call Retrofit directly, and the UI layer never sees a DTO —
repositories map network DTOs to domain models.

- **`core/network`** — `ApiService` (single Retrofit interface for all endpoints),
  request/response DTOs (`core/network/dto`), shared `networkJson`
  (kotlinx.serialization, in `NetworkJson.kt`), `ApiResult`/`AppError` typed
  success/error wrapper (`ApiResult.kt`), `AuthInterceptor` / `UnauthorizedInterceptor`
  OkHttp interceptors, and `DynamicApiServiceHolder`, which rebuilds the entire
  Retrofit/OkHttp stack whenever the configured base URL changes at runtime.
- **`core/data`** — one repository per API area (`AuthRepository`, `AccountRepository`,
  `PortfolioRepository`, `AssetsRepository`, `ChartsRepository`, `AdminRepository`),
  plus pure validators with their own unit tests: `PortfolioValidator`,
  `DateRangeValidator`, `ConnectionUrlValidator`.
- **`core/model`** — immutable domain models (`User`, `Holding`, `ManualItem`,
  `Portfolio`, `Asset`, `AppError`, …).
- **`core/auth`** — `TokenStorage` (interface) / `KeystoreTokenStorage` (Android
  Keystore-backed AES-256/GCM implementation — key never leaves secure hardware),
  `SessionManager` (in-memory current user), `SessionExpiryNotifier` (broadcasts a
  forced logout after any `401` on an authenticated request).
- **`core/storage`** — `SettingsDataStore`, the Preferences DataStore-backed override
  for the API base URL (survives restarts, takes priority over `BuildConfig`).
- **`core/ui`** — shared Compose building blocks (`LineChart` — dependency-free Canvas
  chart, loading/empty/error states, formatters).
- **`core/di`** — Hilt modules: `AppModule`, `NetworkModule`, `StorageBindingsModule`.
- **`feature/*`** — one package per screen area (`login`, `register`, `portfolio`,
  `assets`, `charts`, `account`, `admin`, `connection`, `splash`). Each has its own
  `ViewModel`(s) exposing an immutable `data class ...UiState` via `StateFlow`, plus
  `@Composable` screen(s).
- **`navigation`** — `AppNavHost` (Navigation Compose graph + bottom nav) and
  `Destinations` (route builders).

### API base URL

Never hardcoded into app logic — comes from `BuildConfig.API_BASE_URL`
(`app/build.gradle.kts`, per build type), overridable at runtime via
**Login → Connection settings** (persisted in DataStore, takes priority over
`BuildConfig`). Changing it at runtime rebuilds `DynamicApiServiceHolder` and clears
the local session first — the app never sends a token from one server to another.
Debug builds allow cleartext HTTP (`network_security_config_debug.xml`, debug-only);
release never does.

### Auth flow

- `AuthInterceptor` attaches the token synchronously on every request (in-memory
  `StateFlow` backed by Keystore-encrypted disk storage — no suspend call needed on
  the OkHttp dispatcher thread).
- `UnauthorizedInterceptor`: a `401` on a request that *carried* a token clears the
  token + `SessionManager`, and emits on `SessionExpiryNotifier` (which `AppNavHost`
  collects to navigate back to Login from anywhere). A `401` with **no** token attached
  (e.g. bad login credentials) is left for the caller to handle — nothing to clear.
- No separate refresh/validate call: per the API, any successful authenticated call
  extends the session server-side.
- Force-login: `POST /auth/login` with `force: true` is sent **only** after the user
  confirms a dialog shown for a `409 {"error":{"code":"active_session"}}` response
  (`LoginViewModel.confirmForceLogin`) — never sent speculatively.

### Error handling

Every `ApiService` call goes through `apiCall { ... }` (`core/network/ApiResult.kt`),
turning HTTP responses/exceptions into a typed `ApiResult<T>` / `AppError`
(`BadRequest`, `Unauthorized`, `Forbidden`, `NotFound`, `ActiveSessionConflict`,
`Conflict`, `ValidationFailed`, `ServerError`, `Network`, `Unknown`). Network/IO errors
never clear the token. `AppError` never carries a raw stack trace — messages come from
the server's `error.message`/`details` or a local fallback string. See
`docs/API_INTEGRATION.md` for the full status-code → `AppError` → UI-behavior table.

### Portfolio update semantics (non-obvious contract details)

`PortfolioRepository.updatePortfolio` sends **every** editable holding, not just
changed ones. `quantity == 0` is sent as-is (server treats it as removal — not
filtered client-side). Manual items: existing ones include their numeric `id`; new
ones send `id: null` (kotlinx.serialization has `explicitNulls = true` specifically so
this is never silently omitted — see `NetworkJson.kt`); deleting an existing item sends
`delete: true` with its `id`; an item added and removed within the same edit session
before ever being saved is just dropped. `price_asset_id` and a manually typed
`unit_price` are mutually exclusive in the UI. `PortfolioValidator` rejects negative
quantities/prices and blank manual item names **before** any HTTP call. On success the
ViewModel reloads state from the `PUT` response body directly rather than issuing a
follow-up `GET /portfolio`.

### Decimals and dates

All money/quantity fields are `BigDecimal`, (de)serialized via a custom
`BigDecimalSerializer` that reads/writes JSON numbers as text — values never pass
through `Double`/`Float`. ISO date-times are parsed leniently (offset/`Z` optional —
`LocalDateTimeSerializer.parseFlexible`). `ignoreUnknownKeys = true` and
`coerceInputValues = true` are set so server-side additions/omissions never crash
parsing.

## Known limitations (context for API-shape decisions)

- Several endpoints are **ASSUMED** rather than confirmed against a real spec
  (registration, session validation, account profile/password/deactivate, and all
  `/admin/*` endpoints) — modeled on the conventions of the documented endpoints.
  Every assumed endpoint is flagged in `docs/API_INTEGRATION.md` and at its declaration
  in `ApiService.kt`. Re-verify before relying on the shape.
- "Edit holding" is inline in the Portfolio list (quantity + include-in-chart per row),
  not a separate navigation destination — deliberate, to avoid splitting pending-edit
  state across two ViewModels for a small form.
- `androidx.hilt.navigation.compose:hiltViewModel()` shows as deprecated in this
  toolchain snapshot (replacement not yet in a stable artifact) but is fully functional
  and used by every screen.
- No pagination for admin users/login-history lists — not documented in the API spec.
- Release signing is not configured; `assembleRelease` uses Android Studio's default
  debug signing locally.
