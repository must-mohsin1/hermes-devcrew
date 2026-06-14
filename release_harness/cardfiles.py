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
