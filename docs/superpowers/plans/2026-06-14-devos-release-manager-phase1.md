# devos Release-Manager (Phase 1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the devcrew fleet a deterministic release-trust layer — a Python harness (spec-claim-verify, clean-integrate, pr-hygiene-gate) backed by a self-improving check-library, driven by the elevated integrator (now the "release-manager" role) — so the fleet turns an approved spec into a clean, verified, reviewable draft PR with no operator babysitting.

**Architecture:** A standalone Python package `release_harness/` at the hermes-devcrew repo root, invokable as `python -m release_harness.<tool>` and unit-tested with pytest (matching the existing `tests/test_agent_configs.py` pattern). The integrator profile keeps its name `devcrew-integrator` for board/dispatch continuity but gains a `release-management` skill and runs the harness at two card touchpoints (a pre-gate `spec-verify` card and the post-build `release` card). Everything lives in hermes-devcrew (survives daily kernel updates per `dev-os/docs/kernel-extension-strategy.md`); the harness only *uses* kernel features upstream already ships (`kanban_show`, `profile_exists`, `max_runtime_seconds`, `git`).

**Tech Stack:** Python 3.12 + pytest + PyYAML (already used), GitPython-free (shell out to `git` via `subprocess`), the `hermes` CLI for kanban reads.

**Scope (final, post-CEO-review):** baseline B (3 tools + role elevation) + E1 (check-library) + E2 (stronger gate model) + E3 (fleet-wide harness). **E4 deferred to Phase 2.** The 7 Reviewer Concerns from the spec are resolved inline in the tasks noted.

