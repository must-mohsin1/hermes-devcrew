"""Structured exit codes. A tool that CANNOT run returns ESCALATE (2) — it must
never be read as PASS. This is the verify_code_landed.sh lesson encoded."""
PASS = 0        # checked, clean
VIOLATIONS = 1  # checked, found problems (block)
ESCALATE = 2    # could not run / ambiguous → human decides, NEVER treated as pass
