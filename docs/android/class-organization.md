# Class Organization

## Purpose

This document defines how Kotlin classes must be organized in Android projects.

It applies to:

- Activity classes;
- Fragment classes;
- ViewModel classes;
- Service classes;
- BroadcastReceiver classes;
- Worker classes;
- Custom View classes;
- Dialog classes;
- helper classes;
- manager classes;
- repository classes;
- use case classes;
- reusable UI classes.

This document defines only class structure.

It does not define architecture, dependency injection, naming conventions, Compose organization, or XML resources.

## Applicability in This Project

This project currently has ViewModel and Repository classes only. It has no Fragment,
Service, BroadcastReceiver, Worker, Custom View, or use case classes, and a single
Activity (`MainActivity`) that only hosts Compose content — it has no View Binding,
Activity Result Launchers, or menu callbacks.

**ViewModel Organization** and **Repository Organization** are the sections in active
use today. The Activity, Fragment, Service, Worker, BroadcastReceiver, Custom View, and
Use Case sections apply only if a class of that kind is introduced later — do not use
them to justify restructuring `MainActivity` or adding classes that don't otherwise
belong in this project.

## Core Principles

1. Every class must have a predictable structure.
2. Similar members must remain grouped together.
3. Public API must appear before implementation details.
4. Lifecycle methods must appear before event handlers.
5. Helper methods must remain private unless they belong to the public API.
6. Visibility should be as restrictive as possible.
7. Members inside each section must be ordered alphabetically unless execution order requires otherwise.
8. Existing project architecture and terminology must be preserved.

## Member Ordering

Unless the project already defines another convention, class members must appear in the following order.

1. Companion object
2. Constants (declared inside the companion object from step 1, not a separate location)
3. Dependency injection
4. Public properties
5. Internal properties
6. Private properties
7. Initialization (`init`)
8. Lifecycle methods
9. Public functions
10. Protected functions
11. Internal functions
12. Private helper functions
13. Member extension functions (see Extension Functions below — only when a member extension is actually needed)

Example:

```kotlin
class LoginFragment : Fragment() {

    companion object {

        private const val RequestCode = 100
    }

    @Inject
    lateinit var loginRepository: LoginRepository

    private lateinit var binding: FragmentLoginBinding

    override fun onCreate(...) {}

    override fun onViewCreated(...) {}

    fun submit() {}

    private fun validateInput() {}

    private fun updateUi() {}
}
```

## Activity Organization

Activities should follow this structure.

1. Companion object
2. Injected dependencies
3. View Binding
4. State properties
5. Activity Result Launchers
6. Lifecycle methods
7. Menu callbacks
8. Navigation
9. Public API
10. Private helper methods

Example lifecycle ordering:

```text
onCreate()
onStart()
onResume()
onPause()
onStop()
onDestroy()
```

Lifecycle methods must remain together.

## Fragment Organization

Fragments should follow this structure.

1. Companion object
2. Injected dependencies
3. View Binding
4. Adapters
5. State
6. Lifecycle methods
7. UI initialization
8. Observers
9. Click listeners
10. Navigation
11. Public API
12. Private helper methods

Recommended lifecycle order:

```text
onAttach()
onCreate()
onCreateView()
onViewCreated()
onStart()
onResume()
onPause()
onStop()
onDestroyView()
onDestroy()
onDetach()
```

## ViewModel Organization

Recommended structure:

1. Companion object
2. Dependencies
3. Mutable state
4. Public state
5. Initialization
6. Public API
7. Private business logic
8. Private helper methods

Example:

```kotlin
private val _state = MutableStateFlow(...)

val state = _state.asStateFlow()
```

Private mutable state must appear immediately before the corresponding public state.

## Service Organization

Recommended order:

1. Companion object
2. Dependencies
3. Binder
4. State
5. Lifecycle
6. Public API
7. Private helpers

## Worker Organization

Recommended order:

