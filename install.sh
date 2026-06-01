#!/usr/bin/env bash
# hermes-devcrew installer — stands up an autonomous, hybrid software-engineering
# team on the Hermes agent platform.
#
# Usage:
#   ./install.sh                     install all agents + init the kanban board
#   ./install.sh --daemon            also start the autonomous dispatcher
#   ./install.sh --with-skill-packs  also install standard skill packs (needs network)
#   ./install.sh --help
#
# Environment:
#   OPENROUTER_API_KEY   pre-supply the key (skips the prompt)
#   DEVCREW_SKIP_KEYS=1  do not prompt for / write any key
#   DEVCREW_BOARD        kanban board name (default: devcrew)
#   DEVCREW_REPO         git URL to clone when run via `curl | bash`
#   HERMES_HOME          Hermes root (default: ~/.hermes)
set -euo pipefail

DEVCREW_REPO="${DEVCREW_REPO:-https://github.com/must-mohsin1/hermes-devcrew}"
BOARD="${DEVCREW_BOARD:-devcrew}"
MIN_HERMES="0.12.0"
WITH_SKILL_PACKS=0
START_DAEMON=0

for a in "${@:-}"; do
  case "$a" in
    --with-skill-packs) WITH_SKILL_PACKS=1 ;;
    --daemon)           START_DAEMON=1 ;;
    -h|--help)          grep '^#' "$0" | grep -v '^#!' | sed 's/^#\{1,\} \{0,1\}//'; exit 0 ;;
    "")                 ;;
    *)                  echo "unknown option: $a" >&2; exit 2 ;;
  esac
done

say()  { printf '\033[1;36m▸ %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m! %s\033[0m\n' "$*" >&2; }
die()  { printf '\033[1;31m✗ %s\033[0m\n' "$*" >&2; exit 1; }

# --- 1) Preflight -----------------------------------------------------------
command -v hermes >/dev/null 2>&1 || die "Hermes not found. Install it from \
https://hermes-agent.nousresearch.com/docs/ then re-run."
command -v git >/dev/null 2>&1 || die "git is required."

HV="$(hermes --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || true)"
say "Hermes detected: ${HV:-unknown}"
ver_lt() { [ "$(printf '%s\n%s\n' "$1" "$2" | sort -t. -k1,1n -k2,2n -k3,3n | head -1)" = "$1" ] && [ "$1" != "$2" ]; }
if [ -n "$HV" ] && ver_lt "$HV" "$MIN_HERMES"; then
  warn "Hermes $HV is below the recommended $MIN_HERMES — run 'hermes update' if anything misbehaves."
fi

# --- 2) Locate the repo (clone if piped through curl|bash) ------------------
SRC=""
if [ -n "${BASH_SOURCE:-}" ] && [ -f "${BASH_SOURCE:-}" ]; then
  SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fi
if [ -z "$SRC" ] || [ ! -d "$SRC/agents" ]; then
  say "Fetching $DEVCREW_REPO"
  TMP="${HOME}/.hermes-devcrew-src"
  if [ -d "$TMP/.git" ]; then (cd "$TMP" && git pull --ff-only -q) || true
  else git clone -q "$DEVCREW_REPO" "$TMP"; fi
  SRC="$TMP"
fi
[ -d "$SRC/agents" ] || die "Could not locate agents/ under $SRC"
say "Source: $SRC"

# --- 3) Discover agents -----------------------------------------------------
AGENT_DIRS="$(find "$SRC/agents" -mindepth 1 -maxdepth 1 -type d | sort)"
[ -n "$AGENT_DIRS" ] || die "No agents found under $SRC/agents"

# --- 4) Key handling --------------------------------------------------------
HERMES_HOME_DIR="${HERMES_HOME:-$HOME/.hermes}"
KEY="${OPENROUTER_API_KEY:-}"
if [ "${DEVCREW_SKIP_KEYS:-0}" != "1" ] && [ -z "$KEY" ]; then
  if [ -e /dev/tty ]; then
    printf 'Enter OPENROUTER_API_KEY (hidden; blank to set later): '
    read -r -s KEY </dev/tty || true; echo
  else
    warn "No TTY for prompt — set OPENROUTER_API_KEY in each profile later, or re-run with the env var."
  fi
fi
write_key() {  # $1 = profile name
  [ -n "$KEY" ] || return 0
  pdir="$HERMES_HOME_DIR/profiles/$1"; [ -d "$pdir" ] || return 0
  envf="$pdir/.env"; touch "$envf"
  grep -q '^OPENROUTER_API_KEY=' "$envf" 2>/dev/null || printf 'OPENROUTER_API_KEY=%s\n' "$KEY" >> "$envf"
}

