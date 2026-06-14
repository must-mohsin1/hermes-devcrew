from release_harness import exits

def test_exit_codes_are_distinct_and_documented():
    assert exits.PASS == 0
    assert exits.VIOLATIONS == 1
    assert exits.ESCALATE == 2
    # ESCALATE must never be confused with PASS — the verify_code_landed.sh lesson
    assert len({exits.PASS, exits.VIOLATIONS, exits.ESCALATE}) == 3
