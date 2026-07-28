# Compose Resource Organization

## Purpose

This document defines how UI values must be named, grouped, and organized in Android projects that use Jetpack Compose.

It covers:

* user-visible strings;
* colors;
* dimensions;
* spacing;
* text sizes;
* typography;
* shapes;
* elevations;
* animation durations;
* shared design-system values;
* screen-specific UI constants.

This document applies only to Jetpack Compose code. It must not be used to migrate a project to XML layouts or the Android View system.

## Core Principles

1. Static, app-authored user-visible text must use Android string resources.
2. Shared design values must use the project theme or design system.
3. Screen-specific values must remain close to the screen that owns them.
4. Repeated or meaningful UI literals must be replaced with named values.
5. Names must describe purpose rather than numeric value.
6. Values inside resource groups and Kotlin objects must be ordered alphabetically.
7. Existing project architecture and terminology must be preserved.
8. Values must not be moved between XML resources, theme definitions, and Kotlin objects unless explicitly requested.

## Screen Definition

A screen is a single user-visible navigation destination.

Each independently navigable destination must be treated as a separate screen, even when several screens belong to the same feature.

Examples:

```text
Login
Profile
Admin Users
Admin Logs
Admin Log Details
```

Corresponding Kotlin object names:

```text
LoginScreenDimens
ProfileScreenDimens
AdminUsersScreenDimens
AdminLogsScreenDimens
AdminLogDetailsScreenDimens
```

Do not place unrelated nested destinations inside a generic object such as:

```text
AdminScreenDimens
```

A shared feature-level object may be used only when its values genuinely apply to multiple screens in that feature.

## User-Visible Strings

All user-visible text must use Android string resources.

Use:

```kotlin
Text(
    text = stringResource(R.string.screen_login_title)
)
```

Do not use:

```kotlin
Text(
    text = "Login"
)
```

This rule applies to:

* titles;
* labels;
* buttons;
* hints;
* static error copy (for example, the app-authored fallback text a validation
  message falls back to);
* empty states;
* accessibility descriptions;
* dialog content;
* menu items;
* notifications;
* formatted messages;
* pluralized messages.

Technical values that are not shown to users do not belong in string resources.

This rule does not apply to dynamic runtime content, which cannot be a string
resource because it doesn't exist until the app is running: usernames, asset or item
names, server-provided error messages (for example, an `AppError`'s own `message`
field shown via `errorMessage ?: stringResource(R.string.screen_portfolio_error_fallback)`), other database or
API content, log output, and user-entered text. Only the static, app-authored
fallback/label text around such values belongs in a string resource — the dynamic
value itself is passed in as a formatting argument (see Plurals and Formatted Strings
below) or displayed as received.

## String Naming

Screen-specific string resources must use lowercase `snake_case`.

Recommended format:

```text
screen_<screen_name>_<element>_<purpose>
```

`<element>` may be omitted when the resource describes the screen as a whole rather
than one of its elements (for example `screen_login_title`).

Examples:

```text
screen_admin_logs_empty_message
screen_admin_logs_title
screen_login_button_login
screen_login_email_label
screen_login_password_error
screen_login_title
```

Shared strings must use the `common_` prefix.

Examples:

```text
common_action_cancel
common_action_confirm
common_action_retry
common_error_unknown
```

Names must describe the purpose of the string, not its current text.

Use:

```xml
<string name="screen_login_button_login">Login</string>
```

Do not use:

```xml
<string name="login_text">Login</string>
<string name="text_login">Login</string>
```

## String Grouping

Strings in `strings.xml` must be grouped by screen.

Each group must begin with a comment containing the human-readable screen name.

```xml
<resources>

    <!-- Common -->

    <string name="common_action_cancel">Cancel</string>
    <string name="common_action_retry">Retry</string>

    <!-- Admin Logs Screen -->

    <string name="screen_admin_logs_empty_message">No logs available</string>
    <string name="screen_admin_logs_title">Logs</string>

    <!-- Login Screen -->

    <string name="screen_login_button_login">Login</string>
    <string name="screen_login_email_label">Email</string>
    <string name="screen_login_password_label">Password</string>
    <string name="screen_login_title">Login</string>

</resources>
```

The `Common` group must appear first.

Screen groups must be ordered alphabetically by their human-readable screen names.

## String Ordering

Strings inside each group must be ordered alphabetically by the complete value of the `name` attribute.

Correct:

