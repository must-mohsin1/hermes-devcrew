---
name: ship-frontend-change
description: "Deliver one frontend task: accessible, on-system, tested, in scope."
version: 1.0.0
author: hermes-devcrew
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [frontend, ui, accessibility, components, testing]
    related_skills: [adversarial-review, onboard-to-codebase]
---

# Ship a Frontend Change

Use when implementing a UI task from the board.

## Procedure
1. **Claim & locate.** `hermes kanban claim` → work in the isolated workspace it prints. Re-read
   the acceptance criteria.
2. **Reuse the system.** Find the existing component library, design tokens, and patterns. Reuse
   before you build. Don't introduce a new visual style unless the task says so.
3. **Build the states.** Implement the happy path *and* loading, empty, error, long-content, and
   small-screen states.
4. **Accessibility pass.** Semantic markup, keyboard navigation, visible focus, labels/alt text,
   adequate contrast.
5. **Test.** Add component/interaction tests for the new behavior. Run them.
6. **Verify.** Lint, typecheck, run tests. Capture a screenshot if it helps the reviewer.
7. **Hand off.** `hermes kanban complete` with what changed, how you verified, and any before/after
   notes. Keep diffs small.

## Guardrails
- Coordinate on the API contract; don't invent backend shapes — confirm with the architect/backend.
- Stay in scope; unrelated UI debt becomes a new task.
