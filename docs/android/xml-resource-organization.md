# XML Resource Organization

## Purpose

This document defines how Android XML resources must be named, grouped, and organized in projects that use the Android View system.

It applies to XML resources such as:

* `strings.xml`
* `colors.xml`
* `dimens.xml`
* `integers.xml`
* `bools.xml`
* `styles.xml`

This document does **not** apply to Jetpack Compose projects. Compose projects should follow `compose-resource-organization.md`.

## Resource Extraction

UI values must be stored as Android resources whenever an appropriate resource type exists.

This includes:

* user-visible text;
* colors;
* dimensions;
* spacing;
* margins;
* padding;
* text sizes;
* icon sizes;
* corner radii;
* elevations;
* animation durations;
* arrays;
* integers;
* booleans.

Do not hardcode user-visible text, colors, or UI dimensions in XML layouts or Java/Kotlin source code.

## Screen Definition

A screen is a single user-visible destination.

Nested destinations should use hierarchical screen names.

Examples:

```text
screen_login_
screen_profile_
screen_admin_users_
screen_admin_logs_
screen_admin_log_details_
```

## Resource Naming

Screen-specific resources must use lowercase `snake_case` and begin with:

```text
screen_<screen_name>_
```

Recommended format:

```text
screen_<screen_name>_<element>_<purpose>
```

Examples:

```text
screen_buy_button_confirm
screen_buy_title
screen_login_button_login
screen_login_email_hint
screen_login_form_spacing
screen_login_title_text_color
```

Names must describe the purpose of the resource rather than its value.

Correct:

```xml
<dimen name="screen_login_content_padding">16dp</dimen>
```

Incorrect:

```xml
<dimen name="padding_16">16dp</dimen>
```

## Grouping by Screen

Resources must be grouped by screen.

Each group must begin with a comment containing the screen name.

```xml
<!-- Buy Screen -->

<string name="screen_buy_button_ok">OK</string>
<string name="screen_buy_title">Buy screen</string>

<!-- Login Screen -->

<string name="screen_login_button_login">Login</string>
<string name="screen_login_title">Login screen</string>
```

Screen groups must be ordered alphabetically by screen name.

## Ordering Within a Screen

Resources inside each screen group must be ordered alphabetically by the complete resource name.

Correct:

```xml
<!-- Login Screen -->

<string name="screen_login_button_login">Login</string>
<string name="screen_login_email_hint">Email</string>
<string name="screen_login_password_hint">Password</string>
<string name="screen_login_title">Login</string>
```

Ordering must always use the `name` attribute.

## Shared Resources

Resources used by multiple screens must not be duplicated.

Shared resources must be placed in a `Common` section and use the `common_` prefix.

```xml
<!-- Common -->

<string name="common_action_cancel">Cancel</string>
<string name="common_action_retry">Retry</string>
<dimen name="common_button_height">48dp</dimen>
```

The `Common` section must appear before all screen sections.

A resource should only be moved to `Common` when it represents the same purpose across multiple screens.

Resources that happen to share the same value but have different meanings should remain screen-specific.

## Resource File Structure

Resources should remain in the standard Android resource files.

```text
res/
└── values/
    ├── bools.xml
    ├── colors.xml
    ├── dimens.xml
    ├── integers.xml
    ├── strings.xml
    └── styles.xml
```

Each resource file must follow the same grouping and ordering rules.

## Allowed Exceptions

The following values may remain directly in code:

* Android framework constants;
* algorithmic constants;
* non-UI technical constants;
* temporary test values.

Layout behavior values such as `match_parent`, `wrap_content`, and `0dp` may remain directly in XML.

## Review Checklist

Before completing a change, verify that:

* user-visible text is stored in string resources;
* colors are stored in color resources;
* UI dimensions are stored in dimension resources;
* resources are grouped by screen;
* screen groups are alphabetically ordered;
* resources inside each screen group are alphabetically ordered;
* shared resources are not duplicated;
* resource names describe purpose rather than value.
