---
name: accessibility-review
description: "Audit UI for WCAG accessibility: semantics, keyboard, contrast, focus, motion, forms."
version: 1.0.0
author: hermes-devcrew
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [accessibility, a11y, wcag, ux, inclusive]
    related_skills: [design-critique, frontend-design]
---

# Accessibility Review

Use to check that a UI is usable by everyone, before it ships.

## Checklist (WCAG-aligned)
- **Semantics** — correct elements (`button`/`a`/`nav`/headings/landmarks); logical heading order.
- **Keyboard** — every interactive element reachable + operable; visible focus; sane order; no traps.
- **Contrast** — text ≥ 4.5:1 (AA); large text / UI components ≥ 3:1.
- **Labels** — inputs labeled; images have `alt`; icon-only controls have accessible names.
- **Motion** — respects `prefers-reduced-motion`; no flashing/seizure risk.
- **Forms** — errors announced and associated with fields; required state conveyed non-visually.
- **Dynamic** — live regions for async updates; focus managed on route/modal changes.

## How you respond
- List violations by severity with the element and the fix; cite the criterion. Re-check after fixes.

## Done when
The flow passes the checklist (keyboard + semantics + contrast at minimum) or open issues are filed
with concrete fixes.
