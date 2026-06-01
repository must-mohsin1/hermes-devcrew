---
name: ship-backend-change
description: "Deliver one backend task test-first, in scope, ready for review."
version: 1.0.0
author: hermes-devcrew
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [backend, api, testing, tdd, implementation]
    related_skills: [adversarial-review, onboard-to-codebase]
---

# Ship a Backend Change

Use when implementing a backend task from the board.

## Procedure
1. **Claim & locate.** `hermes kanban claim` → work in the isolated workspace it prints. Re-read
   the task's acceptance criteria.
2. **Map the ground.** Find the relevant module, its tests, and the patterns already in use
   (framework, error handling, validation, naming). Match them.
3. **Test first.** Write a failing test that encodes the acceptance criteria. Run it; watch it
   fail for the right reason.
4. **Implement** the smallest change that makes the test pass. Handle error paths and validate
   inputs at trust boundaries.
5. **Refactor** for clarity once green — small, single-purpose functions.
6. **Verify.** Run the full test suite + linter. No new warnings, no debug leftovers, no secrets.
7. **Hand off.** `hermes kanban complete` with: what changed, files touched, and how you verified
   (commands + result). Keep the diff small for the reviewer.

## Guardrails
- Stay strictly in the task's scope; file new tasks for anything else you notice.
- Never fabricate secrets/endpoints — read config; if missing, `hermes kanban block` with exactly
  what's needed.
