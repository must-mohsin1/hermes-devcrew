# Changelog

## [0.4.1] - 2026-06-12

### Changed
- Per-profile turn caps sized from the control-plane build's run history: backend-dev/integrator/qa **80**, reviewer **70**, others **60** (was 90 — the runaway ceiling). Values keep ~10% headroom over the longest historically *successful* runs (~75 tool-iterations), so proven builds don't die at the cap while 90-turn loops do.
- The `agent.gateway_timeout`/`gateway_timeout_warning` keys are deliberately absent: they only govern gateway chat-session inactivity, not dispatched kanban workers. Wall-clock caps belong to per-task `max_runtime_seconds` (Item 10).
- kanban-worker doctrine synced to **v2.4.0** (byte-identical mirror of the dev-os seed): verification cards must capture real evidence (tee'd `test_run.<task_id>.log` with command + exit code, digest mirrored to a durable comment); dual-cause `timed_out` retry guidance.

### Added
- `tests/test_agent_configs.py` — parses every `agents/*/config.yaml`, enforces `max_turns` as an int 1–90 under the `agent:` mapping, and refuses reintroduction of the inert gateway timeout keys (suite now 27 tests).
