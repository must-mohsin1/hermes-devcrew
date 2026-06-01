---
name: onboard-to-codebase
description: "Build and maintain deep project context so the crew acts on local reality."
version: 1.0.0
author: hermes-devcrew
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [onboarding, domain, codebase, context, conventions]
    related_skills: [ship-backend-change, ship-frontend-change]
---

# Onboard to a Codebase

Use right after install (to customize this agent for a project) and whenever the project changes
in ways the crew must know.

## First-run: capture the project
1. **Survey.** Read the repo: README, build/test/lint commands, entry points, module layout,
   config, CI. Note the real stack and versions.
2. **Find the invariants.** What must never break? Domain rules, data contracts, security
   boundaries, performance budgets.
3. **Collect the glossary.** Domain terms the crew must use correctly and consistently.
4. **Record the gotchas.** Footguns, flaky areas, and "looks wrong but is intentional" spots.
5. **Write it down.** Fill the `PROJECT CONTEXT` block in this profile's `SOUL.md`. That block is
   loaded every turn — it's what makes this agent an expert. Keep it current.

## Per-task (acting as a worker)
- Claim one ready task (`hermes kanban claim`), work in the isolated workspace, and keep changes
  consistent with the captured conventions.
- Flag — via comment or `hermes kanban block` — when a generic approach would violate a project
  invariant, and propose the project-correct path.
- `hermes kanban complete` with a summary + verification; the reviewer still gates your work.

## Done when
The `PROJECT CONTEXT` in `SOUL.md` is accurate and rich enough that the rest of the crew makes
project-correct decisions without rediscovering them.
