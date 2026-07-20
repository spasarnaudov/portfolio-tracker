# Portfolio Tracker — Android

A native Android client for the Portfolio Tracker `/api/v1` REST API (see
[`API.md`](API.md) at the repository root — it is the source of truth for every
endpoint this app calls). Built with Kotlin, Jetpack Compose and Material 3.

## Architecture

MVVM with a strict one-way data flow and a repository layer between the UI and the
network:

```
Composable screen  →  ViewModel (StateFlow<UiState>)  →  Repository  →  ApiService (Retrofit)
      ↑ observes state                    ↓ ApiResult<T>          ↓ Response<DTO>
```

- **`core/network`** — the `ApiService` Retrofit interface, request/response DTOs
  (`core/network/dto`), a shared `networkJson` (kotlinx.serialization) configuration,
  `ApiResult`/`AppError` for typed success/error handling, the `AuthInterceptor` /
  `UnauthorizedInterceptor` OkHttp interceptors, and `DynamicApiServiceHolder`, which
  rebuilds the Retrofit/OkHttp stack when the configured base URL changes.
- **`core/data`** — one repository per API area (`AuthRepository`, `AccountRepository`,
  `PortfolioRepository`, `AssetsRepository`, `ChartsRepository`, `AdminRepository`),
  plus pure, unit-tested validators (`PortfolioValidator`, `DateRangeValidator`,
  `ConnectionUrlValidator`). Repositories map network DTOs to domain models — the UI
  layer never sees a DTO.
- **`core/model`** — immutable domain models (`User`, `Holding`, `ManualItem`,
  `Portfolio`, `Asset`, `AppError`, …).
- **`core/auth`** — `TokenStorage` (interface) / `KeystoreTokenStorage` (the Android
  Keystore-backed implementation), `SessionManager` (in-memory current user),
  `SessionExpiryNotifier` (broadcasts a forced logout after a `401`).
- **`core/storage`** — `SettingsDataStore`, the Preferences DataStore-backed override
  for the API base URL.
- **`core/ui`** — shared Compose building blocks (`LineChart`, loading/empty/error
  states, formatters) and a small dependency-free Canvas line chart.
- **`core/di`** — Hilt modules (`AppModule`, `NetworkModule`, `StorageBindingsModule`).
- **`feature/*`** — one package per screen area (`login`, `register`, `portfolio`,
  `assets`, `charts`, `account`, `admin`, `connection`, `splash`), each with its own
  `ViewModel`(s) + `@Composable` screen(s). ViewModels expose an immutable
  `data class ...UiState` via `StateFlow`; screens never call Retrofit directly.
- **`navigation`** — `AppNavHost` (Navigation Compose graph + bottom navigation) and
  `Destinations` (route builders).

## Technologies

