"""pr-hygiene-gate — the release checklist. Mechanical, deterministic.
Blocks (exit 1) on: a tracked file that git itself reports as ignored (debris),
a missing evidence artifact, or a stale base. ESCALATES (exit 2) when it CANNOT
actually inspect the repo (not a git work-tree, or the base ref won't resolve —
e.g. `origin/main` on a fresh clone with no fetch): a tool that cannot run must
never read as PASS (the verify_code_landed.sh lesson). Never pushes; only inspects."""
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from release_harness import exits

@dataclass
class Finding:
    kind: str
    detail: str

@dataclass
class Report:
    findings: list = field(default_factory=list)
    ok: bool = True   # False → could-not-run → ESCALATE, never a false-clean PASS
    @property
    def exit_code(self):
        if not self.ok:
            return exits.ESCALATE
        return exits.VIOLATIONS if self.findings else exits.PASS

def _run(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)

def check_branch(repo: Path, base: str, evidence: list) -> Report:
    repo = Path(repo)
    rep = Report()
    # 0) the gate must be able to inspect the repo. A tool that cannot run returns
    #    ESCALATE — it must NEVER produce a false-clean PASS.
    wt = _run(repo, "rev-parse", "--is-inside-work-tree")
    if wt.returncode != 0 or wt.stdout.strip() != "true":
        rep.ok = False
        rep.findings.append(Finding("not-a-work-tree",
            f"{repo} is not a git work-tree — cannot inspect; escalate"))
        return rep
    # the base ref must resolve, or the freshness check is meaningless (the common
    # 'origin/main not fetched on a fresh/shallow clone' case) — escalate, don't pass.
    if _run(repo, "rev-parse", "--verify", "--quiet", f"{base}^{{commit}}").returncode != 0:
        rep.ok = False
        rep.findings.append(Finding("base-unresolvable",
            f"base '{base}' does not resolve (remote not fetched?) — cannot verify freshness; escalate"))
        return rep
    # 1) no tracked file that is also gitignored (debris that slipped in)
    for path in _run(repo, "ls-files").stdout.splitlines():
        ci = _run(repo, "check-ignore", "--no-index", path)
        if ci.returncode == 0:  # git says this tracked path matches .gitignore
            rep.findings.append(Finding("tracked-debris",
                f"{path} is tracked but matches .gitignore — debris in the branch"))
    # 2) evidence artifacts present and non-empty
    for ev in evidence:
        p = repo / ev
        if not p.is_file() or p.stat().st_size == 0:
            rep.findings.append(Finding("missing-evidence",
                f"evidence artifact '{ev}' is missing or empty"))
    # 3) base freshness: branch must not be behind <base> (base guaranteed to resolve here)
    behind = _run(repo, "rev-list", "--count", f"HEAD..{base}").stdout.strip()
    if behind and behind.isdigit() and int(behind) > 0:
        rep.findings.append(Finding("stale-base",
            f"branch is {behind} commits behind {base} — rebase before PR"))
    return rep

if __name__ == "__main__":
    import argparse, sys, json
    ap = argparse.ArgumentParser()
    ap.add_argument("repo"); ap.add_argument("--base", default="origin/main")
    ap.add_argument("--evidence", nargs="*", default=[])
    a = ap.parse_args()
    try:
        rep = check_branch(a.repo, a.base, a.evidence)
    except Exception as e:  # a tool that cannot run escalates — never silently "passes"
        print(f"pr_hygiene_gate could not run: {e}", file=sys.stderr)
        sys.exit(exits.ESCALATE)
    print(json.dumps([f.__dict__ for f in rep.findings], indent=2))
    sys.exit(rep.exit_code)
