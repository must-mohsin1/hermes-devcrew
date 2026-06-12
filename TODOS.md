# TODOS

## agents
- **Real wall-clock caps via per-task max_runtime_seconds** — the `gateway_timeout` keys were removed as inert for kanban workers (gateway-chat-only; `tests/test_agent_configs.py` refuses their reintroduction). Dispatcher-side per-profile `max_runtime_seconds` defaults are Item 10 scope on the control-plane board. **Priority:** P2
- **Budget visibility for workers** — workers are never told their `max_turns` budget, and at exhaustion the final model call is toolless, so `kanban_complete` is impossible (the run records `timed_out` and feeds the failure breaker). Needs upstream hermes-agent work; tracked with Item 10 T-A/T-D. **Priority:** P2

## install.sh
- **Fan-out test coverage** — §5a (kanban-worker seed → every devcrew profile, drift warning on divergence) has zero tests; a silent-skip regression would strand stale doctrine in every profile. Minimal test: run the block against a temp HERMES_HOME with fake profile dirs, assert byte-identical copies and the drift warning. **Priority:** P2

## skills
- **Evidence-artifact kernel gate** — kanban-worker v2.4.0 makes the orchestrator treat weak evidence as unverified; the mechanical completion gate is Item 10 T-F. Update the doctrine's enforcement wording once it lands. **Priority:** P2

## Completed
