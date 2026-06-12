"""agents/*/config.yaml sanity: every per-profile config parses, keeps
max_turns under the agent: mapping within 1-90, and does NOT carry
agent.gateway_timeout / gateway_timeout_warning — those keys only govern
gateway chat-session inactivity, not dispatched kanban workers, so setting
them here is inert config that misleads readers (wall-clock caps belong to
per-task max_runtime_seconds)."""
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIGS = sorted((REPO_ROOT / "agents").glob("*/config.yaml"))

INERT_KEYS = ("gateway_timeout", "gateway_timeout_warning")


def _is_int(val) -> bool:
    return isinstance(val, int) and not isinstance(val, bool)


def test_agent_configs_discovered():
    assert CONFIGS, f"no agents/*/config.yaml found under {REPO_ROOT}"


@pytest.mark.parametrize("cfg", CONFIGS, ids=lambda p: p.parent.name)
def test_agent_config_caps(cfg):
    data = yaml.safe_load(cfg.read_text(encoding="utf-8"))
    assert isinstance(data, dict), f"{cfg} did not parse to a mapping"

    agent = data.get("agent")
    assert isinstance(agent, dict), f"{cfg} has no agent: mapping"
    assert "max_turns" in agent, f"{cfg} agent: mapping is missing max_turns"

    turns = agent["max_turns"]
    assert _is_int(turns) and 1 <= turns <= 90, \
        f"{cfg} max_turns must be an int in 1-90, got {turns!r}"

    for key in INERT_KEYS:
        assert key not in agent and key not in data, (
            f"{cfg} sets {key} — inert for kanban workers (gateway-chat-only); "
            "use per-task max_runtime_seconds for wall-clock caps instead"
        )

    # Caps must live under agent:, not at the document top level where Hermes
    # deep-merge would silently ignore them.
    assert "max_turns" not in data, f"{cfg} has top-level max_turns (must be under agent:)"
