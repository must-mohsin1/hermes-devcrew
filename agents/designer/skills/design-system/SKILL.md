---
name: design-system
description: "Define and maintain the design system: tokens, type, color, spacing, motion, components."
version: 1.0.0
author: hermes-devcrew
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [design, design-system, tokens, branding, ui]
    related_skills: [design-critique, frontend-design, design-reference]
---

# Design System

Use to establish or evolve the product's visual language as a reusable system.

## Procedure
1. **Understand** the product, audience, and desired tone. Look at the landscape; pick a direction
   with intent (not a default template). Prefer the **`design-reference`** skill to pull a matching,
   coherent system from Refero as your starting point instead of inventing from scratch.
2. **Define tokens.** Color (semantic roles: bg / surface / ink / accent / success-warn-error),
   type scale, spacing scale (4/8 rhythm), radii, shadows, motion durations + easing.
3. **Type.** A readable body face + a display face with personality (max two families); set scale,
   line-height, and measure (~60–75ch).
4. **Color.** A restrained palette with one confident accent and semantic roles; verify AA contrast.
5. **Components.** Document the core set (button, input, card, nav) with all states.
6. **Record it** in `DESIGN.md` as the source of truth; provide a font + color preview.

## Rules
- Tokens over hardcoded values. Consistency over novelty. AA contrast minimum.
- Evolve deliberately and note the rationale for changes.

## Done when
`DESIGN.md` captures tokens + type + color + spacing + motion + components, and `devcrew-frontend-dev`
can build from it without guessing.
