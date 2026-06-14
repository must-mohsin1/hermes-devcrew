# release_harness/clean_integrate.py
"""clean-integrate — reconstruct one commit per lane off origin/<base>, never
git add -A. A working-tree file claimed by no lane → ESCALATE (don't guess;
this is how 3c62c38 debris and the composition-shape straggler surface).
Per-lane commits are ORGANIZATIONAL — only the branch tip is build-verified
(Reviewer Concern); intermediate commits may not individually build."""
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
    ok: bool = True
    @property
    def exit_code(self):
        if not self.ok:
            return exits.ESCALATE
        return exits.VIOLATIONS if self.findings else exits.PASS

def _git(repo, *args, check=True):
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr}")
    return r.stdout

def _changed_files(repo):
    out = _git(repo, "status", "--porcelain")
    files = []
    for line in out.splitlines():
        path = line[3:].strip()
        # skip gitignored debris entirely (never staged)
        ci = subprocess.run(["git", "-C", str(repo), "check-ignore", "--no-index", path],
                            capture_output=True, text=True)
        if ci.returncode == 0:
            continue
        files.append(path)
    return files

def reconstruct(repo: Path, base: str, lane_map: dict, branch: str) -> Report:
    repo = Path(repo)
    rep = Report()
    claimed = {p for paths in lane_map.values() for p in paths}
    changed = set(_changed_files(repo))
    orphans = changed - claimed
    if orphans:
        rep.ok = False
        rep.findings.append(Finding("unclaimed-file",
            f"changed files claimed by no lane: {sorted(orphans)} — escalate, do not guess"))
        return rep
    _git(repo, "checkout", "-B", branch, base)
    for card_id, paths in lane_map.items():
        present = [p for p in paths if (repo / p).exists() or p in changed]
        if not present:
            continue
        _git(repo, "add", "--", *present)   # explicit paths only, never -A
        _git(repo, "commit", "-q", "-m", f"lane {card_id}")
    return rep

if __name__ == "__main__":
    import argparse, sys, json
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--branch", required=True)
    ap.add_argument("--lane-map", required=True)  # JSON file: {"card_id": ["path", ...]}
    a = ap.parse_args()
    try:
        lane_map = json.loads(Path(a.lane_map).read_text(encoding="utf-8"))
        rep = reconstruct(Path(a.repo), a.base, lane_map, a.branch)
    except Exception as e:  # can't-run (bad base, missing lane-map, git error) → escalate
        print(f"clean_integrate could not run: {e}", file=sys.stderr)
        sys.exit(exits.ESCALATE)
    print(json.dumps([f.__dict__ for f in rep.findings], indent=2))
    sys.exit(rep.exit_code)
