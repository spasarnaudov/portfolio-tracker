# Function Organization

## Purpose

This document defines how Kotlin functions must be organized in Android projects.

It applies to:

- member functions;
- top-level functions;
- extension functions;
- composable helper functions;
- utility functions;
- callback functions;
- lambda expressions.

This document defines function organization only.

It does not define architecture, class organization, naming conventions, Compose resources, or XML resources.

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

```kotlin
private fun validateEmail() {}

private fun validatePassword() {}

private fun submitLogin() {}
```

Avoid:

```kotlin
private fun login() {
    validate()
    savePreferences()
    navigate()
    showToast()
    logAnalytics()
}
```

A function that performs multiple unrelated responsibilities should be split.

This does not forbid a coordinator function that sequences the steps of one cohesive
workflow — for example, a ViewModel's `attemptLogin()`, which reads state, updates
it, launches a coroutine, calls a repository, and updates state again based on the
result, all in service of a single login attempt. That is one responsibility carried
out in steps, not multiple unrelated ones. The anti-pattern above is mixing genuinely
unrelated concerns (validation, persistence, navigation, UI feedback, analytics) in
one function, not calling several steps toward one goal.

## Function Size

Functions should remain reasonably small.

A function should be split when multiple independent responsibilities become visible.

Do not split a cohesive function solely to reduce line count.

## Function Ordering

Class member functions are first grouped by visibility, per Member Ordering in
`class-organization.md` (public functions, then internal, then private helpers).
Within each visibility band, functions should be further ordered by responsibility.
This is a secondary ordering inside a band — for example, inside "Public functions" —
not a replacement for the visibility-based grouping.

Recommended order within a band:

1. User interaction
2. Navigation
3. Validation
4. Formatting
5. Mapping

