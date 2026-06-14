# tests/release_harness/test_cli.py
import json
import subprocess
import sys

REPO = "/Users/mustcompanymohsin/projects/mustCompany/must-dev-agents/hermes-devcrew"


def _run(*args):
    """Invoke a harness module CLI from the repo root so `release_harness` imports."""
    return subprocess.run([sys.executable, "-m", *args], cwd=REPO,
                          capture_output=True, text=True)


def test_pr_hygiene_cli_clean_repo_is_exit_0(tmp_git_repo):
    r = _run("release_harness.pr_hygiene_gate", str(tmp_git_repo),
             "--base", "main", "--evidence", "src.py")
    assert r.returncode == 0  # exits.PASS


def test_pr_hygiene_cli_missing_evidence_is_exit_1(tmp_git_repo):
    # Genuinely discriminating: a module WITHOUT a __main__ block would exit 0,
    # so a non-zero exit here proves the CLI actually runs the gate logic.
    r = _run("release_harness.pr_hygiene_gate", str(tmp_git_repo),
             "--base", "main", "--evidence", "nonexistent.log")
    assert r.returncode == 1  # exits.VIOLATIONS
    findings = json.loads(r.stdout)
    assert any(f["kind"] == "missing-evidence" for f in findings)
