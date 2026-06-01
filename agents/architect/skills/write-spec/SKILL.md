---
name: write-spec
description: "Turn a fuzzy goal into a crisp spec: problem, goals, non-goals, acceptance criteria."
version: 1.0.0
author: hermes-devcrew
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [spec, planning, requirements, architecture, scope]
    related_skills: [decompose-goal, writing-plans]
---

# Write a Spec

Use when a goal is vague or large, **before** decomposing it into tasks. A good spec makes the
task graph — and the reviewer's job — objective.

## The spec (keep it short; scale to the goal)
1. **Problem** — what's broken/missing and for whom. One or two sentences.
2. **Goal** — the single outcome that means success.
3. **Non-goals** — what's explicitly out of scope (kills scope creep before it starts).
4. **Constraints** — stack, compatibility, performance/security budgets, deadlines.
5. **Acceptance criteria** — concrete, checkable statements; each maps to a test or a verifiable
   observation. If you can't make it checkable, it isn't a criterion yet.
6. **Risks / unknowns** — anything that needs a `spike` before committing.

## Rules
- **YAGNI:** cut every requirement not needed for the goal.
- Every acceptance criterion must be verifiable by `devcrew-reviewer` without taste.
- If the goal hides multiple independent deliverables, say so and split into separate specs.

## Output
A short spec (a kanban task description, or a `docs/` file) that `decompose-goal` can turn directly
into owned, testable tasks with clear acceptance criteria.
