---
name: adversarial-review
description: "Verify a completed task adversarially; approve only what you can confirm."
version: 1.0.0
author: hermes-devcrew
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [review, verification, security, quality, gate]
    related_skills: [ship-backend-change, integrate-and-synthesize]
---

# Adversarial Review

Use to verify a worker's completed task before it reaches the integrator. Posture: try to
**break it**, not bless it. Default to "not approved" when uncertain.

## Procedure
1. **Re-read the contract.** Pull the task's acceptance criteria. Verify against those, not vibes.
2. **Correctness.** Trace the logic against the requirement. Don't trust the summary. Run the
   tests; read them — do they assert real behavior, or pass vacuously?
3. **Security.** Hostile-input mindset: injection, authz/authn gaps, secret leakage, SSRF, path
   traversal, unsafe deserialization, dependency/supply-chain risk.
4. **Edge cases.** Error paths, empty/huge inputs, concurrency, partial failure.
5. **Footprint.** In scope? Diff minimal? Any dead code, debug logs, stray TODOs, or fabricated
   secrets?
6. **Fit.** Matches the codebase's patterns, or bolted-on foreign code?

## Verdict
- **Pass** → comment what you verified (so the sign-off is auditable), then mark it verified.
- **Fail** → `hermes kanban block` with specific, actionable findings: file, line, the problem,
  and what "fixed" looks like. Bounce it to the owner; do not fix it yourself.

A clean review that found nothing must still state *what was checked* to earn the pass.
