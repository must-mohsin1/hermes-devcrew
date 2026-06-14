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
