# Regression fixture — phantom-assignee (check_library id: phantom-assignee)

**Incident.** Cards were created for non-spawnable profiles (e.g. `devos-backend`,
`devcrew-developer`) and sat in `ready` forever — the dispatcher silently skips
unknown assignees. Four real incidents across two builds.

**Rule the check enforces.** Every card assignee must resolve via
`profiles.profile_exists` (`spec_claim_verify.verify_assignees`, decompose gate).

**Reproducing input** (task graph with one phantom assignee):

```json
[{"id": "t_a", "assignee": "devcrew-backend-dev"},
 {"id": "t_b", "assignee": "devos-backend"}]
```

With a `profile_exists` that knows only the real pool, `verify_assignees` must emit
a `phantom-assignee` finding for `t_b` and exit VIOLATIONS. Covered by
`test_spec_claim_verify.py::test_phantom_assignee_blocks`.
