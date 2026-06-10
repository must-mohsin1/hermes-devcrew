"""devcrew-closeout behavior: detect blocked/review cards, verify with a REAL check,
resolve on green, file ONE watchdog-compatible fix card on red, refuse to act blind."""
import json

from conftest import calls


def _card(tid, status, kind="dir", path=None, title=None, body="", result=""):
    return {"id": tid, "title": title or f"card {tid}", "body": body, "result": result,
            "status": status, "assignee": "devcrew-backend-dev",
            "workspace_kind": kind, "workspace_path": path}


def _board(fake, tasks):
    (fake / "list.json").write_text(json.dumps(tasks), encoding="utf-8")


# --- pure helpers -----------------------------------------------------------

def test_board_slug_for_repo(closeout):
    assert closeout.board_slug_for_repo("/srv/wt/run-abc123") == "run-abc123"
    assert closeout.board_slug_for_repo("/x/My Repo") == "my-repo"


def test_autodetect_pnpm_build(closeout, tmp_path):
    (tmp_path / "package.json").write_text(json.dumps({"scripts": {"build": "x"}}))
    (tmp_path / "pnpm-lock.yaml").write_text("")
    assert closeout.autodetect_check(str(tmp_path)) == ["pnpm", "run", "build"]


def test_autodetect_npm_then_tsc_then_pytest_then_none(closeout, tmp_path):
    (tmp_path / "package.json").write_text(json.dumps({"scripts": {"build": "x"}}))
    assert closeout.autodetect_check(str(tmp_path)) == ["npm", "run", "build"]
    (tmp_path / "package.json").unlink()
    (tmp_path / "tsconfig.json").write_text("{}")
    assert closeout.autodetect_check(str(tmp_path)) == ["npx", "tsc", "--noEmit"]
    (tmp_path / "tsconfig.json").unlink()
    (tmp_path / "pyproject.toml").write_text("")
    assert closeout.autodetect_check(str(tmp_path)) == ["pytest", "-q"]
    (tmp_path / "pyproject.toml").unlink()
    assert closeout.autodetect_check(str(tmp_path)) is None


# --- main paths (through the shim) ------------------------------------------

