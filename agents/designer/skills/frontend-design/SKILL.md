---
name: frontend-design
description: "Produce distinctive, production-grade UI — avoid generic AI-template aesthetics."
version: 1.0.0
author: hermes-devcrew
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [frontend, design, ui, aesthetics, polish, accessibility]
    related_skills: [ship-frontend-change, web-development]
---

# Frontend Design

Use when building or restyling UI that should look intentional and on-brand — not like a generic
template.

## Principles
- **Honor the existing design system first.** Tokens, type scale, spacing, components. Consistency
  beats novelty. If a `DESIGN.md` or token set exists, it is the source of truth — don't deviate
  without approval.
- **Avoid AI slop.** No default purple→blue gradient hero, no `system-ui` everywhere, no row of
  evenly-gray rounded cards. Make deliberate choices: a real type pairing, a color used with
  intent, asymmetry where it earns attention.
- **Hierarchy & rhythm.** One clear focal point per view. A consistent spacing scale (4/8px
  rhythm). Align to a grid. Let whitespace do work.
- **Type.** A readable body (size / line-height / ~60–75ch measure) and a display face with
  personality. Two families max.
- **Color.** A restrained palette with one confident accent; check contrast (WCAG AA). Avoid pure
  `#000`/`#fff` if the system defines softer ink/paper.
- **Motion.** Purposeful and fast (150–250ms); respects `prefers-reduced-motion`. Motion clarifies
  state — it doesn't decorate.
- **Detail polish.** Designed empty/loading/error states, visible focus, hover affordances,
  aligned icons, zero layout shift on load.

## Checklist
- [ ] Uses the project's tokens/components; no one-off hardcoded colors/fonts
- [ ] Clear focal hierarchy; consistent spacing scale; grid alignment
- [ ] AA contrast; reduced-motion respected; focus visible
- [ ] Empty / loading / error states intentionally designed
- [ ] Looks deliberate — would pass a designer's glance, not read as "obviously AI"