```xml
<!-- Login Screen -->

<string name="screen_login_button_login">Login</string>
<string name="screen_login_email_label">Email</string>
<string name="screen_login_password_label">Password</string>
<string name="screen_login_title">Login</string>
```

Incorrect:

```xml
<!-- Login Screen -->

<string name="screen_login_title">Login</string>
<string name="screen_login_password_label">Password</string>
<string name="screen_login_button_login">Login</string>
```

Ordering must not use the displayed text.

## Plurals and Formatted Strings

Quantity-dependent text must use plural resources.

```xml
<plurals name="screen_notifications_message_count">
    <item quantity="one">%d message</item>
    <item quantity="other">%d messages</item>
</plurals>
```

Use:

```kotlin
pluralStringResource(
    R.plurals.screen_notifications_message_count,
    messageCount,
    messageCount
)
```

Formatted text must remain in string resources.

```xml
<string name="screen_profile_greeting">Hello, %1$s</string>
```

Use:

```kotlin
stringResource(
    R.string.screen_profile_greeting,
    userName
)
```

Do not build user-visible sentences by concatenating hardcoded strings in Kotlin.

## Theme and Design-System Values

Application-wide design values must use the project theme or design system.

This includes:

* application colors;
* typography;
* shapes;
* shared spacing;
* shared elevations;
* reusable component styling;
* standard animation durations.

Use existing project abstractions before creating new ones.

Examples:

```kotlin
MaterialTheme.colorScheme.primary
MaterialTheme.colorScheme.surface
MaterialTheme.shapes.medium
MaterialTheme.typography.bodyLarge
```

Do not create screen-specific aliases for existing theme values unless the alias introduces meaningful screen-specific semantics.

Use:

```kotlin
color = MaterialTheme.colorScheme.error
```

Avoid:

```kotlin
val LoginErrorColor = MaterialTheme.colorScheme.error
```

when the value has no unique meaning on the login screen.

## Screen-Specific Values

A UI value used only by one screen must remain near that screen.

Recommended object names:

```text
<ScreenName>ScreenColors
<ScreenName>ScreenDefaults
<ScreenName>ScreenDimens
<ScreenName>ScreenShapes
<ScreenName>ScreenTypography
```

Use only the objects required by the screen.

Do not create empty or single-purpose objects merely to match a fixed template.

Example:

```kotlin
internal object LoginScreenDimens {

    val ButtonHeight = 48.dp
    val ContentPadding = 16.dp
    val FormSpacing = 12.dp
    val LogoSize = 96.dp
    val TitleBottomPadding = 24.dp
}
```

Properties inside each object must be ordered alphabetically by property name.

## Naming Kotlin Values

Kotlin UI value names must describe purpose rather than numeric value.

Correct:

```kotlin
val ContentPadding = 16.dp
val FormSpacing = 12.dp
val TitleTextSize = 24.sp
```

Incorrect:

```kotlin
val Padding16 = 16.dp
val Size24 = 24.sp
val Space12 = 12.dp
```

A name must remain correct when the underlying value changes.

Follow this project's existing capitalization convention for these values: upper
camel case, precedented in `ui/theme/Color.kt` (`val Purple80 = Color(0xFFD0BCFF)`):

```kotlin
val ContentPadding = 16.dp
```

Do not mix `ContentPadding` and `contentPadding` conventions within the same project.

This casing rule applies only to properties holding deeply-immutable design constants
(dimensions, colors, durations, and similar values covered by this document), and is
this project's own convention, not the official Kotlin one — the official Kotlin
coding conventions specify `SCREAMING_SNAKE_CASE` (for example `MAX_COUNT`) for
`const val` and other true compile-time constants; upper camel case there is reserved
for class/object names and for properties holding singleton-like objects. Follow the
project's upper-camel-case precedent for the design-token values covered by this
document; use standard `SCREAMING_SNAKE_CASE` for an actual `const val` elsewhere.
Regular stateful properties (for example `uiState`, `binding`) and all function names
are unaffected and always use standard lower camel case, per `class-organization.md`
and `function-organization.md`.

## Dimensions and Spacing

Repeated or semantically important `dp` values must not remain as literals inside composable functions.

Use:

```kotlin
Modifier.padding(LoginScreenDimens.ContentPadding)
```

Do not use:

```kotlin
Modifier.padding(16.dp)
```

Extract values that define:

* screen content padding;
* spacing between major sections;
* component sizes;
* minimum touch targets;
* recurring margins;
* dialog dimensions;
* list spacing;
* card dimensions;
* image or icon dimensions.