Functions within the same responsibility group are further ordered alphabetically,
per `class-organization.md`'s Core Principle on alphabetical ordering — unless an
established UI/data-flow order already exists for that group (see
`class-organization.md`'s Alphabetical Ordering section), in which case that order
takes precedence.

Related functions should remain together.

## Parameter Ordering

Parameters should appear in the following order whenever applicable.

1. Required business parameters
2. Modifier (Compose only) — the first optional parameter, immediately after the
   required ones, per the official Jetpack Compose API guidelines
3. Other optional parameters (with default values)
4. Callback parameters

Do not reorder framework-required parameters.

## Parameter Count

Prefer a small number of parameters.

When several parameters always appear together, consider introducing a dedicated model.

Prefer:

```kotlin
updateProfile(profile)
```

instead of

```kotlin
updateProfile(
    firstName,
    lastName,
    age,
    email,
    phone,
    address
)
```

Do not introduce wrapper objects solely to reduce parameter count.

## Return Values

Functions should return meaningful results whenever practical.

Prefer:

```kotlin
val isValid = validateInput()
```

instead of

```kotlin
validateInput()

if (error == null) { ... }
```

Avoid returning `Unit` when the caller naturally expects a result.

This rule does not apply to functions whose entire purpose is to perform an action
rather than compute one: event handlers (`onUsernameChange()`), callbacks, state
mutations (`_uiState.update { ... }`), navigation actions, and `@Composable`
functions all naturally return `Unit` and are not a violation of this rule.

## Early Returns

Guard clauses should be preferred over nested conditions.

Prefer:

```kotlin
if (!isLoggedIn) {
    return
}

loadProfile()
```

Avoid:

```kotlin
if (isLoggedIn) {

    loadProfile()

}
```

Deep nesting should be avoided whenever possible.

## Local Variables

Variables should be declared as close as possible to their first usage.

Prefer:

```kotlin
val profile = repository.load()

render(profile)
```

Avoid:

```kotlin
val profile: Profile

...

profile = repository.load()

...

render(profile)
```

Variables should not remain unused for long sections of code.

## Variable Scope

Keep variable scope as small as possible.

Declare variables inside loops or conditionals when they are not needed elsewhere.

Avoid unnecessarily widening scope.

## Naming

Function names must describe behavior.

Prefer:

```text
calculatePrice()
formatDate()
loadProfile()
navigateHome()
observeState()
validateInput()
```

Avoid:

```text
action()
calculate()
data()
doStuff()
execute()
helper()
process()
run()
```

unless required by the framework.

## Boolean Naming

Boolean functions should clearly communicate their meaning.

Prefer:

```text
canSubmit()
hasPermission()
isConnected()
isValid()
shouldRefresh()
```

Avoid:

```text
check()
flag()
status()
test()
```

## Null Handling

Prefer explicit null handling.

Use:

```kotlin
value ?: return
```

instead of deeply nested null checks.

Avoid unnecessary use of `!!`.

Use `!!` only when the value is guaranteed by program logic.

## Side Effects

Functions should minimize unexpected side effects.

Avoid functions that simultaneously:

- modify state;
- update UI;
- perform navigation;
- write to storage;
- send analytics;
- perform networking.

Separate unrelated responsibilities whenever practical.

## Exception Handling

Catch exceptions only when meaningful recovery is possible.

Do not suppress exceptions silently.

Prefer:

```kotlin
runCatching {

}
```

when it improves readability.

In coroutine or `suspend` code, `runCatching` also catches `CancellationException`,
which silently breaks structured concurrency (a cancelled `viewModelScope`, for
example, would be treated as an ordinary failure instead of propagating). Re-throw it:

```kotlin
runCatching {
    repository.load()
}.onFailure {
    if (it is CancellationException) throw it
}
```

Avoid empty catch blocks.

## Expression Bodies

Use expression bodies only for simple functions.

Prefer:

```kotlin
fun isLoggedIn() = session != null
```

Use block bodies when logic becomes more complex.

## Lambda Organization

Keep lambda bodies concise.

Extract reusable logic into named private functions when lambdas become difficult to read.

Avoid deeply nested lambdas.

## Nested Functions

Nested functions should be rare.

Use them only when the helper has meaning exclusively inside the parent function.

Otherwise, create a private function.

## Magic Numbers

Avoid unexplained numeric literals.

Prefer:

```kotlin
delay(LoginScreenDefaults.ErrorAnimationDurationMillis)
```

instead of

```kotlin
delay(250)
```

Do not extract one-time numeric literals that have no reusable meaning.

## Comments

Well-written code should rarely require explanatory comments.

Prefer expressive names over comments.

Use comments only when they explain:

- business rules;
- framework limitations;
- performance considerations;
- non-obvious implementation decisions.

Do not use comments to describe obvious code.

Avoid:

```kotlin
// Increment counter

counter++
```

## KDoc

Public APIs should use KDoc when their behavior is not immediately obvious.

Private helper functions normally should not use KDoc.

Avoid documenting implementation details.

## Duplication

Avoid duplicated logic.

Extract reusable behavior only after duplication becomes meaningful.

Do not create abstractions for a single use case.

## Architecture Preservation

These rules must adapt to the existing project architecture.

An agent must not:

- move business logic between architectural layers without an explicit request;
- replace synchronous code with asynchronous code without an explicit request;
- introduce new abstractions solely to satisfy this document;
- refactor unrelated functions while implementing a local change.

When existing code conflicts with this document, apply these rules only to new or modified functions unless broader refactoring is explicitly requested.

## Review Checklist

Before completing a change, verify that:

- every function has a single responsibility;
- functions are reasonably small;
- guard clauses are used where appropriate;
- parameter count is reasonable;
- function names describe behavior;
- boolean names are meaningful;
- local variables have minimal scope;
- unnecessary side effects have been avoided;
- magic numbers have been replaced when appropriate;
- exception handling is meaningful;
- expression bodies are used only for simple functions;
- nested functions are justified;
- comments explain only non-obvious behavior;
- duplicated logic has not been introduced;
- the existing project architecture has not been changed without an explicit request.
