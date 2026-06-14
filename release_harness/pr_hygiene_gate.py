"""pr-hygiene-gate — the release checklist. Mechanical, deterministic.
Blocks (exit 1) on: a tracked file that git itself reports as ignored (debris),
a missing evidence artifact, or a stale base. Never pushes; this only inspects."""
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
    @property
    def exit_code(self):
        return exits.VIOLATIONS if self.findings else exits.PASS

def _git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args],
                          capture_output=True, text=True).stdout

def check_branch(repo: Path, base: str, evidence: list) -> Report:
    repo = Path(repo)
    rep = Report()
    # 1) no tracked file that is also gitignored (debris that slipped in)
    tracked = _git(repo, "ls-files").splitlines()
    for path in tracked:
        ci = subprocess.run(["git", "-C", str(repo), "check-ignore", "--no-index", path],
                            capture_output=True, text=True)
        if ci.returncode == 0:  # git says this tracked path matches .gitignore
            rep.findings.append(Finding("tracked-debris",
                f"{path} is tracked but matches .gitignore — debris in the branch"))
    # 2) evidence artifacts present and non-empty
    for ev in evidence:
        p = repo / ev
        if not p.is_file() or p.stat().st_size == 0:
            rep.findings.append(Finding("missing-evidence",
                f"evidence artifact '{ev}' is missing or empty"))
    # 3) base freshness: branch must not be behind origin/<base> (best-effort)
    behind = _git(repo, "rev-list", "--count", f"HEAD..{base}").strip()
    if behind and behind.isdigit() and int(behind) > 0:
        rep.findings.append(Finding("stale-base",
            f"branch is {behind} commits behind {base} — rebase before PR"))
    return rep
