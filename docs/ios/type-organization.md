# Type Organization

## Purpose

This document defines how Swift types must be organized in the iOS app.

It applies to:

- SwiftUI `View` structs;
- screen ViewModel classes (`final class ... : ObservableObject`);
- shared, app-wide `ObservableObject` state holders, not tied to one screen (e.g.
  `SessionStore`, `AppSettings`);
- Core/service types with no `@Published` state of their own — plain classes,
  `protocol`s, and `actor`s (e.g. `APIClient`, the `TokenStoring` protocol and its
  `KeychainTokenStorage` actor implementation);
- enum namespaces used for static constants (e.g. `MaterialColor`, `MaterialFont`).

This document defines only type structure.

It does not define architecture, dependency injection, project-wide naming conventions, or SwiftUI resource organization.

## Applicability in This Project

The app has SwiftUI `View` structs, screen ViewModel classes, exactly two shared
app-wide `ObservableObject` state holders (`SessionStore`, `AppSettings`), a small
number of Core/service types (`APIClient`; the `TokenStoring` protocol and its
`KeychainTokenStorage` actor implementation), and enum namespaces (`MaterialColor`,
`MaterialFont`). There is no UIKit view controller, storyboard, or XIB anywhere in
the project — the app is 100% SwiftUI. There is also no dependency-injection
framework: every dependency is passed explicitly through `init`, wired up by hand
starting from `RootView`. There is no test target yet.

**View Organization**, **ViewModel Organization**, **Shared State Type
Organization**, **Core/Service Type Organization**, and **Enum Namespace
Organization** are the sections in active use today. Do not introduce UIKit types,
a DI framework, or a test target to "complete" this document's coverage — those
sections exist only for if such a type is introduced later, on explicit request.

## Core Principles

1. Every type must have a predictable structure.
2. Similar members must remain grouped together.
3. Public API must appear before implementation details.
4. Helper members must remain private unless they belong to the public API.
5. Visibility must be as restrictive as possible.
6. Members inside each section should follow the order that type kind's section
   below defines — not necessarily alphabetical (see Enum Namespace Organization for
   why resource enums here are ordered by role, not alphabetically).
7. Existing project architecture and terminology must be preserved.

## Member Ordering

Unless a more specific section below applies, type members should appear in the
following order:

1. Static constants, if any
2. Property wrappers / stored properties (see the type-specific section for exact
   sub-ordering — this varies by whether the type is a View, a ViewModel, a
   shared state type, or a plain service type)
3. `init`
4. Computed properties
5. Public functions
6. Private helper functions

This is the default ordering for a type that has no more specific structure below.
When a type-specific section (View, ViewModel, Shared State Type, Core/Service
Type, Enum Namespace) applies, that section's ordering takes precedence over this
general list where the two disagree. Note that a `static func` utility (as opposed
to a `static let`/`static var` constant) is ordered by its role — public or private
— alongside the type's other functions, not grouped with static constants; see
`AppSettings.isValid(_:)`, a `static func` positioned with the rest of its public
API, not at the top.

## View Organization

A SwiftUI `View` struct should follow this structure:

1. External dependencies (`@ObservedObject`, `@EnvironmentObject`) — objects owned
   by a parent and passed in
2. Own state (`@StateObject`) — objects this view creates and owns
3. Local UI state (`@State`)
4. `init` (only needed when a `@StateObject` must be built from a passed-in
   dependency, e.g. `_viewModel = StateObject(wrappedValue: LoginViewModel(session: session))`)
5. `body`
6. Private computed subview properties or private helper methods, only once `body`
   has grown large enough that extracting them improves readability

Example, matching the real project's convention:

```swift
struct LoginView: View {
    @ObservedObject var session: SessionStore
    @ObservedObject var settings: AppSettings
    @StateObject private var viewModel: LoginViewModel
    @State private var showConnectionSettings = false

    init(session: SessionStore, settings: AppSettings) {
        self.session = session
        self.settings = settings
        _viewModel = StateObject(wrappedValue: LoginViewModel(session: session))
    }

    var body: some View {
        ...
    }
}
```

No `View` in this project currently extracts private computed subviews or private
helper methods — bodies stay inline. Do not extract them speculatively; only do it
when a specific `body` has become hard to read, per Function Size in
`function-organization.md`.

## ViewModel Organization

A screen ViewModel (`final class ... : ObservableObject`) should follow this
structure:

1. Static constants, if any (e.g. `AssetDetailViewModel.ranges`/`.intervals`,
   `PortfolioHistoryViewModel.ranges`/`.intervals` — static data a screen picks
   from, not injected per instance)
2. `@Published` state (mutable state the view binds to and reads)
3. Private stored properties: non-published private state, then injected
   dependencies
4. `init`
5. Public functions (typically `async`, calling into a Core service type)
6. Private helper functions

Example, matching every ViewModel in the project today:

```swift
@MainActor
final class AssetsViewModel: ObservableObject {
    @Published private(set) var assets: [Asset] = []
    @Published private(set) var isLoading = false
    @Published var errorMessage: String?

    private let session: SessionStore

    init(session: SessionStore) {
        self.session = session
    }

    func load() async {
        ...
    }
}
```

Mark `@Published` properties `private(set)` whenever the view only reads them and
never writes them directly (as `assets` and `isLoading` are above) — reserve plain
`@Published var` for state the view itself mutates (like `errorMessage`, which a
view can clear, or two-way-bound text fields).

This section covers a ViewModel tied to one screen. For a shared, app-wide
`ObservableObject` state holder like `SessionStore` or `AppSettings`, see Shared
State Type Organization below instead.