A one-time literal may remain inline only when all of the following are true:

* it is used once;
* it has no reusable design meaning;
* it does not affect consistency with other elements;
* naming it would reduce readability.

The exception must not be used for primary screen spacing or repeated dimensions.

## Text Sizes and Typography

Application-wide text styling must use `MaterialTheme.typography` or the existing project typography system.

Use:

```kotlin
Text(
    text = stringResource(R.string.screen_login_title),
    style = MaterialTheme.typography.headlineMedium
)
```

Do not declare direct `sp` values when an existing typography style already represents the intended design.

Screen-specific typography may be introduced only when the shared typography system does not cover the required design.

```kotlin
internal object ChartScreenTypography {

    val AxisLabelSize = 11.sp
    val ValueLabelSize = 13.sp
}
```

Properties must be alphabetically ordered.

Do not duplicate an existing theme typography style under a screen-specific name.

## Colors

Application-wide colors must use `MaterialTheme.colorScheme` or the project design system.

Use:

```kotlin
color = MaterialTheme.colorScheme.onSurface
```

Do not scatter direct `Color(...)` declarations across composable functions.

Screen-specific colors may use a dedicated object when they represent concepts not covered by the global color scheme.

```kotlin
internal object ChartScreenColors {

    val NegativeValue = Color(0xFFC62828)
    val PositiveValue = Color(0xFF2E7D32)
}
```

The property names must describe semantic meaning.

Use:

```kotlin
val PositiveValue = Color(0xFF2E7D32)
```

Do not use:

```kotlin
val green = Color(0xFF2E7D32)
val color2 = Color(0xFF2E7D32)
```

Do not move two colors into a shared object only because their hexadecimal values currently match.

## Shapes

Shared shapes must use `MaterialTheme.shapes` or the existing design system.

Use:

```kotlin
shape = MaterialTheme.shapes.medium
```

Screen-specific shapes may be stored in a dedicated object.

```kotlin
internal object LoginScreenShapes {

    val Form = RoundedCornerShape(16.dp)
    val Logo = CircleShape
}
```

Shape properties must be ordered alphabetically.

Do not create a screen-specific alias for a theme shape without additional semantic value.

## Elevations

Repeated or meaningful elevations must use named values.

```kotlin
internal object LoginScreenDefaults {

    val CardElevation = 4.dp
}
```

Shared elevations should belong to the application design system.

```kotlin
internal object AppElevations {

    val Dialog = 8.dp
    val RaisedCard = 4.dp
}
```

Do not extract an elevation merely because another unrelated component uses the same numeric value.

## Animation Values

Animation durations, delays, thresholds, and other behaviorally meaningful animation values must be named.

```kotlin
internal object LoginScreenDefaults {

    val ErrorAnimationDurationMillis = 250
    val SuccessAnimationDelayMillis = 150
}
```

Do not scatter unexplained numbers such as `150`, `250`, or `300` across animation code.

Use plain `val`, not `const val`, here: these are design-token values covered by
Naming Kotlin Values' upper-camel-case convention above, not true compile-time
constants. Marking them `const` would put them under the official Kotlin
`SCREAMING_SNAKE_CASE` convention for constants instead (see Naming Kotlin Values) —
which is what every real `const val` in this project already uses (for example
`AUTOSAVE_DEBOUNCE_MS`). None of the usages here require a compile-time constant.

The unit must be clear from the property name when the type does not express it.

Use:

```kotlin
val ErrorAnimationDurationMillis = 250
```

Avoid:

```kotlin
val ErrorAnimationDuration = 250
```

unless the type or API makes the unit unambiguous.

## Shared Values

Values genuinely reused by multiple screens must be stored in a shared design-system object.

Examples:

```text
AppAnimationDurations
AppComponentDefaults
AppElevations
AppSpacing
```

Example:

```kotlin
internal object AppSpacing {

    val ExtraLarge = 32.dp
    val Large = 24.dp
    val Medium = 16.dp
    val Small = 8.dp
}
```

Properties must be alphabetically ordered.

A value may become shared only when it represents the same design decision and purpose across multiple screens.

Do not move values into a shared object only because they currently have the same numeric value.

## Component-Specific Values

Values owned by a reusable component should remain with that component instead of being assigned to a screen.

Example:

```kotlin
internal object PrimaryButtonDefaults {

    val ContentPadding = PaddingValues(
        horizontal = 24.dp,
        vertical = 12.dp
    )

    val MinimumHeight = 48.dp
}
```

Use component-specific values when:

