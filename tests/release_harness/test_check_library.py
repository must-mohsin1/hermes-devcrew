from pathlib import Path
from release_harness.check_library import load_library, Check

def test_seed_library_loads_and_has_known_incidents():
    lib = load_library()  # default path: release_harness/check_library.yaml
    ids = {c.id for c in lib}
    # seeded from this session's real incidents:
    assert "phantom-assignee" in ids
    assert "false-route-premise" in ids
    assert "git-add-all-debris" in ids

def test_each_check_has_required_fields():
    for c in load_library():
        assert c.id and c.incident and c.rule and c.severity in {"block", "warn"}

def test_load_from_custom_path(tmp_path):
    p = tmp_path / "lib.yaml"
    p.write_text(
        "checks:\n"
        "  - id: t1\n"
        "    incident: example\n"
        "    rule: 'grep X'\n"
        "    severity: warn\n"
        "    fixture: tests/release_harness/fixtures/t1\n"
    )
    lib = load_library(p)
    assert lib[0].id == "t1" and lib[0].severity == "warn"