- Kotlin 2.0, Jetpack Compose (Material 3), Navigation Compose
- Hilt (dependency injection), Kotlin Coroutines + `StateFlow`
- Retrofit + OkHttp, kotlinx.serialization (JSON)
- Jetpack DataStore (Preferences) for the connection-settings override
- Android Keystore (`AndroidKeyStore` + AES/GCM) for the Bearer token — see
  [Token storage](#token-storage) below
- JUnit4 + MockWebServer (unit tests), Compose UI Test (instrumented tests)

## Requirements

- Android Studio with support for AGP 9.0.x / Kotlin 2.0 (a current release channel)
- JDK 21
- Android SDK Platform 36, Build-Tools 36.x
- `minSdk = 26`, `compileSdk = targetSdk = 36`

The Gradle wrapper (`./gradlew`) downloads Gradle 9.1.0 automatically; you do not need
Gradle installed separately.

## Configuring the API base URL

The base URL is **never hardcoded** into application logic — it comes from
`BuildConfig.API_BASE_URL`, generated per build type in `app/build.gradle.kts`:

| Build type | Default `API_BASE_URL` | Cleartext (HTTP) |
|---|---|---|
| `debug` | `http://piglet:5000/api/v1/` | Allowed (see [`network_security_config_debug.xml`](app/src/debug/res/xml/network_security_config_debug.xml), debug-only) |
| `release` | `https://api.example.com/api/v1/` (placeholder — change before shipping) | **Not allowed** anywhere in the app |

To point at your own server without touching Kotlin code:

1. Edit the `buildConfigField("String", "API_BASE_URL", "\"...\"")` line for the
   relevant build type in `app/build.gradle.kts`, **or**
2. Run the app, open **Login → Connection settings**, type a base URL (must start with
   `http://` or `https://` and end with `/`), and tap **Test connection** then **Save**.
   A DataStore-persisted override always takes priority over `BuildConfig.API_BASE_URL`
   and survives app restarts. **Reset to default** clears the override.

Changing the base URL at runtime rebuilds the Retrofit/OkHttp client
(`DynamicApiServiceHolder`) and, if you were signed in, clears the local session first
(a confirmation dialog explains why) — the app never sends a token from one server to
another.

## Running the app

1. Open the project root in Android Studio and let it sync.
2. Make sure a device/emulator can reach your API base URL (for the debug default,
   that means a host reachable as `piglet` on your network, or edit Connection
   Settings after first launch).
3. Run the `app` debug configuration.

## Tests

```bash
./gradlew test                  # JVM unit tests (repositories, validators, interceptors, error parsing)
./gradlew connectedAndroidTest  # Compose UI tests — needs a connected device/emulator
```

Unit tests live under `app/src/test`; Compose UI tests live under `app/src/androidTest`.
Both use hand-built fakes/`MockWebServer` instead of hitting the real API, and
ViewModels/repositories are constructed directly in tests (no Hilt required there),
so no network access or backend is needed to run them.

## Debug build

```bash
./gradlew assembleDebug
```

Produces `app/build/outputs/apk/debug/app-debug.apk`. Cleartext HTTP is allowed only in
this build type, scoped to the debug network security config.

## Release build

```bash
./gradlew assembleRelease
```

Before shipping:

- Change the `release` build type's `API_BASE_URL` in `app/build.gradle.kts` to your
  real HTTPS endpoint.
- Configure a real signing config (this project ships without one — Android Studio's
  default debug signing is used for local `assembleRelease` runs).
- The release manifest never sets `usesCleartextTraffic="true"` and does not reference
  the debug network security config, so plain HTTP is rejected everywhere.

## Using a local HTTP development server

The default debug `API_BASE_URL` (`http://piglet:5000/api/v1/`) assumes a server
reachable by hostname on your LAN. If that doesn't resolve from your device, open
**Connection settings** and enter an IP-based address instead, e.g.
`http://192.168.1.50:5000/api/v1/`, then **Test connection** before **Save**.
`app/src/debug/res/xml/network_security_config_debug.xml` permits cleartext traffic
in debug builds only.

## Using an HTTPS production server

Set (or override via Connection Settings) an `https://` base URL. No cleartext
exception applies outside of debug builds; the OS's standard TLS/certificate
validation is used as-is — this app never disables SSL/TLS verification.

## Token storage

The Bearer token is encrypted with an AES-256/GCM key generated inside the Android
Keystore (`core/auth/KeystoreTokenStorage`) — the key material never leaves secure
hardware, so the ciphertext persisted in SharedPreferences is useless without the
originating device. The token is:

- attached automatically to every request via `AuthInterceptor`;
- cleared automatically when a protected request comes back `401`
  (`UnauthorizedInterceptor` + `SessionExpiryNotifier` route the app back to Login);
- cleared on logout, account deletion, and when the connection base URL changes;
- never written to logs, analytics, or crash reports (the debug `HttpLoggingInterceptor`
  is capped at `BASIC` level — method/URL/response code only — and explicitly redacts
  the `Authorization` header).

`core/auth/TokenStorage` is an interface specifically so tests can substitute an
in-memory fake instead of touching the real Android Keystore (which isn't available on
a plain JVM).

## Known limitations

- **API.md does not fully specify the contract.** It documents health/auth/portfolio
  update semantics and error shapes in detail, but points to a `openapi.yaml` for the
  complete contract, which was not available while building this app. Registration,
  session validation/refresh, account (profile/change-password/deactivate), and *all*
  admin endpoints are therefore modeled on plausible REST conventions rather than a
  confirmed spec. Every assumed endpoint is called out explicitly in
  [`docs/API_INTEGRATION.md`](docs/API_INTEGRATION.md) — verify each one against the
  real server (or a future `openapi.yaml`) before shipping.
- **"Edit holding" is inline, not a separate screen.** Holdings are edited directly in
  the Portfolio list (quantity field + include-in-chart checkbox per row) rather than
  via a dedicated navigation destination, to avoid splitting the same pending-edit
  state across two screens/ViewModels for a very small form.
- **`androidx.hilt.navigation.compose:hiltViewModel()` is flagged deprecated** by this
  toolchain snapshot (moved to a package not yet published in any stable artifact this
  project could pin). It's still fully functional; every screen in this app uses it.
  Revisit once the replacement ships in a stable `androidx.hilt` release.
- **`connectedAndroidTest` was written but not executed** in the environment this app
  was built in (no attached device/emulator). The tests compile
  (`./gradlew compileDebugAndroidTestKotlin`) and follow the same patterns validated by
  the 54 passing JVM unit tests; run them on a real device/emulator before relying on
  them as a merge gate.
- **No pagination** is implemented for admin users/login-history lists, since API.md
  doesn't document pagination parameters for any endpoint.
- **Release signing** is not configured — `assembleRelease` uses Android Studio's
  default debug signing locally; wire up a real signing config before distributing a
  release build.
