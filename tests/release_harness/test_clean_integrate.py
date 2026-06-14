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
