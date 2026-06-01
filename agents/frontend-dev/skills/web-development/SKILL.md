---
name: web-development
description: "Framework-agnostic reference for building correct, accessible, performant web UI."
version: 1.0.0
author: hermes-devcrew
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [frontend, web, react, vue, accessibility, performance, css]
    related_skills: [ship-frontend-change, adversarial-review]
---

# Web Development Reference

Apply when implementing or reviewing any web UI. Framework-agnostic — adapt to whatever the
project already uses (React, Vue, Svelte, plain DOM). Reuse the project's stack; don't introduce
a new framework.

## Principles
- **Semantic HTML first.** Use the right element (`button`, `a`, `nav`, `label`, headings) before
  reaching for `div` + ARIA. The platform gives you behavior and accessibility for free.
- **Component architecture.** Small, single-purpose, composable components. Props in, events out.
  Lift state only as far as it must go; colocate state with the component that owns it.
- **Data fetching.** Handle the four states every async UI has: loading, success, empty, error.
  Cancel/ignore stale responses. Never render undefined as content.
- **Forms.** Controlled inputs, validation at the boundary, clear inline errors, disabled submit
  while pending, and keyboard submit. Preserve user input on failure.
- **Accessibility (non-negotiable).** Keyboard reachable + visible focus, labels for every input,
  alt text, sufficient contrast, `aria-*` only to fill gaps semantics can't. Test with the keyboard.
- **Performance.** Avoid unnecessary re-renders (stable keys, memoize hot paths), lazy-load heavy
  routes/assets, debounce expensive input handlers, ship the smallest bundle that works.
- **Responsive & resilient.** Mobile-first; test small screens, long content, and slow networks.
- **Match the design system.** Use existing tokens/components; never hardcode `#fff`/`#000` or a
  one-off font/color when a token exists.

## Checklist before "done"
- [ ] Semantic markup; keyboard path works; focus visible
- [ ] Loading / empty / error / long-content states implemented
- [ ] Component/interaction tests added and passing
- [ ] No console errors/warnings; no layout shift on load
- [ ] Reuses design tokens & existing components