1. Companion object
2. Dependencies
3. Constructor properties
4. doWork()
5. Private helper methods

The main worker function should appear before helper methods.

## BroadcastReceiver Organization

Recommended order:

1. Companion object
2. Dependencies
3. onReceive()
4. Private helper methods

## Custom View Organization

Recommended order:

1. Constructors
2. Initialization
3. Public API
4. Drawing
5. Layout
6. Touch handling
7. Animation
8. Private helper methods

## Repository Organization

Repositories should expose public operations before private implementation.

Recommended order:

1. Dependencies
2. Public API
3. Cache helpers
4. Database helpers
5. Network helpers
6. Mapping helpers

## Use Case Organization

A use case should expose only its execution entry point before helper methods.

Recommended order:

1. Dependencies
2. invoke()
3. Private helper methods

## Method Grouping

Methods performing similar responsibilities should remain together.

Examples:

- UI initialization
- Observer registration
- Click listeners
- Navigation
- Validation
- Formatting
- Mapping

Avoid mixing unrelated responsibilities.

Correct:

```text
initializeToolbar()
initializeRecyclerView()
initializeViews()

observeLogin()
observeLoading()

navigateToHome()
navigateToSettings()
```

## Method Naming

Method names must describe behavior.

Prefer:

```text
loadProfile()
navigateToHome()
observeState()
validateInput()
```

Avoid:

```text
doWork()
execute()
method1()
helper()
```

unless those names are required by overridden framework methods.

## Visibility

Every declaration must use the narrowest visibility possible.

Prefer:

```kotlin
private
```

over

```kotlin
internal
```

Prefer

```kotlin
internal
```

over

```kotlin
public
```

when wider visibility is unnecessary.

Avoid exposing implementation details.

## Extension Functions

Extension functions should normally be declared at file/top level, outside any class.
Top-level extension functions are not class members and are not subject to the Member
Ordering rules above.

Use member extension functions only when they require access to private members. A
member extension function is a class member and belongs at position 13 of Member
Ordering (last, after private helper functions).

## Companion Object

A companion object should contain only:

- constants;
- factory methods;
- object creation helpers.

Avoid storing mutable runtime state inside a companion object.

## Constants

Constants must be grouped together inside the class's companion object.

Example:

```kotlin
companion object {

    private const val AnimationDurationMillis = 250
    private const val RequestCode = 100
}
```

Constants should be ordered alphabetically.

## Alphabetical Ordering

Members inside the same logical section must be ordered alphabetically unless execution order requires another arrangement.

Correct:

```text
hideLoading()
navigateHome()
showError()
showLoading()
```

Incorrect:

```text
showLoading()
hideLoading()
navigateHome()
showError()
```

## Region Comments

Large classes may use section comments.

Example:

```kotlin
// Lifecycle

// Initialization

// Observers

// Click Listeners

// Navigation

// Helpers
```

Comments should identify responsibility rather than implementation details.

Do not create unnecessary sections in small classes.

## File Size

Large classes should be split when they contain multiple unrelated responsibilities.

Do not split a cohesive class solely to reduce line count.

## Architecture Preservation

These rules must adapt to the existing project architecture.

An agent must not:

- move business logic between architectural layers without an explicit request;
- convert Activities into Fragments;
- convert Fragments into Compose screens;
- move lifecycle logic into helper classes without an explicit request;
- reorganize unrelated code while implementing a local change.

When existing code conflicts with this document, apply these rules only to new or modified code unless a broader refactoring is explicitly requested.

## Review Checklist

Before completing a change, verify that:

- member ordering follows this document;
- lifecycle methods remain grouped together;
- similar methods remain grouped together;
- public API appears before implementation details;
- helper methods are private whenever possible;
- visibility is as restrictive as possible;
- constants are grouped together;
- members inside each section are alphabetically ordered;
- unrelated responsibilities are not mixed;
- extension functions are placed appropriately;
- the existing project architecture has not been changed without an explicit request.