## Shared State Type Organization

A shared, app-wide `ObservableObject` state holder — not tied to one screen,
unlike a ViewModel — should follow this structure:

1. Nested types, if any (e.g. `SessionStore.Status`)
2. Static constants, if any (e.g. `AppSettings.defaultBaseURL`,
   `AppSettings.overrideKey`)
3. `@Published` state
4. Other stored properties: a dependency this type deliberately exposes to other
   consumers, declared without `private` (e.g. `SessionStore.apiClient`, which
   ViewModels reach through `session.apiClient`), then private dependencies
5. `init`
6. Computed properties
7. Public functions — instance methods and `static func` utilities alike, ordered
   by role, not grouped separately just because one is `static`
8. Private helper functions

Example, matching `SessionStore`:

```swift
@MainActor
final class SessionStore: ObservableObject {
    enum Status {
        case checking
        case loggedOut
        case loggedIn
    }

    @Published private(set) var status: Status = .checking
    @Published private(set) var currentUser: PublicUser?

    let apiClient: APIClient
    private let tokenStorage: any TokenStoring

    init(settings: AppSettings, tokenStorage: any TokenStoring = KeychainTokenStorage()) {
        ...
    }

    func restoreSession() async { ... }
}
```

This project has exactly two such types today: `SessionStore` and `AppSettings`.
Do not introduce a third without an explicit request — state tied to a single
screen belongs in that screen's own ViewModel instead (see ViewModel Organization
above), not in a new shared type.

## Core/Service Type Organization

A Core-layer service type with no `@Published` state of its own — a plain class, a
`protocol`, or an `actor` (e.g. `APIClient`; the `TokenStoring` protocol and its
`KeychainTokenStorage` actor implementation) — should expose public operations
before private implementation:

1. Private stored dependencies (injected via `init`), or — for an `actor` or a
   protocol's concrete implementation — its own private stored state
2. `init`
3. Private computed properties (e.g. `APIClient`'s `decoder`/`encoder`)
4. Public API
5. Private helper functions (e.g. `APIClient`'s `requestJSON`/`send`,
   `KeychainTokenStorage`'s `load`/`query`)

A `protocol` used to define this contract (e.g. `TokenStoring`) declares only the
public API; this ordering otherwise applies to its concrete implementation(s).

## Enum Namespace Organization

An enum used purely as a namespace for static constants (e.g. `MaterialColor`,
`MaterialFont`) should group its `static let`/`static var` members by semantic role,
in the order that role naturally reads — not alphabetically. This matches the
project's real convention:

- `MaterialColor` groups by Material role family: `primary`, `onPrimary`,
  `primaryContainer`, `onPrimaryContainer`, then the `secondary` family, then
  `tertiary`, then `error`, then `background`/`surface`.
- `MaterialFont` groups by type-scale hierarchy: `headlineSmall`, `titleLarge`,
  `titleMedium`, `titleSmall`, `bodyLarge`, `bodyMedium`, `labelLarge`,
  `labelSmall` — largest/most prominent role first.

When adding a new resource enum (for example a future `AppSpacing`), pick the
grouping that makes the scale's own structure legible (e.g. smallest to largest, or
grouped by where a value is used) and stay consistent with it — do not default to
alphabetical here just because other parts of this project's documentation set use
alphabetical ordering for a different kind of file (see
`../android/compose-resource-organization.md` for that unrelated, Kotlin-specific
convention — it does not apply to this document).

## Visibility

Every declaration must use the narrowest Swift access level possible:

Prefer `private` over `fileprivate`, `fileprivate` over `internal`, `internal` over
`public`/`open`, when wider visibility is unnecessary. Most types in this app should
stay `internal` (the default) or `private`/`fileprivate` for their members — nothing
in the app currently needs `public`/`open`, since it's a single app target, not a
framework.

Avoid exposing implementation details: mark a `@Published` property `private(set)`
when only the type itself should mutate it (see ViewModel Organization above).

## MARK Comments

Larger types may use `// MARK: -` section comments to group related members (for
example `// MARK: - Public API`, `// MARK: - Private helpers`). No type in this
project currently uses them — most files are small enough not to need them. Add
them only once a type is large enough that scanning it without section markers is
genuinely hard; do not add them to already-small, already-clear types.

## Architecture Preservation

These rules must adapt to the existing project architecture.

An agent must not:

- introduce a dependency-injection framework, replacing the project's manual
  constructor injection, without an explicit request;
- introduce UIKit view controllers, storyboards, or XIBs without an explicit
  request — the app is 100% SwiftUI today;
- add a test target or test files without an explicit request — none exists today;
- migrate `MaterialColor`/`MaterialFont` to native Asset Catalog colors or Dynamic
  Type without an explicit request — `AccentColor.colorset` exists as an empty
  Xcode-generated placeholder today and is not the app's real color source;
- reorganize unrelated types while implementing a local change.

When existing code conflicts with this document, apply these rules only to new or
modified code unless a broader refactoring is explicitly requested.

## Review Checklist

Before completing a change, verify that:

- member ordering follows the relevant type-specific section (View, ViewModel,
  Shared State Type, Core/Service Type, or Enum Namespace) above;
- public API appears before implementation details;
- `@Published` properties are `private(set)` unless the view genuinely mutates them;
- helper members are private whenever possible;
- visibility is as restrictive as possible;
- resource enum members are grouped by semantic role, not forced into alphabetical
  order;
- MARK comments, if present, are only in types large enough to need them;
- the existing project architecture (manual DI, 100% SwiftUI, no test target) has
  not been changed without an explicit request.
