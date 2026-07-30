# UX Guidelines — Android App

## Purpose

General UX rules that apply to every screen, independent of that screen's
specific content. Screen-specific decisions belong in that screen's brief
(see [`screen-brief-template.md`](screen-brief-template.md)), not here.

## Information hierarchy

MUST:

- Give every screen one clear primary action.
- Distinguish primary actions from secondary actions visually (e.g. filled
  vs. outlined/text button), not only by position.
- Order content by what the user needs first, not by data-model order.

## Navigation

MUST:

- Keep the existing bottom-navigation structure and screen set unless a
  navigation change is explicitly requested and approved — see
  [`claude-design-workflow.md`](claude-design-workflow.md).
- Make the current location within the app always visible.

## Required screen states

Every screen that loads or submits data MUST define, and Claude Design MUST
present, all of the following states before a screen counts as designed:

- Loading
- Empty (no data, not an error)
- Error (with a retry action where retrying makes sense)
- Success (the normal populated state)

Do not treat "success" as the only state a screen needs.

## Accessibility

MUST:

- Meet WCAG AA text contrast (see [`design-system.md`](design-system.md)).
- Keep touch targets at 48dp minimum.
- Provide a content description for every icon-only interactive element.
- Not rely on color alone to convey meaning (e.g. positive/negative values
  also need a shape or label cue, not just red/green).

## Responsive behavior

MUST:

- Design layouts to hold up across common Android phone widths (compact to
  medium width classes); do not assume one fixed screen size.
- Avoid fixed pixel-based layouts that break on smaller or larger devices.

## Copy

MUST:

- Keep user-facing copy short and specific to the action (per
  [`../android/compose-resource-organization.md`](../android/compose-resource-organization.md)'s
  string-resource rules for how it is implemented).

MUST NOT:

- Introduce copy for features the app does not have.
