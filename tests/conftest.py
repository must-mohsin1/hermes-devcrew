"""Fixtures for devcrew-closeout tests: a fake `hermes` CLI on PATH.

The shim logs every invocation to $HERMES_FAKE_DIR/calls.log (one JSON argv per
line) and serves canned responses:
  - `kanban list --json`  -> contents of list.json, or list_seq.json advanced one
    entry per call (for --watch tests); exit code from list_rc if present.
  - `kanban create ...`   -> {"id": "t-fix-1"}
  - everything else       -> exit 0.
"""
import importlib.machinery
import importlib.util
import json
import os
import stat
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "devcrew-closeout"

SHIM = r'''#!/usr/bin/env python3
import json, os, sys
fake = os.environ["HERMES_FAKE_DIR"]
with open(os.path.join(fake, "calls.log"), "a") as f:
    f.write(json.dumps(sys.argv[1:]) + "\n")
args = sys.argv[1:]
if args[:1] == ["kanban"]:
    args = args[1:]
if args[:2] == ["list", "--json"]:
    rc_path = os.path.join(fake, "list_rc")
    if os.path.exists(rc_path):
        sys.stderr.write("fake list failure\n")
        sys.exit(int(open(rc_path).read().strip()))
    seq_path = os.path.join(fake, "list_seq.json")
    if os.path.exists(seq_path):
        seq = json.load(open(seq_path))
        idx_path = os.path.join(fake, "list_idx")
        idx = int(open(idx_path).read()) if os.path.exists(idx_path) else 0
        open(idx_path, "w").write(str(min(idx + 1, len(seq) - 1)))
        print(json.dumps(seq[idx]))
        sys.exit(0)
    print(open(os.path.join(fake, "list.json")).read())
    sys.exit(0)
if args[:1] == ["create"]:
    print(json.dumps({"id": "t-fix-1"}))
    sys.exit(0)
if args[:1] == ["complete"]:
    rc_path = os.path.join(fake, "complete_rc")
    sys.exit(int(open(rc_path).read().strip()) if os.path.exists(rc_path) else 0)
sys.exit(0)
'''


@pytest.fixture()
def closeout():
    """Import the extensionless devcrew-closeout script as a module."""
    loader = importlib.machinery.SourceFileLoader("devcrew_closeout", str(SCRIPT))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


@pytest.fixture()
def fake_hermes(tmp_path, monkeypatch):
    """Install the shim on PATH; return the fake dir for fixtures + call assertions."""
    fake = tmp_path / "fake"
    fake.mkdir()
    bindir = tmp_path / "bin"
    bindir.mkdir()
    shim = bindir / "hermes"
    shim.write_text(SHIM, encoding="utf-8")
    shim.chmod(shim.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    monkeypatch.setenv("PATH", f"{bindir}:{os.environ['PATH']}")
    monkeypatch.setenv("HERMES_FAKE_DIR", str(fake))
    (fake / "calls.log").write_text("", encoding="utf-8")
    return fake


def calls(fake: Path) -> list[list[str]]:
    return [json.loads(line) for line in
            (fake / "calls.log").read_text(encoding="utf-8").splitlines() if line]


@pytest.fixture
def tmp_git_repo(tmp_path):
    """A throwaway git repo for release_harness tests. NEVER use a real repo or
    live board in tests (kanban-worker v2.5.0 isolation rule). Lives in the root
    conftest so it is inherited by every test dir without a colliding second
    conftest module (test_devcrew_closeout.py does `from conftest import calls`)."""
    repo = tmp_path / "repo"
    repo.mkdir()

    def g(*args):
        subprocess.run(["git", "-C", str(repo), *args], check=True,
                       capture_output=True, text=True)

    g("init", "-q")
    g("config", "user.email", "t@t")
    g("config", "user.name", "t")
    (repo / ".gitignore").write_text("*.log\nagentdb.rvf\n")
    (repo / "src.py").write_text("x = 1\n")
    g("add", ".")
    g("commit", "-q", "-m", "base")
    g("branch", "-M", "main")
    return repo
