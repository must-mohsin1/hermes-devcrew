# Regression fixture — broken-main-uncommitted-helper (check_library id: broken-main-uncommitted-helper)

**Incident.** Item-12 committed a route that imported a helper which was never
committed → main's build broke on the missing import.

**Rule the check enforces.** Every import target must be a tracked file or live in
the release branch. Mechanically, `clean_integrate` reconstructs one commit per lane
and ESCALATES on any changed file claimed by no lane (so a stray/uncommitted helper
surfaces instead of silently shipping), and `pr_hygiene_gate` re-runs the build/test
evidence so a broken import fails before the PR opens.

**Reproducing shape.** A lane commits `route.py` that does `from helper import x`
while `helper.py` is unclaimed/uncommitted. `clean_integrate.reconstruct` must return
ESCALATE listing the orphan rather than committing a half-built tree. Related coverage:
`test_clean_integrate.py::test_unclaimed_file_escalates`.

> Phase-2 note: a dedicated import-resolution check (parse imports, assert each
> target is tracked or in-branch) is not yet built; this fixture documents the
> incident the future check must catch.
