# hermes-devcrew — Design

**Date:** 2026-06-01
**Status:** Design — pending review
**Working name:** `hermes-devcrew` (rename freely)

## 1. Problem & Goal

Build a **reusable, autonomous, domain-expert software-engineering team** on top of the
[Hermes Agent](https://hermes-agent.nousresearch.com) platform, and **package it for public
distribution** so any internet user can install the same team for their own project with a
single command.

A "team" here = several Hermes **profiles** (each an isolated agent with its own persona,
skills, model, memory, and workspace) that collaborate through Hermes' shared **kanban board**
and run **autonomously** via the kanban **dispatcher daemon** (parallel workers → verifier →
synthesizer).

### Success criteria

1. A fresh machine with Hermes installed can run **one command** and end up with the full team
   installed, keys configured, kanban board initialized, and the daemon running.
2. Stating a single engineering goal ("build feature X in repo Y") results in the team
   autonomously decomposing, implementing, reviewing, and synthesizing the result — hands-off.
3. The package contains **no secrets** and works for a stranger using **their own** API key.
4. The team is **updatable** (`hermes profile update`) without clobbering the user's
   accumulated memory, sessions, or credentials.

## 2. Non-Goals (YAGNI)

- **No fine-tuning / model training.** "Domain expert" = persona + skills + memory, not weights.
- **No custom orchestrator.** We use Hermes' native kanban swarm + daemon, not a new engine.
- **No private model hosting.** Users bring their own OpenRouter key.
- **No GUI.** CLI + messaging gateway only (gateway is optional for end users).
- **v1 is not multi-tenant SaaS.** It's a self-host package. (Hermes kanban has `--tenant`; we
  leave the hooks in but don't build a hosted service.)

## 3. Key Platform Findings (constraints that shape the design)

Researched from the installed Hermes source (`~/.hermes/hermes-agent`,
`hermes_cli/profile_distribution.py`) and CLI:

1. **Distributions are per-profile.** One agent = one git repo (or local dir) containing a
   `distribution.yaml` manifest. Installed via `hermes profile install <source>`.
   **There is no native multi-profile "team" package and no post-install hook.**
   → A team must ship as **N profile distributions + a bootstrap script** that installs them
   and wires up the board/daemon.

2. **What ships vs. what doesn't** (critical):
   - **Distribution-owned (ships, replaced on update):** `SOUL.md`, `config.yaml`
     (preserved on update unless `--force-config`), `mcp.json`, `skills/`, `cron/`,
     `distribution.yaml`.
   - **User-owned (never touched, never shipped):** `memories/`, `sessions/`, `state.db`,
     `auth.json`, `.env`, `logs/`, `workspace/`, `home/`, `plans/`, `*_cache/`, `local/`.
   - **Implication:** Expertise that must travel has to live in **`SOUL.md` + `skills/` + `cron/`**.
     You cannot "teach" an agent via accumulated memory and expect it to ship — a stranger's
     install starts with empty memory.

3. **Secrets are declared, not shipped.** The manifest's `env_requires:` lists required/optional
   env vars (name, description, required, default). The installer supplies their own values into
   the user-owned `.env`. This is the secure portability model.

4. **Manifest schema** (`distribution.yaml` at profile root):
   ```yaml
   name: backend-dev
   version: 0.1.0
   description: "Backend implementation specialist"
   hermes_requires: ">=0.14.0"
   author: "..."
   license: "MIT"
   env_requires:
     - name: OPENROUTER_API_KEY
       description: "OpenRouter API key — powers all team models"
       required: true
   distribution_owned:        # optional; sensible defaults apply
     - SOUL.md
     - config.yaml
     - skills/
     - cron/
   ```

5. **Native team primitives already exist:**
   - `hermes kanban init` / `boards` — durable SQLite board shared across profiles.
   - `hermes kanban swarm "<goal>" --worker P:TITLE:SKILLS … --verifier P --synthesizer P`
     — builds a parallel-workers → verifier → synthesizer graph in one call.
   - `hermes kanban decompose` / `specify` — break a goal into tasks.
   - `hermes kanban assign / link / claim` — assignment + dependencies + atomic claims.
   - `hermes kanban daemon` / `dispatch` / `watch` — autonomous execution; each task runs as
     its assigned profile in an isolated workspace.
   - `hermes cron` — per-profile recurring routines.
   - `hermes skills install` + `hermes bundles` — install skill packs; group them per role.

## 4. Architecture

### 4.1 Repository layout (monorepo + installer)

```
hermes-devcrew/
├── install.sh              # bootstrap (the one-liner target)
├── team.yaml               # OUR manifest: roster + swarm topology + board name
├── README.md               # curl|bash one-liner, prerequisites, usage
├── LICENSE                 # MIT
├── VERSION                 # team package version (semver)
├── docs/
│   ├── superpowers/specs/  # this design doc lives here
│   └── usage.md            # how to drive the team (goals, swarm, daemon)
├── shared-skills/          # skill packs reused by multiple agents (copied in at build)
└── agents/
    ├── architect/          # each subdir is a full profile distribution
    │   ├── distribution.yaml
    │   ├── SOUL.md
    │   ├── config.yaml
    │   └── skills/
    ├── backend-dev/
    ├── frontend-dev/
    ├── devops/
    ├── reviewer/
    ├── integrator/
    └── domain-expert/      # customizable template slot for the user's codebase
```

Each `agents/<role>/` contains `distribution.yaml` at its root, so it is independently
installable via `hermes profile install ./agents/<role>` — the bootstrap just loops over them.

### 4.2 Install flow

End-user one-liner (clones, then runs the local installer):

```bash
curl -fsSL https://raw.githubusercontent.com/<owner>/hermes-devcrew/main/install.sh | bash
```

`install.sh` responsibilities (idempotent):

1. **Preflight** — verify `hermes` is installed and `hermes --version` satisfies
   `hermes_requires`; if missing, print the Hermes install one-liner and exit.
2. **Clone/locate** the monorepo (if piped, clone to a temp/`~/.hermes-devcrew-src`).
3. **Keys** — read each agent manifest's `env_requires`, prompt once for the union
   (primarily `OPENROUTER_API_KEY`), write into each installed profile's user-owned `.env`.
4. **Install agents** — for each `agents/<role>`:
   `hermes profile install ./agents/<role> --name <role> --yes` (`--force` on reinstall).
5. **Board** — `hermes kanban init`; create a board named after the user's project
   (`hermes kanban boards create <project>`); register assignees.
6. **Daemon (autonomous mode)** — start `hermes kanban daemon` (optionally as a managed
   background process / launchd). Print how to stop it.
7. **Smoke check** — `hermes profile list` shows all agents; print next-step usage.

### 4.3 Roster → swarm mapping (hybrid)

`hermes kanban swarm "<goal>" --created-by architect --worker backend-dev:… --worker
frontend-dev:… --worker devops:… --verifier reviewer --synthesizer integrator`

| Agent | Swarm role | Baked-in expertise (SOUL + skills) | Model tier |
|---|---|---|---|
| **architect** | anchor / decomposer (`--created-by`) | system design, task decomposition, planning doctrine | strong |
| **backend-dev** | worker | `software-development`, `rest-graphql-debug`, language packs | mid |
| **frontend-dev** | worker | `web-development` | mid |
| **devops** | worker | `devops` (docker, CI/CD, deploy) | mid |
| **reviewer** | **verifier** | `security` + code-review doctrine; refuses on uncertainty | strong |
| **integrator** | **synthesizer** | merges worker output, resolves conflicts, writes PR/docs | strong |
| **domain-expert** | worker (customizable) | template SOUL the installer fills in for THEIR codebase; installer adds domain skills + points workspace at their repo | mid |

The **domain-expert** slot is what makes this "hybrid" and reusable: the role-based core is
generic, while the domain-expert is the per-project specialist each installer customizes.

### 4.4 Autonomous execution model

1. User states a goal (CLI, or via gateway from Discord/WhatsApp/Slack).
2. `architect` decomposes it onto the board (`kanban decompose`/`specify`), linking dependencies.
3. `kanban daemon` promotes ready tasks and dispatches each to its assigned profile, running in
   an **isolated workspace** (worktree). Workers run in parallel up to a concurrency cap.
4. `reviewer` (verifier) gates worker output; failures are commented and re-queued.
5. `integrator` (synthesizer) merges verified output into the final deliverable (branch/PR/docs).
6. Daemon idles until the next goal; `cron` routines (e.g., nightly dep audit) run on schedule.

**Guardrails (defaults):** workers operate in isolated workspaces (no shared mutation); reviewer
must pass before synthesis; concurrency cap; `--yolo` is **off** by default (destructive ops and
network publishing require the user's configured policy); the daemon writes an auditable event
stream (`kanban tail`/`log`).

## 5. Model / Provider Strategy (OpenRouter + open defaults)

- **One key unlocks the team:** `OPENROUTER_API_KEY` is the single required env var.
- **Per-role defaults in each `config.yaml`:** strong-tier model for architect/reviewer/integrator,
  a faster/cheaper mid-tier for the workers. Exact OpenRouter model slugs are finalized during
  implementation (validated against `hermes model` / models cache, with a documented fallback).
- **Overridable:** users can run `hermes --profile <role> model` to swap any agent's model;
  `config.yaml` is preserved on `profile update` unless `--force-config`.
- **Optional fallbacks:** `fallback_providers` can be pre-populated so rate limits/outages degrade
  gracefully (kept minimal in v1).

## 6. Security & Portability

- **No secrets in the repo.** `.env`, `auth.json` are user-owned; manifests only *declare*
  `env_requires`. A pre-publish check (CI) greps the tree for key-shaped strings and fails on any.
- **Skill provenance.** Bundled skills come from the audited `optional-skills/` library or pinned
  sources; skills with native deps (pip/npm) declare them and the installer surfaces them.
- **Least privilege.** Default tool policy is conservative; publishing/destructive actions are
  opt-in. Document the trust model prominently in the README.
- **Updatable & non-destructive.** `hermes profile update <role>` re-pulls distribution-owned
  files only; user memory/sessions/keys survive.

## 7. Risks & Open Questions

| # | Risk / question | Mitigation / note |
|---|---|---|
| R1 | No post-install hook → wiring must be a separate script | `install.sh` owns wiring; documented + idempotent |
| R2 | Skill native deps (pip/npm) may not auto-install on a stranger's box | Declare deps; installer checks; prefer dependency-light skills in v1 |
| R3 | OpenRouter model slugs drift / get deprecated | Pin + provide fallback; `hermes migrate` handles retired models |
| R4 | Autonomous daemon doing destructive/networked actions unsupervised | `--yolo` off by default; isolated workspaces; reviewer gate; audit log |
| R5 | `hermes_requires` floor vs. user's installed version | Preflight check in `install.sh` with a clear upgrade message |
| R6 | Monorepo subdir install relies on local-dir install semantics | Confirmed: `<source>` may be a local dir containing `distribution.yaml` |
| Q1 | Final v1 agent count — ship all 7, or a leaner core first? | Proposal: build/validate 1 agent, then the full 7 |
| Q2 | Publish target (GitHub owner/repo) + brand name | Needed before the public one-liner is real |

## 8. Build Phases (for the implementation plan)

1. **Spike one agent end-to-end.** Author `agents/backend-dev` (manifest + SOUL + config + one
   skill), `hermes profile install ./agents/backend-dev`, run a trivial task. Proves the loop.
2. **Full roster.** Author the remaining role agents + the `domain-expert` template; pick skill
   bundles + per-role model defaults.
3. **Bootstrap.** Write `install.sh` (preflight, keys, install loop, kanban init, daemon) +
   `team.yaml` + README one-liner. Make idempotent.
4. **Autonomy validation.** Drive a real multi-step goal through the swarm + daemon end-to-end;
   confirm worker → verifier → synthesizer flow and the audit trail.
5. **Release hardening.** Secret-scan CI, versioning (`VERSION` + git tags), `profile update`
   test, LICENSE, docs/usage.md, publish to GitHub, verify the public one-liner on a clean env.

## 9. Out-of-the-box usage (post-install)

```bash
# one autonomous goal:
hermes kanban swarm "Add OAuth login to ./myapp and tests" \
  --created-by architect \
  --worker backend-dev:"Implement OAuth endpoints":software-development \
  --worker frontend-dev:"Login UI":web-development \
  --verifier reviewer --synthesizer integrator

# or hand the goal to the architect and let the daemon run the board:
hermes --profile architect -z "Plan and execute: add OAuth to ./myapp"
hermes kanban daemon         # autonomous dispatch
hermes kanban tail           # watch the team work
```
