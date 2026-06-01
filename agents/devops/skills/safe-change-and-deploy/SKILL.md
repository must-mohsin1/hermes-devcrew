---
name: safe-change-and-deploy
description: "Make infra/CI/deploy changes that are reproducible, reversible, and least-privilege."
version: 1.0.0
author: hermes-devcrew
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [devops, ci-cd, deploy, infrastructure, observability, safety]
    related_skills: [adversarial-review]
---

# Safe Change & Deploy

Use for any containers / CI / IaC / deploy / observability task.

## Procedure
1. **Claim & locate.** `hermes kanban claim` → work in the isolated workspace it prints. Re-read
   the acceptance criteria and the target environment.
2. **Write the rollback first.** Before changing anything with side effects, state how to undo it.
   If you can't undo it, escalate (see Safety).
3. **Codify, don't click.** Express the change as code/config (Dockerfile, pipeline, IaC). Pin
   versions; update lockfiles. No un-reviewable manual changes.
4. **Least privilege.** Request only the scopes needed. Secrets come from env/secret store —
   never hardcoded, never committed.
5. **Dry-run / stage.** Validate in a safe context (plan, build, staging) before anything real.
6. **Apply & verify.** Confirm health/metrics/logs after the change. Capture evidence.
7. **Hand off.** `hermes kanban complete` with: what changed, how to verify, and how to revert.

## Safety — hard stops
Destructive or production-affecting actions (delete, drop, force-push, prod deploy, scaling to
zero) require **explicit human approval**. Surface them via `hermes kanban block` describing the
action and its blast radius. Default to the safe path.
