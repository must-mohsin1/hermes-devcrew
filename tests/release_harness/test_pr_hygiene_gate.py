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
