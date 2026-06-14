# Regression fixture — false-route-premise (check_library id: false-route-premise)

**Incident.** Item-13 A1 claimed a route was "missing" and asked to create it — but
the route already existed, so the build produced dead/duplicate code.

**Rule the check enforces.** Spec "X is missing" claims must be grep-verified against
the repo (`spec_claim_verify.verify_spec_claims`, plan gate). Fail-open: a refuted
claim is surfaced as a *candidate* for the human, not a hard block.

**Reproducing input** (spec claims an existing file is missing):

```
A1: the route src/exists.ts is missing, create it.
```

When `src/exists.ts` exists in the repo, `verify_spec_claims` must emit a
`refuted-missing-claim` finding naming that path. Covered by
`test_spec_claim_verify.py::test_false_missing_claim_is_flagged`.
