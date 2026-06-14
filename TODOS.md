# TODOS

## agents
- **Real wall-clock caps via per-task max_runtime_seconds** — the `gateway_timeout` keys were removed as inert for kanban workers (gateway-chat-only; `tests/test_agent_configs.py` refuses their reintroduction). Dispatcher-side per-profile `max_runtime_seconds` defaults are Item 10 scope on the control-plane board. **Priority:** P2
- **Budget visibility for workers (Item-11 T-B) — upstream-PR candidate** — workers are never told their `max_turns` budget, and at exhaustion the final model call is toolless, so `kanban_complete` is impossible (the run records `timed_out` and feeds the failure breaker). This is the one genuinely kernel-bound Item-11 fix: 2 of its 3 parts need kernel hooks that don't exist (system-prompt-assembly, budget-exhaustion) — see `dev-os/docs/kernel-extension-strategy.md`. Right path is an upstream PR to NousResearch (it's generic — every Hermes user benefits), NOT a fork. Mitigation already shipped: the v3.10.0 guided-retry doctrine (rescued 4/4 budget-exhausted cards). **Priority:** P2, not urgent.

## release-manager (Phase 2)
- **E4 — kernel debris-guard** — deferred from Phase 1. A pre-commit/pre-push guard that refuses to track gitignored debris at the kernel level. Collides with `checkpoint_manager.py`'s `git add -A`; needs an upstream hook (no pre-commit hook exists today). The Phase-1 `pr_hygiene_gate` + the worker pre-completion doctrine (kanban-worker v2.6.0) are the agent-layer mitigation. **Priority:** P2.
- **Structured `Files:` card field** — the lane→file map is parsed from the architect's free-prose `Files:` block (`release_harness/cardfiles.py`). A structured kanban field would be more robust; revisit if prose parsing proves fragile in practice. **Priority:** P3.

## install.sh
- **Fan-out test coverage** — §5a (kanban-worker seed → every devcrew profile, drift warning on divergence) has zero tests; a silent-skip regression would strand stale doctrine in every profile. Minimal test: run the block against a temp HERMES_HOME with fake profile dirs, assert byte-identical copies and the drift warning. **Priority:** P2

## Completed
- **Evidence-artifact kernel gate wording** — kanban-worker v2.5.0 (2026-06-12) documents the shipped Item 10 T-F gate: QA/integrator `kanban_complete` is kernel-rejected without `artifacts=[...]` pointing at existing non-empty files; doctrine now teaches the parameter and the tee'd-log workflow.
