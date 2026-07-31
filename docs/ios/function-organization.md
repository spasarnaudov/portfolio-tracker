# Function Organization

## Purpose

This document defines how Swift functions and methods must be organized in the
iOS app.

It applies to:

- methods on `View` structs, ViewModel classes, shared state types, and
  Core/service types (including `protocol`s and `actor`s);
- free functions;
- closures passed as parameters.

This document defines function organization only.

It does not define architecture, type organization, project-wide naming
conventions, or SwiftUI resource organization.

## Core Principles

1. Every function must have a single responsibility.
2. Functions should be short and easy to understand.
3. Functions must describe behavior through their name.
4. Functions should minimize side effects.
5. Local variables should remain close to their first usage.
6. Guard clauses should be preferred over deep nesting.
7. Duplication should be avoided.
8. Existing project architecture must be preserved.

## Single Responsibility

Each function must perform one logical task.

Prefer:

```swift
private func validateQuantity(_ text: String) -> Double? { ... }
private func buildHoldingRequests() -> [UpdateHoldingRequest] { ... }
func save() async { ... }
```

Avoid a function that mixes genuinely unrelated concerns — validation, persistence,
navigation, and analytics all in one body.

This does not forbid a coordinator function that sequences the steps of one
cohesive workflow — for example, the project's own `LoginViewModel.attemptLogin(force:)`,
which clears error state, sets `isLoading`, calls the API client, and updates
`@Published` state based on the result, all in service of a single login attempt.
That is one responsibility carried out in steps, not multiple unrelated ones.

## Function Size

Functions should remain reasonably small.

A function should be split when multiple independent responsibilities become
visible — for example, `PortfolioViewModel.save()` builds request payloads,
validates input, and calls the API; if this function grows further, extracting
`buildHoldingRequests()`/`buildManualItemRequests()` private helpers would be a
reasonable split.

Do not split a cohesive function solely to reduce line count.

## Parameter Ordering

Parameters should appear in the following order whenever applicable, per Swift's
own API Design Guidelines:

1. Required parameters, ordered so the call reads as a grammatical phrase (as
   `login(username:password:force:)` does)
2. Parameters with default values
3. A trailing closure last, when the function takes one (e.g. a completion
   handler or a SwiftUI `@ViewBuilder` content parameter)

Do not reorder framework-required parameter positions (for example, SwiftUI
modifiers and result builders that require a specific parameter shape).

## Parameter Count

Prefer a small number of parameters.

When several parameters always appear together, consider introducing a dedicated
type — as this project already does with `UpdateHoldingRequest`/
`UpdateManualItemRequest` instead of passing each field separately.

Do not introduce wrapper types solely to reduce parameter count for a function
that only has two or three genuinely independent parameters.

## Return Values

Functions should return meaningful results whenever practical.

Prefer:

```swift
static func isValid(_ candidate: String) -> Bool { ... }
```

instead of setting a side-effect flag the caller has to check separately.

Avoid returning `Void` when the caller naturally expects a result. This does not
apply to functions whose entire purpose is to perform an action rather than
compute one: `@Published` state mutations, navigation actions, and `async`
functions that update ViewModel state as their effect (like `load()` and `save()`
in every ViewModel in this project) all naturally return `Void` and are not a
violation of this rule.

## Early Returns

Guard clauses should be preferred over nested conditions.

Prefer:

```swift
guard let quantity = Double(edit.quantityText), quantity >= 0 else {
    errorMessage = "\(edit.symbol): quantity must be a number that isn't negative."
    return
}
```

over an `if let` that wraps the rest of the function body in a nested block.

Deep nesting should be avoided whenever possible.

## Local Variables and Scope

Variables should be declared as close as possible to their first usage, and kept
in the smallest scope that works — declare a variable inside a `for` loop or
closure when nothing outside that scope needs it.

## Naming

Function names must describe behavior, following Swift's API Design Guidelines:
name a mutating method or one with a side effect as a verb phrase (`load()`,
`save()`, `addManualItem()`), and a non-mutating one that returns a value as a
noun phrase or `is`/`has`-prefixed predicate.

Prefer:

```swift
func load() async
func addManualItem()
func removeManualItem(_ item: ManualItemEdit)
```

