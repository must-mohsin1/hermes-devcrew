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

def test_non_git_dir_escalates(tmp_path):
    # a gate that cannot inspect the repo must ESCALATE (2), never false-clean PASS
    rep = check_branch(tmp_path, base="main", evidence=[])
    assert rep.exit_code == exits.ESCALATE
    assert any(f.kind == "not-a-work-tree" for f in rep.findings)

def test_unresolvable_base_escalates(tmp_git_repo):
    # origin/main on a repo with no remote fetched: freshness is unverifiable, so
    # escalate rather than silently passing (the verify_code_landed lesson).
    rep = check_branch(tmp_git_repo, base="origin/main", evidence=["src.py"])
    assert rep.exit_code == exits.ESCALATE
    assert any(f.kind == "base-unresolvable" for f in rep.findings)
