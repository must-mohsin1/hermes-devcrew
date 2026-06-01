---
name: post-deploy-canary
description: "Watch production right after a deploy for errors, regressions, and anomalies."
version: 1.0.0
author: hermes-devcrew
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [canary, monitoring, deploy, production, observability]
    related_skills: [qa-testing, safe-change-and-deploy]
---

# Post-Deploy Canary

Use immediately after a deploy to confirm the live system is healthy — before declaring success.

## Procedure
1. **Pre-deploy baseline.** Capture key signals before deploy: error rate, latency, health
   endpoints, and a smoke/screenshot of critical pages.
2. **Smoke the critical paths.** After deploy, exercise the few flows that must work (login,
   checkout, the changed feature). Fast and shallow.
3. **Watch the signals.** For a short window, compare error rate, latency, console errors, and key
   pages against the baseline.
4. **Decide.** Healthy → confirm success. Anomaly → raise it loudly and recommend rollback
   (coordinate with `devcrew-devops`, who owns the rollback).

## Rules
- A deploy isn't "done" until the canary window passes. **Silence ≠ success** — check the signals.
- Favor fast detection over deep analysis during the window; investigate after stabilizing.

## Done when
Critical paths are verified live and signals match or beat the pre-deploy baseline — or a rollback
has been recommended with evidence.
