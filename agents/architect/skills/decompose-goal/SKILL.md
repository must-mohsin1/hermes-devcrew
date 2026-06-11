---
name: decompose-goal
description: "Turn a goal into a verifiable kanban task graph with owners and acceptance criteria."
version: 1.1.0
author: hermes-devcrew
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [planning, decomposition, kanban, architecture, orchestration]
    related_skills: [adversarial-review, integrate-and-synthesize]
---
<!-- Doctrine rule: any edit to this file MUST bump the minor version — drift detection across profile copies depends on it. -->

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
   leave the rest independent so they run in parallel. **Reviewer, QA, and integrator lanes
   are NOT independent** — see the dep rule below.
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

## Reviewer / QA / integrator dep rule (REQUIRED)

The reviewer, QA, and integrator lanes are **not** parallel workers. They are
downstream gates (`team.yaml`: verifier, dynamic-verifier, synthesizer). If
you wire them as siblings of the implementation tasks, they run while the
code is still being written and produce "this code doesn't exist yet"
findings.

Implementation cards are siblings unless one consumes another's output —
never chain them by default. The designer card is upstream of frontend
implementation cards only.

**Mandatory dep graph for any build with >3 implementation tasks:**

```
T-design (designer) ──► frontend impl cards only

T1 (impl) ──┐
T2 (impl) ──┤   all implementation cards run in PARALLEL;
 …          ┼─► each one is a parent of BOTH gates
TN (impl) ──┘
        ▼                      ▼
  T14-Reviewer (static)   T15-QA (dynamic)      ← parallel gates
        └───────────┬──────────┘
                    ▼
        T16-Integrator (parents: T14 AND T15; the orchestrator expands
                        this at runtime with every fix card the gates create)
```

Concretely, for every implementation card Tn:

- `hermes kanban link Tn T14` AND `hermes kanban link Tn T15` — one card per
  call (multi-id link is silent on latter ids; loop per-id).
- Integrator: `hermes kanban link T14 T16` and `hermes kanban link T15 T16`.
- Remember FIRST_ARG = PARENT: `link A B` makes A the parent of B.

**When a build has 3 or fewer implementation tasks**, the gates may be
parented on the last impl card only; the integrator still depends on both
gates.

**Ownership discipline (mirrors the devcrew-run briefing):** every card body
MUST list the exact files it creates or modifies under a `Files:` line.
Shared wiring files — barrel/index files, route registries, package.json,
lockfiles, shared config — belong ONLY to the integrator card, which runs
after the gates. Workers must not edit files outside their card's `Files:`
list; anything extra becomes a follow-up card.

**Why this matters:** without the rule, the gates run in parallel with the
impl cards and produce false-positive findings; with it, both gates see
complete code, the integrator sees gated code, and the build stays parallel
where it is safe (the impl cards) and serial only where it must be.
