# Screen Brief Template

Claude Design MUST present every screen using this template before it can be
approved. Copy this template per screen; do not skip a section — write "N/A"
with a reason if a section genuinely does not apply.

```markdown
## Screen: <name>

### Purpose
What this screen is for.

### Primary user task
The single main thing a user comes to this screen to do.

### Information hierarchy
What appears first, second, third, and why.

### Primary action
The one main action on this screen.

### Secondary actions
Other actions available, and how they're visually de-emphasized vs. the
primary action.

### Components used
Which reusable components this screen uses (see design-system.md for the
constraints they must satisfy, and
../android/compose-resource-organization.md's Component-Specific Values
section for how approved components are organized in code).

### States
- Loading:
- Empty:
- Error:
- Success:

### Light theme
(mockup or description)

### Dark theme
(mockup or description)

### Accessibility
- Text/background contrast: confirm WCAG AA or note the risk.
- Touch targets: confirm every interactive element is 48dp or larger.
- Content descriptions: list every icon-only interactive element and its description.
- Color-independence: how meaning is conveyed without relying on color alone
  (e.g. for positive/negative values).

### Responsive behavior
How this layout holds up across compact-to-medium width classes, or why a
single layout works for both.

### UX rationale
Why the layout/choices above serve the primary task.

### Open questions / assumptions requiring approval
Anything Claude Design assumed or is unsure about — listed explicitly, not
silently decided.
```