Avoid vague names (`process()`, `handle()`, `doStuff()`) unless required by a
protocol conformance.

## Boolean Naming

Boolean properties and functions should clearly communicate their meaning, using
`is`/`has`/`should` prefixes — matching the project's existing `isLoading`,
`isSaving`, `hasLoaded`, `hasVisitedSecondTab`, and `AppSettings.isValid(_:)`.

Avoid unprefixed booleans whose meaning isn't obvious from the name alone
(`valid`, `flag`, `state`).

## Optional and Error Handling

Prefer explicit optional handling — `guard let`/`if let`, or `??` for a default —
over force-unwrapping with `!`. Use `!` only when a `nil` at that point would mean
a programming error, not a runtime condition (for example, a value the compiler
can't prove is non-nil but the surrounding logic guarantees is).

Catch errors only when meaningful recovery or user-facing messaging is possible.
Do not suppress an error silently — an empty `catch {}` block, or a `catch` that
doesn't set an `errorMessage` or otherwise surface the failure, hides real
problems.

A catch-all `catch { ... }` after `try await` also catches `CancellationError`,
which silently breaks Swift's structured concurrency — a `Task` that gets
cancelled (for example, a view disappearing mid-request) will otherwise be treated
as an ordinary failure and shown to the user as an error message, instead of
completing silently as a cancellation should. Every ViewModel's `catch { ... }`
block in this project currently does this — check for cancellation before setting
`errorMessage`:

```swift
} catch is CancellationError {
    // Cancelled (e.g. the view disappeared mid-request) — not a user-facing error.
} catch let error as AppError {
    errorMessage = error.message
} catch {
    errorMessage = error.localizedDescription
}
```

Apply this to new or modified `catch` blocks; it does not require rewriting every
existing one in the same change unless that change already touches it.

## Magic Numbers

Avoid unexplained numeric literals — this project currently has many (`.padding(.vertical, 12)`,
`.padding(.horizontal, 20)`, `cornerRadius: 4`), since no spacing constants exist
yet. See `swiftui-resource-organization.md` for how to extract a repeated or
meaningful value into a named constant once one exists to extract it into.

Do not extract a one-time numeric literal that has no reusable meaning.

## Comments

Well-written code should rarely require explanatory comments. Prefer expressive
names over comments.

Use comments only when they explain business rules, framework limitations,
performance considerations, or non-obvious implementation decisions — matching
this project's own existing comments, for example the note in `LoginView`
explaining why a health-check request fires during `.task` (a Tailscale-only
backend pays for DNS/TLS setup on the first request) or the note in
`PortfolioViewModel` explaining why `PUT /portfolio` always sends every holding
rather than only changed ones.

Do not use comments to describe obvious code.

## Documentation Comments

Use `///` doc comments on public APIs whose behavior is not immediately obvious
from the signature — matching the project's existing doc comments on
`APIClient`, `MaterialColor`, and `MaterialFont`. Private helper functions
normally should not need one.

## Duplication

Avoid duplicated logic. Extract reusable behavior only after duplication becomes
meaningful — do not create an abstraction for a single use case.

## Architecture Preservation

These rules must adapt to the existing project architecture.

An agent must not:

- replace `async`/`await` with completion handlers or Combine without an explicit
  request;
- introduce new abstractions solely to satisfy this document;
- refactor unrelated functions while implementing a local change.

When existing code conflicts with this document, apply these rules only to new or
modified functions unless a broader refactoring is explicitly requested.

## Review Checklist

Before completing a change, verify that:

- every function has a single responsibility (coordinator functions sequencing
  one workflow are not a violation);
- functions are reasonably small;
- guard clauses are used where appropriate;
- parameter count and ordering are reasonable;
- function and boolean names describe behavior per Swift's API Design Guidelines;
- local variables have minimal scope;
- force-unwrap (`!`) is used only where a `nil` would be a programming error;
- `catch` blocks handle `CancellationError` separately instead of surfacing it as
  a user-facing error, for new or modified code;
- magic numbers have been replaced when a named constant already exists to use;
- comments explain only non-obvious behavior;
- duplicated logic has not been introduced;
- the existing project architecture (async/await, manual DI) has not been changed
  without an explicit request.