def test_nothing_to_resolve(closeout, fake_hermes, tmp_path, capsys):
    _board(fake_hermes, [_card("t1", "done")])
    rc = closeout.main(["--repo", str(tmp_path), "--json"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0 and out["status"] == "ok" and out["resolved"] == []


def test_green_path_unblocks_comments_completes(closeout, fake_hermes, tmp_path, capsys):
    repo = str(tmp_path)
    _board(fake_hermes, [_card("t1", "blocked", path=repo),
                         _card("t2", "review", path=repo),
                         _card("t3", "done", path=repo)])
    rc = closeout.main(["--repo", repo, "--check", "exit 0", "--json"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0 and out["status"] == "ok" and sorted(out["resolved"]) == ["t1", "t2"]
    got = calls(fake_hermes)
    flat = [" ".join(c) for c in got]
    assert any(c[:2] == ["kanban", "comment"] and "t1" in c for c in got)
    assert any(c[:2] == ["kanban", "unblock"] and "t1" in c for c in got)
    assert any(c[:2] == ["kanban", "complete"] and "t1" in c for c in got)
    assert any(c[:2] == ["kanban", "complete"] and "t2" in c for c in got)
    # review cards are completed but never unblocked
    assert not any(c[:2] == ["kanban", "unblock"] and "t2" in c for c in got)
    assert not any("t3" in s for s in flat if "complete" in s or "unblock" in s)


def test_red_path_files_one_watchdog_compatible_fix_card(closeout, fake_hermes,
                                                         tmp_path, capsys):
    repo = str(tmp_path)
    _board(fake_hermes, [_card("t1", "blocked", path=repo)])
    rc = closeout.main(["--repo", repo, "--check", "exit 3", "--json"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 1 and out["status"] == "check-failed" and out["fix_card"] == "t-fix-1"
    creates = [c for c in calls(fake_hermes) if c[:2] == ["kanban", "create"]]
    assert len(creates) == 1
    create = creates[0]
    title = create[2]
    assert "t1" in title                      # watchdog dedup: ids in the TITLE
    assert "fix" in title.lower()             # matches watchdog REMEDIATION_RE
    assert "--assignee" in create and "devcrew-integrator" in create
    assert "--idempotency-key" in create
    # no card was completed or unblocked on a red check
    assert not any(c[:2] == ["kanban", "complete"] for c in calls(fake_hermes))
    assert not any(c[:2] == ["kanban", "unblock"] for c in calls(fake_hermes))


def test_red_path_skips_when_active_fix_exists(closeout, fake_hermes, tmp_path, capsys):
    repo = str(tmp_path)
    fix = _card("t9", "ready", title="Fix build check failure on x — cards t1 (auto-closeout)")
    _board(fake_hermes, [_card("t1", "blocked", path=repo), fix])
    rc = closeout.main(["--repo", repo, "--check", "exit 3", "--json"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 1 and out["fix_card"] is None
    assert not any(c[:2] == ["kanban", "create"] for c in calls(fake_hermes))


def test_report_only_without_check_or_workdir(closeout, fake_hermes, tmp_path, capsys):
    _board(fake_hermes, [_card("t1", "blocked", kind="scratch", path=None)])
    rc = closeout.main(["--board", "some-board", "--json"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0 and out["status"] == "report-only"
    assert not any(c[:2] == ["kanban", "complete"] for c in calls(fake_hermes))


def test_broken_check_is_exit_2_not_a_fix_card(closeout, fake_hermes, tmp_path, capsys):
    repo = str(tmp_path)
    _board(fake_hermes, [_card("t1", "blocked", path=repo)])
    rc = closeout.main(["--repo", repo, "--check",
                        "definitely-not-a-real-command-9x7", "--json"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 2 and out["status"] == "error"
    assert not any(c[:2] == ["kanban", "create"] for c in calls(fake_hermes))


def test_dry_run_mutates_nothing(closeout, fake_hermes, tmp_path, capsys):
    repo = str(tmp_path)
    _board(fake_hermes, [_card("t1", "blocked", path=repo)])
    rc = closeout.main(["--repo", repo, "--check", "exit 0", "--dry-run", "--json"])
    assert rc == 0
    mutating = [c for c in calls(fake_hermes)
                if c[:2] in (["kanban", "comment"], ["kanban", "unblock"],
                             ["kanban", "complete"], ["kanban", "create"])]
    assert mutating == []


def test_watch_waits_for_quiescence(closeout, fake_hermes, tmp_path, capsys):
    repo = str(tmp_path)
    busy = [_card("t1", "running", path=repo)]
    quiet = [_card("t1", "blocked", path=repo)]
    (fake_hermes / "list_seq.json").write_text(json.dumps([busy, busy, quiet]))
    rc = closeout.main(["--repo", repo, "--check", "exit 0", "--watch",
                        "--poll", "0", "--timeout", "30", "--json"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0 and out["resolved"] == ["t1"]


def test_watch_timeout_is_exit_2(closeout, fake_hermes, tmp_path, capsys):
    repo = str(tmp_path)
    _board(fake_hermes, [_card("t1", "running", path=repo)])
    rc = closeout.main(["--repo", repo, "--watch", "--poll", "0",
                        "--timeout", "0", "--json"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 2 and out["status"] == "error"


def test_list_failure_is_exit_2(closeout, fake_hermes, tmp_path, capsys):
    (fake_hermes / "list_rc").write_text("3")
    rc = closeout.main(["--repo", str(tmp_path), "--json"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 2 and out["status"] == "error"


def test_active_fix_id_prefix_does_not_false_skip(closeout, fake_hermes, tmp_path, capsys):
    """t-1 must not be considered covered by a fix card that mentions only t-12."""
    repo = str(tmp_path)
    fix = _card("t9", "ready",
                title="Fix build check failure on x — cards t-12 (auto-closeout)")
    _board(fake_hermes, [_card("t-1", "blocked", path=repo), fix])
    rc = closeout.main(["--repo", repo, "--check", "exit 3", "--json"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 1 and out["fix_card"] == "t-fix-1"
    assert any(c[:2] == ["kanban", "create"] for c in calls(fake_hermes))


def test_green_partial_failure_when_complete_fails(closeout, fake_hermes, tmp_path, capsys):
    repo = str(tmp_path)
    (fake_hermes / "complete_rc").write_text("5")
    _board(fake_hermes, [_card("t1", "blocked", path=repo)])
    rc = closeout.main(["--repo", repo, "--check", "exit 0", "--json"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 2 and out["status"] == "partial"
    assert out["resolved"] == [] and out["failed"] == ["t1"]


def test_permission_denied_check_is_broken(closeout, tmp_path):
    script = tmp_path / "not-executable.sh"
    script.write_text("#!/bin/sh\nexit 0\n")
    script.chmod(0o644)
    kind, code, tail = closeout.run_check([str(script)], str(tmp_path))
    assert kind == "broken"


def test_fix_card_title_truncates_after_five_ids(closeout, fake_hermes, tmp_path, capsys):
    repo = str(tmp_path)
    cards = [_card(f"t-{i}", "blocked", path=repo) for i in range(1, 8)]  # 7 cards
    _board(fake_hermes, cards)
    rc = closeout.main(["--repo", repo, "--check", "exit 3", "--json"])
    assert rc == 1
    creates = [c for c in calls(fake_hermes) if c[:2] == ["kanban", "create"]]
    assert len(creates) == 1
    title = creates[0][2]
    body = creates[0][creates[0].index("--body") + 1]
    assert "+2 more" in title
    assert sum(1 for i in range(1, 8) if f"t-{i}" in title.split("(auto-closeout)")[0]) == 5
    assert all(f"t-{i}" in body for i in range(1, 8))