* the component is reused across screens;
* the value is part of the component contract;
* changing the value should affect every use of the component.

Do not place screen layout values inside reusable component defaults.

## Modifier Organization

Complete `Modifier` chains should not normally be stored as constants.

Prefer:

```kotlin
Modifier
    .fillMaxWidth()
    .padding(LoginScreenDimens.ContentPadding)
```

Avoid:

```kotlin
val loginContentModifier = Modifier
    .fillMaxWidth()
    .padding(16.dp)
```

Reusable modifier behavior may be implemented as a modifier extension when it represents meaningful shared behavior.

```kotlin
fun Modifier.screenContentPadding(): Modifier =
    padding(AppSpacing.Medium)
```

Do not create modifier extensions only to hide a single literal or shorten one call site.

## File Organization

Screen-specific values should remain in the feature or screen package that owns them.

Example:

```text
feature/
└── login/
    ├── LoginScreen.kt
    ├── LoginScreenDefaults.kt
    ├── LoginScreenDimens.kt
    ├── LoginScreenShapes.kt
    └── LoginViewModel.kt
```

Small screens may keep related values in the screen file when separate files would make navigation harder.

Example:

```kotlin
private object LoginScreenDimens {

    val ContentPadding = 16.dp
    val FormSpacing = 12.dp
}
```

Shared theme and design-system values should remain in the existing theme or design-system package.

The project's theme package currently contains:

```text
ui/
└── theme/
    ├── Color.kt
    ├── Theme.kt
    └── Type.kt
```

New shared abstractions introduced by this document (`AppElevations`, `AppShapes`,
`AppSpacing`, and similar) belong in that same package, in their own file named after
the abstraction — for example `ui/theme/Elevation.kt` for `AppElevations`, or
`ui/theme/Spacing.kt` for `AppSpacing`. Do not create these files speculatively; add one
only when the corresponding shared value is actually introduced.

Do not create a parallel package when the project already has an authoritative location for these values.

## Alphabetical Ordering

Properties inside resource objects must be ordered alphabetically by property name unless execution order is materially important.

Correct:

```kotlin
internal object LoginScreenDimens {

    val ButtonHeight = 48.dp
    val ContentPadding = 16.dp
    val FormSpacing = 12.dp
    val LogoSize = 96.dp
}
```

Incorrect:

```kotlin
internal object LoginScreenDimens {

    val LogoSize = 96.dp
    val ContentPadding = 16.dp
    val ButtonHeight = 48.dp
    val FormSpacing = 12.dp
}
```

Different value categories should normally use separate focused objects instead of comment-separated sections inside one large object.

## Allowed Inline Values

The following values may remain directly in Kotlin code:

* framework-required constants;
* algorithmic constants unrelated to rendering;
* values used only in calculations;
* temporary test values;
* one-time trivial UI literals without reusable design meaning.

The exception must not be used for:

* user-visible text;
* repeated spacing;
* primary screen padding;
* repeated dimensions;
* direct repeated colors;
* shared typography;
* shared shapes;
* elevations with design meaning;
* animation values with behavioral meaning.

## Architecture Preservation

These rules must adapt to the existing project architecture.

An agent must not:

* migrate Compose values to XML dimension or color resources without an explicit request;
* replace an existing design system with new screen objects;
* duplicate theme values in screen-specific files;
* create a new resource abstraction when an equivalent one already exists;
* reorganize unrelated screens while implementing a local change.

When existing code conflicts with this document, apply the rules to new or modified code unless a broader migration is explicitly requested.

## Review Checklist

Before completing a change, verify that:

* all static, app-authored user-visible text uses string resources (dynamic runtime
  content — usernames, asset/item names, server-provided messages, database/API
  content, logs, user-entered text — is exempt, see User-Visible Strings);
* strings are grouped by screen;
* string groups are alphabetically ordered;
* strings inside each group are alphabetically ordered by resource name;
* shared strings use the `common_` prefix;
* shared colors use the theme or design system;
* shared typography uses the project typography system;
* shared shapes use the theme or design system;
* screen-specific values remain near their screen;
* reusable component values remain with their component;
* repeated or meaningful `dp` and `sp` literals are named;
* direct `Color(...)` values are not scattered across composables;
* meaningful elevations and animation values are named;
* values inside Kotlin objects are alphabetically ordered;
* names describe purpose rather than numeric value;
* shared values are not duplicated;
* unrelated values are not moved into shared objects;
* the existing project architecture has not been changed without an explicit request.