**Locked decisions (resolve spec ambiguities):**
1. Profile NAME stays `devcrew-integrator`; the elevated ROLE is "release-manager" (capability, not a rename — a rename would strand card routing). The `release-management` skill carries the new behavior.
2. Harness is a Python package `release_harness/`, CLI via `python -m release_harness.<tool>`, exit codes `0`=pass, `1`=violations, `2`=cannot-run/escalate.
3. The lane→file map is parsed from the architect's per-card `Files:` prose (read via `hermes kanban show`), NOT the planner spec (Reviewer Concern: lane-map source).
4. E1 registry is a YAML file `release_harness/check_library.yaml` with a fixed schema; `spec_claim_verify` consumes it (Reviewer Concern #4).
5. E2 bumps the three verification-gate roles (reviewer, qa, integrator) from `deepseek-v4-flash` to `deepseek-v4-pro` in `team.yaml`.

---

## File structure

```
hermes-devcrew/
  release_harness/
    __init__.py            # package marker + version
    exits.py               # PASS=0 VIOLATIONS=1 ESCALATE=2 constants
    cardfiles.py           # parse architect `Files:` prose from a card body → {path: lane_card_id}
    check_library.py       # E1 registry read/write + apply registered rules
    check_library.yaml     # E1 registry data (incident → rule + fixture), seeded from this session
    spec_claim_verify.py   # plan-gate prose claim check + decompose-time assignee validation
    clean_integrate.py     # reconstruct per-lane commits off origin/main, strip debris
    pr_hygiene_gate.py     # release checklist (no debris, evidence present, base fresh, unpushed)
  tests/release_harness/
    conftest.py            # tmp-repo + tmp-board fixtures (NEVER touch live repos/boards)
    test_cardfiles.py
    test_check_library.py
    test_spec_claim_verify.py
    test_clean_integrate.py
    test_pr_hygiene_gate.py
  agents/integrator/
    skills/release-management/SKILL.md   # judgment playbook (NEW)
    SOUL.md                              # elevated (MODIFY)
  team.yaml                              # E2 model bump (MODIFY)
  install.sh                             # enable harness import path (MODIFY)
```

---

## Task 1: Harness package skeleton + exit codes

**Files:**
- Create: `release_harness/__init__.py`
- Create: `release_harness/exits.py`
- Create: `tests/release_harness/__init__.py`
- Test: `tests/release_harness/test_exits.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/release_harness/test_exits.py
from release_harness import exits

def test_exit_codes_are_distinct_and_documented():
    assert exits.PASS == 0
    assert exits.VIOLATIONS == 1
    assert exits.ESCALATE == 2
    # ESCALATE must never be confused with PASS — the verify_code_landed.sh lesson
    assert len({exits.PASS, exits.VIOLATIONS, exits.ESCALATE}) == 3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd hermes-devcrew && python -m pytest tests/release_harness/test_exits.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'release_harness'`

- [ ] **Step 3: Create the package + constants**

```python
# release_harness/__init__.py
"""Deterministic release-trust harness for the devcrew release-manager.
Ships in hermes-devcrew (survives kernel updates). See
docs/superpowers/specs/2026-06-13-devos-release-manager-design.md."""
__version__ = "0.1.0"
```

```python
# release_harness/exits.py
"""Structured exit codes. A tool that CANNOT run returns ESCALATE (2) — it must
never be read as PASS. This is the verify_code_landed.sh lesson encoded."""
PASS = 0        # checked, clean
VIOLATIONS = 1  # checked, found problems (block)
ESCALATE = 2    # could not run / ambiguous → human decides, NEVER treated as pass
```

```python
# tests/release_harness/__init__.py
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd hermes-devcrew && python -m pytest tests/release_harness/test_exits.py -q`
Expected: PASS (1 passed)

- [ ] **Step 5: Commit**

```bash
git add release_harness/__init__.py release_harness/exits.py tests/release_harness/__init__.py tests/release_harness/test_exits.py
git commit -m "feat(harness): package skeleton + structured exit codes (0/1/2)"
```

---

## Task 2: Card `Files:` parser (lane→file map)

Resolves Reviewer Concern: lane-map source is the architect's per-card `Files:` prose, read via `hermes kanban show` — not the planner spec, and not a structured field.

**Files:**
- Create: `release_harness/cardfiles.py`
- Test: `tests/release_harness/test_cardfiles.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/release_harness/test_cardfiles.py
from release_harness.cardfiles import parse_files_block

CARD_BODY = """\
Implement T-A: signup onboarding fix.
Files:
- Create: web/src/middleware.ts
- Modify: web/src/app/(marketing)/login/page.tsx
- Test: web/src/app/(marketing)/login/page.test.tsx
Acceptance: ...
"""

def test_parses_create_modify_test_paths():
    files = parse_files_block(CARD_BODY)
    assert "web/src/middleware.ts" in files
    assert "web/src/app/(marketing)/login/page.tsx" in files
    assert "web/src/app/(marketing)/login/page.test.tsx" in files

def test_missing_files_block_returns_none():
    # A card with no Files: line (e.g. the `hermes kanban swarm` fast path)
    assert parse_files_block("Just do the thing, no files line.") is None

def test_blank_files_block_returns_empty_not_none():
    assert parse_files_block("Files:\n\nAcceptance: x") == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd hermes-devcrew && python -m pytest tests/release_harness/test_cardfiles.py -q`
Expected: FAIL with `ModuleNotFoundError`/`ImportError: cannot import name 'parse_files_block'`

- [ ] **Step 3: Implement the parser**

```python
# release_harness/cardfiles.py
"""Parse the architect's free-prose `Files:` block out of a kanban card body.
The kanban card schema has NO structured files field, so the architect's
decompose-goal skill writes a `Files:` line per card; we parse that prose.
Returns None when no Files: block exists (caller escalates), [] when the block
is present but empty, else a list of repo-relative paths."""
import re

_FILES_HEADER = re.compile(r"^\s*Files:\s*$", re.IGNORECASE | re.MULTILINE)
# bullet lines like "- Create: path", "- Modify: path:12-20", "- Test: path"
_BULLET = re.compile(
    r"^\s*[-*]\s*(?:Create|Modify|Delete|Test|Edit)?\s*:?\s*(?P<path>[\w./()\[\]@-]+)",
    re.IGNORECASE,
)

def parse_files_block(card_body: str):
    m = _FILES_HEADER.search(card_body or "")
    if not m:
        return None
    rest = card_body[m.end():]
    paths = []
    for line in rest.splitlines():
        if line.strip() == "":
            # blank line ends the block only if we already saw bullets; otherwise skip
            if paths:
                break
            continue
        if not line.lstrip().startswith(("-", "*")):
            break  # block ended (next prose section)
        bm = _BULLET.match(line)
        if bm:
            path = bm.group("path").rstrip(":").strip()
            # strip an optional :line-range suffix (path:12-20)
            path = re.sub(r":\d+(?:-\d+)?$", "", path)
            if path:
                paths.append(path)
    return paths
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd hermes-devcrew && python -m pytest tests/release_harness/test_cardfiles.py -q`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add release_harness/cardfiles.py tests/release_harness/test_cardfiles.py
git commit -m "feat(harness): parse architect Files: prose into a lane→file map"
```

---

## Task 3: E1 check-library registry

Resolves Reviewer Concern #4 (E1 is a built component, not an aspiration): a concrete YAML registry + a read/apply API, seeded with this session's incidents.

**Files:**
- Create: `release_harness/check_library.py`
- Create: `release_harness/check_library.yaml`
- Test: `tests/release_harness/test_check_library.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/release_harness/test_check_library.py
from pathlib import Path
from release_harness.check_library import load_library, Check

def test_seed_library_loads_and_has_known_incidents():
    lib = load_library()  # default path: release_harness/check_library.yaml
    ids = {c.id for c in lib}
    # seeded from this session's real incidents:
    assert "phantom-assignee" in ids
    assert "false-route-premise" in ids
    assert "git-add-all-debris" in ids

def test_each_check_has_required_fields():
    for c in load_library():
        assert c.id and c.incident and c.rule and c.severity in {"block", "warn"}

def test_load_from_custom_path(tmp_path):
    p = tmp_path / "lib.yaml"
    p.write_text(
        "checks:\n"
        "  - id: t1\n"
        "    incident: example\n"
        "    rule: 'grep X'\n"
        "    severity: warn\n"
        "    fixture: tests/release_harness/fixtures/t1\n"
    )
    lib = load_library(p)
    assert lib[0].id == "t1" and lib[0].severity == "warn"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd hermes-devcrew && python -m pytest tests/release_harness/test_check_library.py -q`
Expected: FAIL (`ImportError`)

- [ ] **Step 3: Implement registry + seed data**

```python
# release_harness/check_library.py
"""E1 self-improving check-library. Every operator/release-manager catch becomes
a permanent entry here (incident → rule + fixture). The release-management skill
MANDATES adding an entry on each new catch, so the same failure never recurs.
This is the moat: trust compounds build-over-build."""
from dataclasses import dataclass
from pathlib import Path
import yaml

_DEFAULT = Path(__file__).with_name("check_library.yaml")

@dataclass(frozen=True)
class Check:
    id: str
    incident: str       # one-line description of the failure this prevents
    rule: str           # human/tool-readable rule the verifier applies
    severity: str       # "block" (exit 1) or "warn" (report only)
    fixture: str = ""   # path to the regression fixture proving the catch

def load_library(path: Path = _DEFAULT) -> list[Check]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return [Check(**{**{"severity": "block"}, **c}) for c in data.get("checks", [])]
```

```yaml
# release_harness/check_library.yaml
# Self-improving check-library (E1). Append an entry whenever a new failure
# class is caught — never delete, never let it rot. Each entry is a permanent
# automated gate. Seeded 2026-06-14 from the session that designed this harness.
checks:
  - id: phantom-assignee
    incident: "cards created for non-spawnable profiles sat ready forever (4 incidents)"
    rule: "every card assignee must resolve via profiles.profile_exists"
    severity: block
    fixture: tests/release_harness/fixtures/phantom_assignee
  - id: false-route-premise
    incident: "Item 13 A1 claimed a route was missing when it existed → dead code"
    rule: "spec 'X is missing' claims must be grep-verified against the repo"
    severity: warn
    fixture: tests/release_harness/fixtures/false_route_premise
  - id: git-add-all-debris
    incident: "a worker git add -A pushed 18 build/log artifacts into a PR that merged to main"
    rule: "no gitignored/debris paths may be tracked in the release branch"
    severity: block
    fixture: tests/release_harness/fixtures/git_add_all_debris
  - id: broken-main-uncommitted-helper
    incident: "Item 12 committed a route importing an uncommitted helper → main build broken"
    rule: "every import target must be a tracked file or in the release branch"
    severity: block
    fixture: tests/release_harness/fixtures/broken_main_import
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd hermes-devcrew && python -m pytest tests/release_harness/test_check_library.py -q`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add release_harness/check_library.py release_harness/check_library.yaml tests/release_harness/test_check_library.py
git commit -m "feat(harness): E1 self-improving check-library (registry + this session's incidents)"
```

---

## Task 4: `spec-claim-verify` — plan-gate prose claims

Resolves Reviewer Concern: two gates, two artifacts. This task is the PLAN-GATE check (fuzzy, fail-open, flags candidates). Assignee validation is Task 5.

**Files:**
- Create: `release_harness/spec_claim_verify.py`
- Test: `tests/release_harness/test_spec_claim_verify.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/release_harness/test_spec_claim_verify.py
from pathlib import Path
from release_harness.spec_claim_verify import verify_spec_claims
from release_harness import exits

def _repo(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "exists.ts").write_text("export const x = 1;\n")
    return tmp_path

def test_false_missing_claim_is_flagged(tmp_path):
    repo = _repo(tmp_path)
    spec = tmp_path / "spec.md"
    spec.write_text("A1: the route src/exists.ts is missing, create it.\n")
    report = verify_spec_claims(spec, repo)
    # the file EXISTS, so the "missing" claim is refuted → a flagged candidate
    assert any(f.kind == "refuted-missing-claim" and "src/exists.ts" in f.detail
               for f in report.findings)

def test_true_missing_claim_passes(tmp_path):
    repo = _repo(tmp_path)
    spec = tmp_path / "spec.md"
    spec.write_text("A1: src/absent.ts is missing, create it.\n")
    report = verify_spec_claims(spec, repo)
    assert not report.findings  # the file really is absent → no flag

def test_plan_gate_is_fail_open(tmp_path):
    # prose claims are fuzzy → findings are 'warn', exit is PASS-with-report
    repo = _repo(tmp_path)
    spec = tmp_path / "spec.md"
    spec.write_text("src/exists.ts is missing\n")
    report = verify_spec_claims(spec, repo)
    assert report.exit_code in (exits.PASS, exits.VIOLATIONS)
    assert report.gate == "plan"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd hermes-devcrew && python -m pytest tests/release_harness/test_spec_claim_verify.py -q`
Expected: FAIL (`ImportError`)

- [ ] **Step 3: Implement the plan-gate verifier**

```python
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

_MISSING = re.compile(
    r"(?P<path>[\w./()\[\]-]+\.\w{1,5})\s+(?:is|are|does not exist|doesn't exist|missing)",
    re.IGNORECASE,
)

@dataclass
class Finding:
    kind: str
    detail: str

@dataclass
class Report:
    gate: str
    findings: list[Finding] = field(default_factory=list)
    @property
    def exit_code(self) -> int:
        return exits.VIOLATIONS if self.findings else exits.PASS

def verify_spec_claims(spec_file: Path, repo: Path) -> Report:
    text = Path(spec_file).read_text(encoding="utf-8")
    report = Report(gate="plan")
    for m in _MISSING.finditer(text):
        rel = m.group("path")
        if "missing" not in m.group(0).lower() and "not exist" not in m.group(0).lower():
            continue
        if (Path(repo) / rel).exists():
            report.findings.append(Finding(
                "refuted-missing-claim",
                f"spec claims '{rel}' is missing, but it EXISTS in the repo — verify before building",
            ))
    return report
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd hermes-devcrew && python -m pytest tests/release_harness/test_spec_claim_verify.py -q`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add release_harness/spec_claim_verify.py tests/release_harness/test_spec_claim_verify.py
git commit -m "feat(harness): spec-claim-verify plan-gate prose check (fail-open candidates)"
```

---

## Task 5: `spec-claim-verify` — decompose-time assignee validation

**Files:**
- Modify: `release_harness/spec_claim_verify.py`
- Test: `tests/release_harness/test_spec_claim_verify.py` (add cases)

- [ ] **Step 1: Write the failing test**

```python
# append to tests/release_harness/test_spec_claim_verify.py
from release_harness.spec_claim_verify import verify_assignees
from release_harness import exits

def test_phantom_assignee_blocks():
    # profile_exists injected for hermetic test (no real ~/.hermes dependency)
    graph = [{"id": "t_a", "assignee": "devcrew-backend-dev"},
             {"id": "t_b", "assignee": "devos-backend"}]  # phantom
    real = {"devcrew-backend-dev", "devcrew-qa"}
    report = verify_assignees(graph, profile_exists=lambda p: p in real)
    assert report.gate == "decompose"
    assert report.exit_code == exits.VIOLATIONS
    assert any("devos-backend" in f.detail for f in report.findings)

def test_all_real_assignees_pass():
    graph = [{"id": "t_a", "assignee": "devcrew-qa"}]
    report = verify_assignees(graph, profile_exists=lambda p: True)
    assert report.exit_code == exits.PASS
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd hermes-devcrew && python -m pytest tests/release_harness/test_spec_claim_verify.py -q`
Expected: FAIL (`cannot import name 'verify_assignees'`)

- [ ] **Step 3: Implement assignee validation (uses the kernel's own profile_exists)**

```python
# add to release_harness/spec_claim_verify.py

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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd hermes-devcrew && python -m pytest tests/release_harness/test_spec_claim_verify.py -q`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add release_harness/spec_claim_verify.py tests/release_harness/test_spec_claim_verify.py
git commit -m "feat(harness): decompose-time assignee validation via kernel profile_exists"
```

---

## Task 6: `pr-hygiene-gate`

Resolves Reviewer Concerns: build/test evidence presence + base-freshness + no-debris + never-pushed-to-main. (Evidence *validity* — re-running tests — is the release-manager skill's job, Task 9; this gate checks presence + cleanliness mechanically.)

**Files:**
- Create: `release_harness/pr_hygiene_gate.py`
- Test: `tests/release_harness/test_pr_hygiene_gate.py`
- Create: `tests/release_harness/conftest.py` (tmp git repo fixture)

- [ ] **Step 1: Write the tmp-repo fixture + failing test**

```python
# tests/release_harness/conftest.py
import subprocess, pytest
from pathlib import Path

def _git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True,
                   capture_output=True, text=True)

@pytest.fixture
def tmp_git_repo(tmp_path):
    """A throwaway git repo. NEVER use a real repo or live board in tests
    (kanban-worker v2.5.0 isolation rule)."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@t")
    _git(repo, "config", "user.name", "t")
    (repo / ".gitignore").write_text("*.log\nagentdb.rvf\n")
    (repo / "src.py").write_text("x = 1\n")
    _git(repo, "add", "."); _git(repo, "commit", "-q", "-m", "base")
    _git(repo, "branch", "-M", "main")
    return repo
```

```python
# tests/release_harness/test_pr_hygiene_gate.py
import subprocess
from release_harness.pr_hygiene_gate import check_branch
from release_harness import exits

def _git(repo, *a):
    subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True, text=True)

def test_clean_branch_passes(tmp_git_repo):
    rep = check_branch(tmp_git_repo, base="main", evidence=["src.py"])
    assert rep.exit_code == exits.PASS

def test_tracked_debris_fails(tmp_git_repo):
    (tmp_git_repo / "build.log").write_text("noise")
    _git(tmp_git_repo, "add", "-f", "build.log")  # force-track a gitignored debris file
    _git(tmp_git_repo, "commit", "-q", "-m", "oops debris")
    rep = check_branch(tmp_git_repo, base="main", evidence=["src.py"])
    assert rep.exit_code == exits.VIOLATIONS
    assert any("build.log" in f.detail for f in rep.findings)

def test_missing_evidence_fails(tmp_git_repo):
    rep = check_branch(tmp_git_repo, base="main", evidence=["nonexistent.log"])
    assert rep.exit_code == exits.VIOLATIONS
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd hermes-devcrew && python -m pytest tests/release_harness/test_pr_hygiene_gate.py -q`
Expected: FAIL (`ImportError`)

- [ ] **Step 3: Implement the gate**

```python
# release_harness/pr_hygiene_gate.py
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
    findings: list[Finding] = field(default_factory=list)
    @property
    def exit_code(self):
        return exits.VIOLATIONS if self.findings else exits.PASS

def _git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args],
                          capture_output=True, text=True).stdout

def check_branch(repo: Path, base: str, evidence: list[str]) -> Report:
    repo = Path(repo)
    rep = Report()
    # 1) no tracked file that is also gitignored (debris that slipped in)
    tracked = _git(repo, "ls-files").splitlines()
    for path in tracked:
        ci = subprocess.run(["git", "-C", str(repo), "check-ignore", path],
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd hermes-devcrew && python -m pytest tests/release_harness/test_pr_hygiene_gate.py -q`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add release_harness/pr_hygiene_gate.py tests/release_harness/test_pr_hygiene_gate.py tests/release_harness/conftest.py
git commit -m "feat(harness): pr-hygiene-gate (debris/evidence/base checks on tmp repos)"
```

---

## Task 7: `clean-integrate`

Resolves Reviewer Concerns: lane attribution (earliest-lane is wrong; shared files belong to the integration commit), co-edit handling, escalate-on-ambiguity, per-lane commits are organizational (only branch tip is build-verified).

**Files:**
- Create: `release_harness/clean_integrate.py`
- Test: `tests/release_harness/test_clean_integrate.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/release_harness/test_clean_integrate.py
import subprocess
from release_harness.clean_integrate import reconstruct
from release_harness import exits

def _git(repo, *a):
    return subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True)

def test_reconstructs_one_commit_per_lane_strips_debris(tmp_git_repo):
    repo = tmp_git_repo
    # simulate a messy working tree: two lanes' files + one debris file
    (repo / "laneA.py").write_text("a = 1\n")
    (repo / "laneB.py").write_text("b = 2\n")
    (repo / "junk.log").write_text("debris\n")   # gitignored
    lane_map = {"t_a": ["laneA.py"], "t_b": ["laneB.py"]}
    rep = reconstruct(repo, base="main", lane_map=lane_map, branch="rel/test")
    assert rep.exit_code == exits.PASS
    # exactly two lane commits, debris NOT committed
    log = _git(repo, "log", "--oneline", "main..rel/test").stdout
    assert log.count("\n") == 2
    assert "junk.log" not in _git(repo, "ls-files").stdout

def test_unclaimed_file_escalates(tmp_git_repo):
    repo = tmp_git_repo
    (repo / "laneA.py").write_text("a=1\n")
    (repo / "orphan.py").write_text("o=1\n")  # changed but in no lane
    rep = reconstruct(repo, base="main",
                      lane_map={"t_a": ["laneA.py"]}, branch="rel/t2")
    assert rep.exit_code == exits.ESCALATE
    assert any("orphan.py" in f.detail for f in rep.findings)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd hermes-devcrew && python -m pytest tests/release_harness/test_clean_integrate.py -q`
Expected: FAIL (`ImportError`)

- [ ] **Step 3: Implement reconstruction**

```python
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
    findings: list[Finding] = field(default_factory=list)
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
        ci = subprocess.run(["git", "-C", str(repo), "check-ignore", path],
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd hermes-devcrew && python -m pytest tests/release_harness/test_clean_integrate.py -q`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add release_harness/clean_integrate.py tests/release_harness/test_clean_integrate.py
git commit -m "feat(harness): clean-integrate per-lane commits, escalate on unclaimed files"
```

---

## Task 8: CLI entry points + the full-harness smoke test

**Files:**
- Modify: `release_harness/spec_claim_verify.py`, `clean_integrate.py`, `pr_hygiene_gate.py` (add `__main__` blocks)
- Test: `tests/release_harness/test_cli.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/release_harness/test_cli.py
import subprocess, sys

def test_pr_hygiene_cli_exit_codes(tmp_git_repo):
    r = subprocess.run([sys.executable, "-m", "release_harness.pr_hygiene_gate",
                        str(tmp_git_repo), "--base", "main", "--evidence", "src.py"],
                       cwd="/Users/mustcompanymohsin/projects/mustCompany/must-dev-agents/hermes-devcrew",
                       capture_output=True, text=True)
    assert r.returncode == 0  # exits.PASS
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd hermes-devcrew && python -m pytest tests/release_harness/test_cli.py -q`
Expected: FAIL (no `__main__` / nonzero exit)

- [ ] **Step 3: Add `__main__` blocks (one shown; mirror for the other two)**

```python
# append to release_harness/pr_hygiene_gate.py
if __name__ == "__main__":
    import argparse, sys, json
    ap = argparse.ArgumentParser()
    ap.add_argument("repo"); ap.add_argument("--base", default="origin/main")
    ap.add_argument("--evidence", nargs="*", default=[])
    a = ap.parse_args()
    rep = check_branch(a.repo, a.base, a.evidence)
    print(json.dumps([f.__dict__ for f in rep.findings], indent=2))
    sys.exit(rep.exit_code)
```

(Mirror equivalent `__main__` blocks for `spec_claim_verify.py` — subcommands `plan`/`assignees` — and `clean_integrate.py`.)

- [ ] **Step 4: Run test to verify it passes**

Run: `cd hermes-devcrew && python -m pytest tests/release_harness/test_cli.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add release_harness/*.py tests/release_harness/test_cli.py
git commit -m "feat(harness): CLI entry points returning structured exit codes"
```

---

## Task 9: `release-management` skill (the judgment playbook)

The agent-layer doctrine that drives the harness at the two card touchpoints, resolving the remaining Reviewer Concerns (spec-amendment-after-decompose, draft-PR idempotency, build-command per repo, E3/§6 run-dedup).

**Files:**
- Create: `agents/integrator/skills/release-management/SKILL.md`

- [ ] **Step 1: Write the skill** (no test — it's doctrine; verified by Task 12's config test that it loads)

Create `agents/integrator/skills/release-management/SKILL.md` with `version: 1.0.0` and these sections:
- **Two card types you own:** `spec-verify` (pre-gate) and `release` (post-build).
- **spec-verify:** run `python -m release_harness.spec_claim_verify plan <spec> <repo>`; post the report as a comment + artifact; refuted-missing claims are *candidates* — surface to the human, do not hard-block; the human approves with the report in hand.
- **release:** (1) read each impl card's `Files:` via `hermes kanban show` → build the lane map; (2) run `clean_integrate`; on ESCALATE (exit 2) stop and comment — never guess; (3) re-run the repo's build/test command (read it from the repo's `release.cmd` file if present, else the spec's "Green suites" line — Reviewer Concern: build-command), tee to an evidence log; (4) run `pr_hygiene_gate` with that evidence; (5) on PASS push the branch + open a **draft** PR (idempotent: if a PR for this item is already open, update it; on auth/remote failure exit 2); never merge, never push main.
- **spec-amendment-after-decompose** (Reviewer Concern): if `spec-verify` blocks and the spec is amended after cards exist, archive the stale impl cards and re-decompose — do not build the old graph.
- **check-library duty (E1):** whenever you catch a NEW failure class not already in `release_harness/check_library.yaml`, append an entry (incident + rule + fixture) before completing. This is mandatory — it is how the harness gets stronger.
- **exit-code contract:** 0 proceed, 1 block with the findings, 2 escalate to human (never treat 2 as pass).

- [ ] **Step 2: Commit**

```bash
git add agents/integrator/skills/release-management/SKILL.md
git commit -m "docs(skill): release-management playbook driving the harness at both card gates"
```

---

## Task 10: Elevate the integrator role + config test

**Files:**
- Modify: `agents/integrator/SOUL.md`
- Test: `tests/test_release_manager_role.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_release_manager_role.py
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def test_release_management_skill_present():
    assert (ROOT / "agents/integrator/skills/release-management/SKILL.md").is_file()

def test_soul_names_the_release_manager_role_and_harness():
    soul = (ROOT / "agents/integrator/SOUL.md").read_text()
    assert "release-manager" in soul.lower()
    assert "release_harness" in soul or "pr-hygiene-gate" in soul

def test_harness_importable():
    import release_harness  # noqa
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd hermes-devcrew && python -m pytest tests/test_release_manager_role.py -q`
Expected: FAIL (soul assertions)

- [ ] **Step 3: Elevate SOUL.md**

Append a section to `agents/integrator/SOUL.md`:
> ## Elevated role: release-manager
> You are the fleet's **release-manager** (the profile keeps the name `devcrew-integrator` for dispatch continuity). Beyond synthesizing the build, you own the release-trust boundary: run the `release_harness` tools (`spec_claim_verify`, `clean_integrate`, `pr_hygiene_gate`) per the `release-management` skill. Broken build → no PR. You open a DRAFT PR only — never merge, never push `main`. A harness exit code 2 means escalate to a human; it is never a pass.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd hermes-devcrew && python -m pytest tests/test_release_manager_role.py -q`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add agents/integrator/SOUL.md tests/test_release_manager_role.py
git commit -m "feat(role): elevate integrator into the release-manager (SOUL + harness wiring)"
```

---

## Task 11: E2 — stronger model for the verification gates + eval

**Files:**
- Modify: `team.yaml:20-21,23` (reviewer, integrator, qa)
- Create: `tests/release_harness/eval_gate_model.md` (documented eval procedure — LLM judgment is not a deterministic unit test)

- [ ] **Step 1: Bump the three verification-gate roles**

In `team.yaml`, change `model: deepseek/deepseek-v4-flash` → `model: deepseek/deepseek-v4-pro` on the `devcrew-reviewer`, `devcrew-integrator`, and `devcrew-qa` lines only (leave the coder workers on flash — cost). 

- [ ] **Step 2: Write the eval procedure**

Create `tests/release_harness/eval_gate_model.md`: run each `check_library.yaml` fixture's verify-judgment prompt against flash and pro; record correct/incorrect; **pass bar: pro must be correct on ≥ all `severity: block` fixtures and strictly ≥ flash overall.** If pro does not beat flash, revert the model bump (keep flash). This is run manually / in CI, not as a unit test.

- [ ] **Step 3: Validate team.yaml still parses**

Run: `cd hermes-devcrew && python -m pytest tests/test_agent_configs.py -q`
Expected: PASS (the existing config invariants still hold with the new model string)

- [ ] **Step 4: Commit**

```bash
git add team.yaml tests/release_harness/eval_gate_model.md
git commit -m "feat(E2): verification gates (reviewer/qa/integrator) → deepseek-v4-pro + eval bar"
```

---

## Task 12: E3 — fleet-wide wiring (dev-os orchestrator + worker doctrine)

E3 lives in the dev-os repo (the orchestrator) and the kanban-worker doctrine. This task is doctrine, not code; the harness it calls already exists (Tasks 4-8).

**Files (dev-os repo):**
- Modify: `dev-os/agents/devos/skills/kanban-orchestrator/SKILL.md` (bump version)
- Modify: `dev-os/skills/devops/kanban-worker/SKILL.md` (bump version) + sync

- [ ] **Step 1: Orchestrator — run assignee validation at decompose-time + insert the spec-verify card**

Add to `kanban-orchestrator/SKILL.md`: after building the task graph, run `python -m release_harness.spec_claim_verify assignees <graph.json>` (or validate each assignee via `hermes profile list`) BEFORE creating cards; and insert a `spec-verify` card (assignee `devcrew-integrator`) as the parent of the human-approve gate. Resolve the E3/§6 dedup (Reviewer Concern): the orchestrator runs the assignee check at decompose; the `spec-verify` card runs the prose check at the gate — they are different checks, no duplication.

- [ ] **Step 2: Worker — pr-hygiene before completing**

Add to `kanban-worker/SKILL.md`: before `kanban_complete`, an impl worker runs `python -m release_harness.pr_hygiene_gate <workspace> --base origin/main --evidence <test-log>`; on exit 1, fix the debris before completing; on exit 2, escalate. (This stops debris at the source — the E3 "workers run pr-hygiene" goal.)

- [ ] **Step 3: Bump versions + sync**

Bump kanban-orchestrator to v3.12.0 and kanban-worker to v2.6.0; run `bash dev-os/scripts/sync-doctrine.sh`; verify byte-identical checksums across profile copies (the established check).

- [ ] **Step 4: Commit (dev-os repo)**

```bash
cd ../dev-os && git add agents/devos/skills/kanban-orchestrator/SKILL.md skills/devops/kanban-worker/SKILL.md
git commit -m "feat(E3): fleet-wide harness — orchestrator assignee-check + worker pr-hygiene"
```

---

## Task 13: Installer wiring + ship

**Files:**
- Modify: `install.sh` (ensure `release_harness` is importable on PATH for spawned workers)
- Modify: `VERSION`, `CHANGELOG.md`, `TODOS.md`

- [ ] **Step 1: Make the harness importable for workers**

In `install.sh`, add the hermes-devcrew repo root to the worker `PYTHONPATH` (or `pip install -e .` the harness package) so `python -m release_harness.*` resolves in every spawned worker's environment. Add a smoke check: `python -c "import release_harness"` post-install.

- [ ] **Step 2: Run the full hermes-devcrew suite**

Run: `cd hermes-devcrew && python -m pytest -q`
Expected: PASS (all release_harness tests + the existing config/closeout tests; 0 failures)

- [ ] **Step 3: Version + changelog + TODOS**

Bump `VERSION` 0.4.2 → 0.5.0; add a CHANGELOG `[0.5.0]` entry describing the release-manager + harness + E1/E2/E3; move the relevant TODOS items to Completed; record E4 + the T-B upstream-PR as remaining (Phase 2 / upstream).

- [ ] **Step 4: Commit + ship**

```bash
git add install.sh VERSION CHANGELOG.md TODOS.md
git commit -m "chore: bump version + changelog + installer wiring for the release harness (v0.5.0)"
```
Then `/ship` (tests, PR via must-mohsin1, restore gh to mohsinzahid; merge on operator word).

---

## Self-review notes (run after implementing)

- **Spec coverage:** baseline B = Tasks 1-10; E1 = Task 3 (+ skill duty in Task 9); E2 = Task 11; E3 = Task 12. E4 intentionally absent (Phase 2).
- **Reviewer Concerns mapped:** lane-map source → Task 2/7; assignee gate split → Task 4/5; build-command + PR idempotency + spec-amendment + E3/§6 dedup → Task 9; co-edit/per-lane-build → Task 7; E1 schema → Task 3.
- **Isolation:** every test uses `tmp_path`/`tmp_git_repo` — no live repo or live kanban board is touched (kanban-worker v2.5.0 rule).
- **Type consistency:** `Report.exit_code`, `Finding(kind, detail)`, `parse_files_block`, `load_library`/`Check`, `verify_spec_claims`/`verify_assignees`, `check_branch`, `reconstruct` are used consistently across tasks.
