# Changelog

## [0.5.0] - 2026-06-14

### Added
- **devos release-manager (Phase 1)** — the integrator is elevated to the fleet's
  release-manager: a deterministic `release_harness` Python package turns an approved
  spec + reviewer-approved build into a clean, evidence-backed **draft** PR with no
  operator babysitting. Lives entirely in hermes-devcrew (survives kernel updates per
  `dev-os/docs/kernel-extension-strategy.md` — we never fork the kernel).
  - `release_harness/`: `exits` (structured 0/1/2 codes — a tool that can't run returns
    ESCALATE, never PASS), `cardfiles` (parse the architect's `Files:` prose into a
    lane→file map), `check_library` (E1 self-improving registry, seeded with this
    session's real incidents), `spec_claim_verify` (plan-gate prose check + decompose-time
    assignee validation via the kernel's own `profile_exists`), `clean_integrate` (one
    commit per lane off the base, explicit paths only, ESCALATE on any unclaimed file —
    never `git add -A`), `pr_hygiene_gate` (tracked-debris / missing-evidence / stale-base
    checks). Each tool has a `python3 -m release_harness.<tool>` CLI returning the exit code.
  - `agents/integrator/skills/release-management/SKILL.md` — the judgment playbook driving
    the harness at the `spec-verify` (pre-build) and `release` (post-build) card gates;
    `SOUL.md` elevated to name the release-manager role and the never-merge / never-push-main
    boundary.
  - **E1** check-library: every new catch becomes a permanent rule (incident → rule +
    fixture) so the same failure never recurs.
  - **E2** verification gates (reviewer / qa / integrator) → `deepseek-v4-pro` via
    `model.default` in each `config.yaml` (the authoritative model; team.yaml is reference),
    with flash kept as graceful-degradation fallback; coder workers stay on flash for cost.
    Eval bar in `tests/release_harness/eval_gate_model.md` gates the bump (revert if pro !> flash).
  - **E3** fleet-wide wiring (dev-os repo): kanban-orchestrator v3.12.0 (decompose-time
    assignee gate + a spec-verify card parented under the human-approve gate), kanban-worker
    v2.6.0 (run `pr_hygiene_gate` before completing).
  - `install.sh` installs `release_harness` (editable, PYTHONPATH `.env` fallback) plus a
    post-install import smoke check; `pyproject.toml` makes the package pip-installable.
- 22 new tests (`tests/release_harness/` + `tests/test_release_manager_role.py`); full suite green.

### Notes
- **E4** (kernel debris-guard) deferred to Phase 2 — it collides with the kernel's
  `checkpoint_manager.py` `git add -A` and needs an upstream hook. The T-B
  worker-budget-visibility fix is the one genuinely kernel-bound item left → upstream PR to
  NousResearch (the v3.10.0 guided-retry doctrine is the current mitigation).

## [0.4.2] - 2026-06-13

### Changed
- kanban-worker doctrine synced to **v2.5.0** (byte-identical mirror of the dev-os seed). Documents the now-shipped Item-10 T-F evidence gate: QA and integrator `kanban_complete` calls are kernel-rejected unless `artifacts=[...]` lists at least one existing, non-empty file. Adds the fix-card assignee rule (copy a real profile name verbatim — four phantom-assignee incidents across two builds silently stranded cards), the integrator's sweep-for-open-fix-cards check before completing, kanban-on-kanban test isolation (fixtures use temp DBs / scratch boards, never the live board — an item-10 stress test ran 17 concurrent writers against production), and the retry-guidance contract (treat an orchestrator `RETRY GUIDANCE` comment as ground truth instead of re-exploring).

## [0.4.1] - 2026-06-12

### Changed
- Per-profile turn caps sized from the control-plane build's run history: backend-dev/integrator/qa **80**, reviewer **70**, others **60** (was 90 — the runaway ceiling). Values keep ~10% headroom over the longest historically *successful* runs (~75 tool-iterations), so proven builds don't die at the cap while 90-turn loops do.
- The `agent.gateway_timeout`/`gateway_timeout_warning` keys are deliberately absent: they only govern gateway chat-session inactivity, not dispatched kanban workers. Wall-clock caps belong to per-task `max_runtime_seconds` (Item 10).
- kanban-worker doctrine synced to **v2.4.0** (byte-identical mirror of the dev-os seed): verification cards must capture real evidence (tee'd `test_run.<task_id>.log` with command + exit code, digest mirrored to a durable comment); dual-cause `timed_out` retry guidance.

### Added
- `tests/test_agent_configs.py` — parses every `agents/*/config.yaml`, enforces `max_turns` as an int 1–90 under the `agent:` mapping, and refuses reintroduction of the inert gateway timeout keys (suite now 27 tests).
