# tests/test_release_manager_role.py
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]


def test_release_management_skill_present():
    assert (ROOT / "agents/integrator/skills/release-management/SKILL.md").is_file()


def test_soul_names_the_release_manager_role_and_harness():
    soul = (ROOT / "agents/integrator/SOUL.md").read_text()
    assert "release-manager" in soul.lower()
    assert "release_harness" in soul or "pr-hygiene-gate" in soul


def test_harness_importable():
    import release_harness  # noqa
