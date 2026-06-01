---
name: decompose-goal
description: "Turn a goal into a verifiable kanban task graph with owners and acceptance criteria."
version: 1.0.0
author: hermes-devcrew
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [planning, decomposition, kanban, architecture, orchestration]
    related_skills: [adversarial-review, integrate-and-synthesize]
---

# Decompose a Goal into a Task Graph

Use when a new goal arrives and the crew needs a plan it can execute autonomously.

## Procedure
1. **Understand reality.** Read the target repo/workspace. Note the stack, entry points, tests,
   and constraints. Do not plan against unverified assumptions.
2. **State the definition of done** for the whole goal in one or two sentences. If you can't,
   the goal is too vague — create a blocked clarification task and stop.
3. **Slice into tasks.** Each task: one outcome, one owner, testable, finishable in a short
   session. Split anything larger.
4. **Assign owners** by specialty: `devcrew-backend-dev`, `devcrew-frontend-dev`,
   `devcrew-devops`, `devcrew-domain-expert`.
5. **Write acceptance criteria** per task — concrete and checkable, so `devcrew-reviewer` can
   verify without taste.
6. **Wire dependencies.** `hermes kanban link <parent> <child>` only where order truly matters;
   leave the rest independent so they run in parallel.
7. **Flag risk.** Mark migrations, auth, irreversible or networked actions for extra review.

## Fast path: one-shot swarm
For a self-contained goal, create the whole worker→verifier→synthesizer graph at once:

```bash
hermes kanban swarm "<goal>" \
  --created-by devcrew-architect \
  --worker devcrew-backend-dev:"<task>" \
  --worker devcrew-frontend-dev:"<task>" \
  --verifier devcrew-reviewer \
  --synthesizer devcrew-integrator
```

## Done when
Every task has an owner, acceptance criteria, and correct dependencies; the board is ready for
the dispatcher to run.
