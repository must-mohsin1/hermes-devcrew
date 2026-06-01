---
name: qa-testing
description: "Systematically test a running app, file reproducible bugs, drive the fix-verify loop."
version: 1.0.0
author: hermes-devcrew
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [qa, testing, bugs, regression, quality]
    related_skills: [page-agent, verification-before-completion]
---

# QA Testing

Use to verify a feature/app dynamically — by running it, not reading it.

## Procedure
1. **Scope & tier.** From the acceptance criteria, list the flows to test. Prioritize: critical
   (blocks use) → high → medium → cosmetic.
2. **Establish health.** Get the app running (or hit the deployed URL/API). Confirm the happy path
   works before hunting edge cases.
3. **Attack the seams.** Per flow: invalid/empty/huge inputs, error paths, auth/permission
   boundaries, concurrency, slow/offline network, small viewports.
4. **File reproducible bugs.** Each: title, steps to reproduce, expected vs. actual, severity,
   environment, evidence (output / screenshot path / log). No repro → not a bug yet.
5. **Drive the loop.** `hermes kanban create` a fix task for the owner with the repro; after the
   fix, **re-run the exact repro** and confirm resolved + no regression.
6. **Score it.** Pass/fail per tier + a one-line ship / no-ship verdict.

## Tools
Drive the UI with the `page-agent` skill; hit APIs with curl/httpie; run the project's own test
suite as a baseline before manual exploration.

## Done when
Every acceptance criterion is exercised, open bugs are filed with repros, and you've given a clear
ship-readiness verdict backed by evidence.
