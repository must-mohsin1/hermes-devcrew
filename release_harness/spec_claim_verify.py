# release_harness/spec_claim_verify.py
"""spec-claim-verify — two modes, two gates (Reviewer Concern: two artifacts).

PLAN GATE (this function): grep-able prose claims in the planner spec
('X is missing' / 'file Y' references). Genuinely fuzzy because the spec is
prose, so findings are flagged as CANDIDATES for the human (fail-open) — they
never hard-block. Catches the Item-13 A1 false-premise class.

DECOMPOSE-TIME (verify_assignees, Task 5): assignee validation against the
architect's task graph via the kernel's own profile_exists. Hard.
"""
import re
from dataclasses import dataclass, field
from pathlib import Path
from release_harness import exits

# Require the missing/not-exist keyword to actually be captured (so a bare 'is'
# can't satisfy the claim). Path is the named group; the keyword follows it.
_MISSING = re.compile(
    r"(?P<path>[\w./()\[\]-]+\.\w{1,5})\s+(?:is\s+|are\s+)?(?:missing|does\s+not\s+exist|doesn'?t\s+exist)",
    re.IGNORECASE,
)

@dataclass
class Finding:
    kind: str
    detail: str

@dataclass
class Report:
    gate: str
    findings: list = field(default_factory=list)
    @property
    def exit_code(self) -> int:
        return exits.VIOLATIONS if self.findings else exits.PASS

def _kernel_profile_exists(name: str) -> bool:
    """Use the kernel's OWN resolver so we never diverge from the dispatcher
    (Reviewer Concern: do not reimplement profile resolution)."""
    from hermes_cli import profiles as _p  # provided by the installed kernel
    return _p.profile_exists(name)

def verify_assignees(task_graph, profile_exists=None) -> Report:
    check = profile_exists or _kernel_profile_exists
    report = Report(gate="decompose")
    for card in task_graph:
        a = (card.get("assignee") or "").strip()
        if a and not check(a):
            report.findings.append(Finding(
                "phantom-assignee",
                f"card {card.get('id','?')} assigned to '{a}' which is not a spawnable profile",
            ))
    return report

def verify_spec_claims(spec_file: Path, repo: Path) -> Report:
    text = Path(spec_file).read_text(encoding="utf-8")
    report = Report(gate="plan")
    for m in _MISSING.finditer(text):
        rel = m.group("path")
        if (Path(repo) / rel).exists():
            report.findings.append(Finding(
                "refuted-missing-claim",
                f"spec claims '{rel}' is missing, but it EXISTS in the repo — verify before building",
            ))
    return report

if __name__ == "__main__":
    import argparse, sys, json
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="mode", required=True)
    p_plan = sub.add_parser("plan")
    p_plan.add_argument("spec"); p_plan.add_argument("repo")
    p_ass = sub.add_parser("assignees")
    p_ass.add_argument("graph_json")  # JSON file: [{"id":..,"assignee":..}, ...]
    a = ap.parse_args()
    if a.mode == "plan":
        rep = verify_spec_claims(Path(a.spec), Path(a.repo))
    else:
        graph = json.loads(Path(a.graph_json).read_text(encoding="utf-8"))
        rep = verify_assignees(graph)
    print(json.dumps([f.__dict__ for f in rep.findings], indent=2))
    sys.exit(rep.exit_code)
