---
name: design-critique
description: "Critique a UI against the design system; find issues and prescribe specific fixes."
version: 1.0.0
author: hermes-devcrew
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [design, critique, review, ui, polish]
    related_skills: [design-system, accessibility-review]
---

# Design Critique

Use to review a built or proposed UI for quality and consistency.

## What you check
1. **Hierarchy** — one clear focal point; size/weight/contrast guide the eye.
2. **Rhythm & spacing** — consistent scale; grid alignment; whitespace doing work.
3. **Consistency** — matches tokens/components; no one-off colors or fonts.
4. **Type** — readable measure and line-height; sensible scale.
5. **Color & contrast** — restrained palette; AA contrast; intentional accent use.
6. **States** — empty / loading / error / hover / focus designed, not default.
7. **AI-slop smell** — generic gradient hero, `system-ui`, evenly-gray cards.

## How you respond
- Prioritized findings (blocking → polish). Each: what's wrong, the **principle**, and the
  **specific fix** — e.g. "H1 reads flat: raise to 2.5rem / line-height 1.1 and add 24px below."
- Never "make it pop." Name the change so `devcrew-frontend-dev` can implement it directly.

## Done when
A prioritized, actionable critique that maps each issue to a concrete fix.
