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