# --- 5) Install each agent --------------------------------------------------
INSTALLED=""
for d in $AGENT_DIRS; do
  name="$(grep -E '^name:' "$d/distribution.yaml" | head -1 | sed 's/^name:[[:space:]]*//' | tr -d '"'"'"' ')"
  [ -n "$name" ] || { warn "skip $d (no name in distribution.yaml)"; continue; }
  say "Installing $name"
  if hermes profile install "$d" --yes >/dev/null 2>&1 \
     || hermes profile install "$d" --force --yes >/dev/null 2>&1; then
    write_key "$name"
    INSTALLED="$INSTALLED $name"
  else
    warn "install failed: $name"
  fi
done
[ -n "$INSTALLED" ] || die "No agents installed."
say "Installed:$INSTALLED"

# --- 5b) Orchestrator routing descriptions (consumed by the kanban orchestrator) ---
say "Setting orchestrator descriptions"
for d in $AGENT_DIRS; do
  role="$(basename "$d")"; name="devcrew-$role"
  case "$role" in
    architect)     desc="Lead architect & decomposer: plans goals into verifiable task graphs, designs systems, sets acceptance criteria. Swarm anchor." ;;
    backend-dev)   desc="Backend specialist: APIs, services, data models, business logic, backend tests (test-first)." ;;
    frontend-dev)  desc="Frontend specialist: web UI, components, state, styling, forms, accessibility." ;;
    devops)        desc="DevOps specialist: containers, CI/CD, infrastructure-as-code, deploys, observability (reversible, least-privilege)." ;;
    reviewer)      desc="Verifier: adversarial review for correctness and security; the quality gate before integration." ;;
    integrator)    desc="Synthesizer: merges verified work into one coherent deliverable, resolves conflicts, writes PR/docs." ;;
    domain-expert) desc="Project specialist: deep knowledge of this codebase's conventions, invariants, and gotchas. Customizable." ;;
    *)             desc="" ;;
  esac
  [ -n "$desc" ] && hermes profile describe "$name" --text "$desc" >/dev/null 2>&1 || true
done

# --- 6) Optional standard skill packs (best effort; bundled skills are the baseline) ---
# Every agent already ships a bundled, always-available skill. These registry packs are a
# best-effort enhancement — if a name isn't in the user's skill registry, we skip it quietly.
if [ "$WITH_SKILL_PACKS" = "1" ]; then
  for d in $AGENT_DIRS; do
    role="$(basename "$d")"; name="devcrew-$role"
    case "$role" in
      architect|backend-dev|integrator) packs="software-development" ;;
      frontend-dev)                      packs="web-development" ;;
      devops)                            packs="devops" ;;
      reviewer)                          packs="red-teaming software-development" ;;
      domain-expert)                     packs="research" ;;
      *)                                 packs="" ;;
    esac
    for p in $packs; do
      if hermes --profile "$name" skills install "$p" --yes >/dev/null 2>&1; then
        say "skills: $name += $p"
      else
        echo "  · skills: '$p' not in registry — $name uses its bundled skill (fine)"
      fi
    done
  done
fi

# --- 7) Kanban board --------------------------------------------------------
say "Initializing kanban board: $BOARD"
hermes kanban init >/dev/null 2>&1 || true
hermes kanban boards create "$BOARD" >/dev/null 2>&1 || true

# --- 7b) Turnkey runner -----------------------------------------------------
RUNNER="$SRC/devcrew-run"
RUN_HINT="./devcrew-run"
if [ -f "$RUNNER" ]; then
  chmod +x "$RUNNER" 2>/dev/null || true
  if [ -d "$HOME/.local/bin" ]; then
    ln -sf "$RUNNER" "$HOME/.local/bin/devcrew-run" 2>/dev/null && RUN_HINT="devcrew-run" \
      && say "Linked devcrew-run -> ~/.local/bin/devcrew-run"
  fi
fi

# --- 8) Optional autonomous dispatcher -------------------------------------
if [ "$START_DAEMON" = "1" ]; then
  say "Starting kanban dispatcher (autonomous mode)"
  hermes kanban daemon >/dev/null 2>&1 &
  echo "  daemon pid: $! (stop with: kill $!)"
fi

cat <<DONE

✅ hermes-devcrew is installed.
   Agents:$INSTALLED
   Board:  $BOARD
$([ -z "$KEY" ] && echo "   NOTE: no key set — run 'hermes --profile devcrew-architect auth add openrouter' before use." || true)

Drive the crew — one command:
  $RUN_HINT "Add OAuth login to the API" /path/to/repo
  hermes kanban tail        # watch the crew work

  ($RUN_HINT briefs the architect to decompose the goal onto the board, then
   runs the dispatcher. Flags: --swarm (fixed parallel fan-out), --no-daemon (stage only).)

Manual / advanced:
  hermes kanban swarm "<goal>" --created-by devcrew-architect \\
    --worker devcrew-backend-dev:"<task>" --verifier devcrew-reviewer \\
    --synthesizer devcrew-integrator
  hermes kanban daemon --verbose
DONE
