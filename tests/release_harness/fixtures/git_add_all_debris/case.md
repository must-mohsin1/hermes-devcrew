# Regression fixture — git-add-all-debris (check_library id: git-add-all-debris)

**Incident.** A worker ran `git add -A` and pushed 18 build/log artifacts into a PR
that then merged to main (commit 3c62c38). Operator cleanup raced the merge.

**Rule the check enforces.** No gitignored/debris path may be tracked in the release
branch (`pr_hygiene_gate.check_branch` → `tracked-debris`, and `clean_integrate`
stages explicit lane paths only, never `git add -A`).

**Reproducing input.** Force-track a gitignored file:

```bash
echo noise > build.log          # matches *.log in .gitignore
git add -f build.log && git commit -m "oops debris"
```

`pr_hygiene_gate` must report `tracked-debris` for `build.log` (via
`git check-ignore --no-index`) and exit VIOLATIONS. Covered by
`test_pr_hygiene_gate.py::test_tracked_debris_fails`.
