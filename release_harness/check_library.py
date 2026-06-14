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
