---
name: codebase-research
description: "Investigate an unfamiliar codebase systematically before changing or advising on it."
version: 1.0.0
author: hermes-devcrew
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [research, codebase, investigation, onboarding, architecture]
    related_skills: [onboard-to-codebase, decompose-goal]
---

# Codebase Research

Use to build accurate, evidence-based understanding of a project before acting — and to answer
"how does X work here?" without guessing.

## Procedure
1. **Map the territory.** Read README, CONTRIBUTING, and any `docs/`. List top-level dirs and what
   each owns. Identify the build/test/run commands and the dependency manifest.
2. **Find the entry points.** CLI mains, server bootstraps, route tables, job schedulers. Trace
   from "what runs first" inward.
3. **Follow the data.** Pick one real request/operation and trace it end to end: input → validation
   → business logic → storage → response. Note the seams between layers.
4. **Read the tests.** Tests document intended behavior and edge cases faster than prose. Find the
   test for the area you care about before reading the implementation.
5. **Use history as evidence.** `git log`/`git blame` on a file reveals *why* code is the way it is.
   Recent churn flags active or fragile areas.
6. **Extract invariants & glossary.** What must never break (data contracts, auth boundaries,
   ordering)? Which domain terms have precise local meaning? Write them down.
7. **Verify, don't assume.** Confirm a hypothesis by running code, reading the test, or grepping
   for callers — cite the file:line evidence, not memory.

## Output
A short, durable brief — wired into this profile's `SOUL.md` PROJECT CONTEXT block — covering:
stack, where things live, invariants, glossary, gotchas, and the definition of done. Keep it
current as the code evolves.
