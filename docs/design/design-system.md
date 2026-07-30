# Design System Requirements — Android App

## Purpose

This document defines what the Android app's visual design system MUST
satisfy. It does not fix a color palette, type scale, or spacing scale — those
are proposed by Claude Design during workflow step 5 in
[`claude-design-workflow.md`](claude-design-workflow.md) and become the actual
design system once approved. This document is the constraint set that
proposal must fit inside.

## Current state

No project-specific design system exists today. The app uses default Material
3 theming with no defined color roles, type scale, spacing scale, or
documented dark theme.

## Target state — requirements

MUST:

- Base the system on Material Design 3 (`MaterialTheme.colorScheme`,
  `.typography`, `.shapes` — see
  [`../android/compose-resource-organization.md`](../android/compose-resource-organization.md)
  for how tokens are expected to be organized in code once defined).
- Define both a light theme and a dark theme.
- Keep text/background color pairs at WCAG AA contrast or better.
- Keep every interactive touch target at 48dp or larger.
- Define a consistent spacing scale and apply it uniformly (no ad-hoc padding
  per screen).
- Define states for interactive components (default, pressed, disabled,
  focused) consistent with Material 3. Unlike colors, typography, and
  spacing, these states normally come from Material 3's own components
  (e.g. `Button`'s `enabled` parameter, its built-in interaction source)
  without needing a separate token file. A custom-drawn interactive element
  still needs its states defined explicitly.
- Fit the existing screen set: login, register, portfolio, assets, charts,
  account, admin, connection, splash (see
  [`../../apps/android/README.md`](../../apps/android/README.md)).

SHOULD:

- Use cards moderately — group genuinely related content, not by default for
  every block.
- Leave generous whitespace; avoid dense layouts.
- Prefer a small number of consistent, reused components over one-off
  variants per screen.

MUST NOT:

- Add decorative effects (gradients, shadows beyond Material 3 elevation,
  glow, unnecessary motion) without a functional reason.
- Copy the specific visual identity of another named app.
- Assume a component or pattern the current app has no data/feature for.

## Mapping to code

Once a design system is approved, its tokens are implemented as Kotlin objects
per [`../android/compose-resource-organization.md`](../android/compose-resource-organization.md)
(`ui/theme/Color.kt`, `Type.kt`, and any new `AppSpacing`/`AppElevations`
files as needed). This document does not define that code structure — only
the design decisions themselves.
