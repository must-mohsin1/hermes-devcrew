# Design — devos Release-Manager: trustworthy build→PR (Phase 1)

Date: 2026-06-13
Status: APPROVED (design) — pending implementation plan
Author: operator brainstorming session
Scope: Phase 1 of a 3-phase program to transfer operator-grade release expertise into the devos fleet.

---

## 1. Context & motivation

The control-plane is a multi-tenant SaaS (signup → org → team → agents → dashboard →
billing/observability). The devos fleet's value proposition is **autonomously shipping
features to it**. So the binding constraint is not "generate features faster" — the
devos already generates working features — it is **trust at the point where work
reaches `main`/prod.**

Unsupervised this session, the devos on its own would have (and in two cases did):

- **merged a broken build to `main`** (Item 12's `composition-shape` import with no
  committed file — `main`'s clean build was broken for hours).
- **shipped a false-premise spec lane** (Item 13 A1 claimed a route was "missing"
  when it existed; building it would have produced dead code).
- **pushed 18 worker-debris files into a PR** that then merged to `main` (a worker's
  `git add -A`, commit `3c62c38`).
- **attempted to push unreviewed security changes** outward (Item 12 integrator).
- mid-build: created phantom-assignee cards, double-decomposed, and spawned 4 workers
  into one shared git tree.

For a SaaS the first four are catastrophic (broken/insecure `main`, wasted spend); the
speed issues are a rounding error by comparison. Nearly all the operator value added
this session was at the **gate → integration → release** boundary, and — critically —
it came from **mechanical verification** (`grep`/`git`/build checks), not intuition.
Every catch was a check, not a hunch.

**Lesson that shapes the design:** doctrine alone is insufficient. The orchestrator
already carried the v3.10.0 same-tree and sole-decomposer rules and *still*
double-decomposed and spawned same-tree. Reading a rule ≠ following it. The transfer
must be backed by deterministic checks, not just a better prompt.

## 2. Goal (Phase 1)

The devos turns an approved spec into a **clean, verified, reviewable PR with no
operator babysitting** — so the human's only manual steps are (a) approving the spec
at the plan gate and (b) merging the final PR. Everything reaching those gates is
mechanically verified clean, build-green, and secure.

## 3. Non-goals (Phase 1)

- **Kernel/dispatcher enforcement** of the mechanical invariants (same-tree
  serialization at dispatch, deepened evidence gates) — that is **Phase 2**.
  Phase 1 gives the release-manager the doctrine + harness to *catch* these like the
  operator did; Phase 2 makes the kernel *prevent* them. (The CEO review briefly pulled
  the debris-guard forward as E4, then the spec review found it collides with
  `checkpoint_manager`'s `git add -A` and is "common case only" — so D3 returned E4 to
  Phase 2, where it pairs with the structured `files` card field. See §11.)
- **Throughput optimization** (parallelism, retry economics, budgeting) — **Phase 3**.
- Auto-merging or pushing to `main` — never, in any phase.
- NLP-parsing arbitrary spec prose — the verifier targets *checkable* assertions only.
- New product features; no control-plane behavior change.

## 4. Architecture

The transferred expertise lives at **two touchpoints**:

1. **Pre-build (plan gate):** verify the spec's factual claims against the code
   *before* the human approves.
2. **Post-build (integration):** reconstruct clean per-lane commits, strip debris,
   verify the build, prepare the PR, hold the merge.

Phase 1 introduces **one role that owns both**, by **elevating the existing
`integrator` into a `release-manager`** (no 10th crew role — the integrator already
sits gated on reviewer+QA, the correct position). It handles two card types.

Resulting per-item kanban graph (★ = release-manager cards):

```
research → plan → ★spec-verify → [HUMAN GATE] → impl lanes (chained per same-tree rule)
                                                     → reviewer ∥ QA
                                                         → ★release → [HUMAN PR APPROVAL]
```

The push stays human-gated at both ends. This is the SaaS operating model:
autonomous dev, human approves the spec and merges the PR.

## 5. Components

Four pieces — one role, three deterministic tools it is *required* to run. All three
tools ship in **hermes-devcrew** (they travel with the crew); the role references them
via a new `release-management` skill.

### 5.1 `devcrew-release-manager` agent (elevated from `integrator`)
- **Does:** owns both touchpoints; runs the harness; exercises judgment only on what
  the harness cannot decide; escalates or holds otherwise.
- **Interface:** handles `spec-verify` (pre-gate) and `release` (post-build) cards.
  Full tool access (terminal/file/git/kanban); retains the integrator's turn budget.
- **Depends on:** the `release-management` skill (judgment playbook — the
  verify/reconstruct/classify/escalate patterns from this session) + the three tools.

### 5.2 `spec-claim-verify` (script)
- **Does:** extracts the spec's *checkable* assertions and proves/refutes each against
  the code: file/route existence ("X is missing"), `file:line` symbol refs, and every
  assignee in the decomposition table (resolves to a real profile?). Outputs a
  pass/fail/uncheckable table with evidence.
- **Interface:** `spec-claim-verify <spec-file> <repo-path>` → report + exit code.
- **Two gates, two artifacts (CORRECTED per CEO review):** the two headline catches do
  NOT fire at one gate.
  - *Plan gate (against the planner spec):* grep-able `file`/`symbol`/"missing/exists"
    claims in spec prose — the A1 false-premise class. The spec is prose, not
    structured, so this check is genuinely fuzzy: it flags *candidates* for the human
    (fail-open with a clear report), not hard refutations.
  - *Decompose-time (against the architect's task graph, part of E3):* assignee
    validation — every card's assignee resolves to a real profile via the **same**
    `profiles.profile_exists` path the dispatcher uses (do not reimplement). This is
    the phantom-assignee class. It cannot run at the plan gate (the plan spec has no
    assignee table — assignees are the architect's later output).
  The earlier draft's claim that one gate "auto-catches A1 AND phantom assignees" was
  wrong; they are two different checks at two different gates, and the plan-gate prose
  check is the weaker one — sell it as best-effort, not a guarantee.

### 5.3 `clean-integrate` (script)
- **Does:** refuses/strips `git add -A` debris; reconstructs one commit per
  decomposition lane off current `origin/main`; excludes gitignored/debris paths;
  outputs a clean branch + a report.
- **Interface:** `clean-integrate <repo-path> <lane-map>` → branch + report + exit code.
- **Lane→file map source (CORRECTED per CEO review):** a "lane" = one implementation
  card, keyed by card id. The per-card file list is the `Files:` line the **architect**
  writes at decompose-time (`hermes-devcrew/agents/architect/skills/decompose-goal`),
  in **free prose inside the card description** — NOT the planner's spec (the spec
  defers the breakdown to the architect), and NOT a structured field (the kanban card
  schema has no `files` field). So `clean-integrate` reads card descriptions via
  `kanban_show` and parses the `Files:` prose; the result is agent-confirmed against
  `git status`. Files changed but claimed by no card are flagged (this is how the
  `3c62c38` debris surfaces). **Honest limitation:** this is a prose parse, not a
  structured lookup — if a card has no `Files:` line (e.g. the `hermes kanban swarm`
  fast path omits it) the map is incomplete → the tool returns exit 2 (escalate),
  never attribute-by-guess. A structured `files`/`blast_radius` card field would make
  this robust and is noted as a Phase-2 kernel candidate.
- **Pragmatic limit:** when lanes co-edit a file (the login-page T-A+T-C case),
  attribute to the earliest lane and flag for the agent to confirm; a genuine
  non-composing conflict escalates rather than guessing.

### 5.4 `pr-hygiene-gate` (script)
- **Does:** the release checklist — no debris/gitignored files tracked; build+test
  evidence artifacts present; branch is off *current* `origin/main` (not stale);
  nothing pushed to `main`; commit messages non-empty.
- **Interface:** `pr-hygiene-gate <branch>` → pass/violations + exit code.

These are the agent-side, pre-emptive versions of the shipped kernel T-A (assignee
validation) and T-F (evidence gate); Phase 2 turns the same invariants into structural
backstops.

## 6. Data flow

- **`spec-verify` card** (parented on plan, gates the human approve): reads the spec
  (durable specs-dir path) + repo; runs `spec-claim-verify`; posts the report as a
  comment **and** durable artifact. Refuted claims → **block** (spec is amended,
  re-verified). Clean → complete → gate promotes. The human approves a spec carrying a
  green verification report.
- **`release` card** (parented on reviewer+QA, replaces integrator): reads the build
  tree, the decomposition (lane→file map), and the reviewer/QA verdicts + evidence;
  runs `clean-integrate` → `pr-hygiene-gate`; produces a clean branch.
- **Outward reach (decided):** the release-manager **pushes the branch + opens a
  *draft* PR**, then stops. Pushing a branch/draft is low-stakes (nothing merges or
  deploys); it hands the human a real reviewable PR. The release-manager **never merges
  and never pushes `main`.**

## 7. Failure modes & safety properties

1. **Refuted claim → block (fail-closed); uncheckable claim → note, don't block
   (fail-open).** The human sees both lists.
2. **Broken build → no PR, period.** Test/build failure blocks the release card with
   evidence; no draft is prepared. (Would have stopped Item 12's broken-`main` merge.)
3. **Never merges, never pushes `main`.** Branch + draft PR only. No config loosens it.
4. **Debris already on `main` → flag, don't pretend.** `clean-integrate` strips debris
   from its branch; if debris already merged (the `3c62c38`→main case), it files a
   follow-up and surfaces it rather than silently proceeding.
5. **A broken harness script must escalate, not silently pass/fail** — the
   `verify_code_landed.sh` lesson. Tools return structured exit codes: `0`=pass,
   `1`=violations-found, `2`=script-couldn't-run. The agent treats `2` as
   *escalate to human*, never as "passed." A verifier that can't run is not a green light.

Net: the agent's judgment is guarded by the harness gates (three tools, plus the
fleet-wide E3 checks and the E4 kernel guard) **and** the human PR approval. Even if
the release-manager drifts or rubber-stamps, a `pr-hygiene-gate` failure or the human
catches it.

## 8. Testing

This session's incidents become the regression fixtures — the mechanism by which the
expertise is *verified* transferred, not just written down. All tests run on
**temp repos / scratch boards — never the live control-plane or live kanban boards**
(the kanban-worker v2.5.0 isolation rule).

- **`spec-claim-verify`** (fixture specs + repos): "route missing" when it exists →
  refute (A1); assignee `devos-backend` → invalid (phantom); "`middleware.ts` absent"
  when true → pass; design-intent prose → uncheckable; malformed spec → exit 2.
- **`clean-integrate`** (fixture trees): mixed-lane changes + a `git add -A` debris
  commit → per-lane reconstruction, debris stripped (Item 13 / `3c62c38`); co-edited
  file → earliest-lane + flag; debris on base → detect + report.
- **`pr-hygiene-gate`** (fixture branches): tracked debris → fail; missing evidence →
  fail; stale base → fail; clean → pass.
- **Agent-behavior scenarios** (heavier, fewer, scratch board): false-premise spec →
  blocks; tangled tree → clean draft PR + push held; broken build → blocks, no PR.
- **Config/skill presence:** a test like the existing `test_agent_configs.py` asserts
  the role config + skill are wired.

## 9. Cross-repo footprint

- **hermes-devcrew:** the `release-manager` role config (elevated from `integrator`),
  the `release-management` skill, the three harness scripts, and their tests. Bulk of
  the work.
- **dev-os:** a small orchestrator change — the decomposition flow inserts the
  `spec-verify` card as a parent of the human-approve gate, and routes the `release`
  card to `devcrew-release-manager`. Doctrine note in `kanban-orchestrator`.

## 10. Phasing

- **Phase 1 (this spec):** the release-boundary trust layer — agent + harness, the
  build→clean-PR pipeline. Catches the failures like the operator did.
- **Phase 2:** the kernel enforcement — dispatch-time same-tree serialization, deepened
  evidence gates, the **E4 debris-guard** (D3 returned it here), and a structured
  `files`/`blast_radius` card field (surfaced by the CEO review) that gives the kernel
  the allow-list E4 needs and makes `clean-integrate`'s lane map robust. These pair
  naturally, which is why E4 belongs here, not in Phase 1.
- **Phase 3:** throughput — parallelism, retry economics, budgeting — once correctness
  is locked.

Each phase is its own spec → plan → build cycle.

---

## 11. Accepted scope expansions (CEO review, 2026-06-14)

Mode: SELECTIVE EXPANSION. Baseline = approach B (full harness + release-manager).
The CEO review surfaced four expansions; **all four accepted into Phase 1.** They move
Phase 1 from "the agreed harness" toward the self-improving trust layer (approach C).

| # | Expansion | Effect on the design | Effort (human / CC) |
|---|-----------|----------------------|---------------------|
| E1 | **Self-improving check-library** | New first-class component: a registry mapping `incident → harness rule + regression fixture`. The release-manager (and the operator) MUST add an entry whenever a new failure class is caught, so the same mistake can never recur. This is the moat — trust compounds build-over-build. The "incidents as fixtures" testing note in §8 becomes this living mechanism, not a one-time seed. | ~3-5 days / ~1-2 hrs |
| E2 | **Stronger model for the verification gates** | CORRECTED: the *whole* devcrew fleet runs `deepseek-v4-flash` (per `team.yaml`), not just the integrator — so reviewer and QA are also trust gates on the weak model. E2 upgrades the **verification-judgment roles** (release-manager first, and reviewer + QA flagged as equal-priority candidates) to a stronger reasoning model, with an eval against E1's fixtures that defines a concrete pass bar (e.g. ≥ N/M verify fixtures correct, strictly better than flash). If it doesn't beat flash, keep flash. | ~0.5-1 day / ~15-30 min |
| E3 | **Fleet-wide harness tools** | The three tools are not release-manager-only: the **orchestrator** runs `spec-claim-verify` at decompose-time (catches false premises before the human even sees the gate), and **workers** run `pr-hygiene-gate` before completing (debris never enters the tree). The release-manager becomes the backstop, not the sole catch. Extends §6 data flow to the orchestrator + worker card lifecycles. | ~2-3 days / ~1 hr |
| E4 | **Kernel debris-guard** | **DEFERRED to Phase 2 (D3, 2026-06-14).** Briefly accepted into Phase 1, then the spec review found the naive "reject worker `git add -A`" is unsafe — `checkpoint_manager.py` uses `git add -A` as core rollback-snapshot infra; a blanket reject breaks checkpointing fleet-wide. It must target the worker→branch commit path only, exempt the checkpoint manager, and even then is gitignore+heuristics ("common case," not "structurally impossible"). Re-scoped to ~3-5 days and moved to Phase 2, where it pairs with the structured `files` card field that gives the kernel the allow-list it needs. Phase 1's `clean-integrate` + `pr-hygiene-gate` already catch debris at integration in the meantime. | ~3-5 days / ~1-2 hrs (Phase 2) |

**Net Phase-1 scope (final, post-D3):** the full harness + elevated release-manager
(B), now fleet-wide (E3), backed by a stronger-model gate (E2), feeding a self-improving
check-library (E1). **E4 deferred to Phase 2.** Remaining Phase 2 = same-tree
serialization at dispatch, deepened evidence gates, the structured `files` card field,
and the E4 debris-guard (which pairs with that field). Phase 3 = throughput. The Phase-1
expansions (E1+E2+E3) enlarge the first bite by roughly **6-9 human-days** (~3-4 hrs CC)
over baseline B — the trade the user accepted for the compounding moat.

---

## Reviewer Concerns (open items, CEO review 2026-06-14)

Raised by the independent spec reviewer; writing-plans MUST resolve each (not yet
designed):

1. **Spec-amendment-after-decompose:** when `spec-verify` refutes a claim and the spec
   is amended, the architect may have already decomposed the *old* spec into cards.
   Define how stale cards are invalidated / re-decomposed.
2. **Build/test command + evidence schema undefined:** `pr-hygiene-gate` checks evidence
   is *present*, not *valid/fresh*. Define the per-repo build/test invocation, the
   evidence-artifact schema, and whether the release-manager re-runs the build or trusts
   QA's artifact.
3. **Draft-PR idempotency/failure:** reuse-open-PR, auth/remote-missing, branch
   collision, push-rejected. Add a failure subsection to §6.
4. **E1 registry is a process aspiration, not a built component:** specify the registry
   file path, entry schema, and the consuming check (which tool reads it at runtime to
   actually prevent recurrence).
5. **Co-edit attribution contradicts doctrine:** `decompose-goal` already routes shared
   wiring files to the integrator card. "Earliest lane" is wrong; align with "shared
   files belong to the release-manager's own integration commit."
6. **Per-lane commits may not individually build** (only the branch tip is
   build-verified). State that per-lane commits are organizational, or squash.
7. **E3/§6 run duplication:** the orchestrator (E3) and the `spec-verify` card both run
   `spec-claim-verify`. Resolve which run is authoritative and which gates the human.

---

## GSTACK REVIEW REPORT

| Review run | Status | Key findings |
|---|---|---|
| CEO Step-0 (premise / leverage / dream-state / alternatives) | DONE | Reframed the moat as a self-improving check-library; flagged the gate's weak model; confirmed elevate-integrator over new role. |
| Implementation approach (0C-bis) | DONE | Approach B selected (full harness), minimal-A and ideal-C as bookends. |
| Mode + expansion cherry-pick (0F) | DONE | SELECTIVE EXPANSION; all 4 expansions (E1-E4) accepted into Phase 1. |
| Independent adversarial spec review (subagent) | DONE — score 5/10 | Two factual errors in the design's self-model (lane-map source; E2 model premise) + E4 kernel collision with `checkpoint_manager`. 5 corrections applied inline; 7 items logged as Reviewer Concerns. |

**VERDICT: CHANGES APPLIED — design corrected, one scope decision re-opened.** The
design is strategically sound (the fail-closed / never-merge / exit-2-escalates posture
is strong), but the independent review proved the first draft mis-described its own
system. The factual errors are fixed; the feasibility of E4 changed materially
(~3-5 days, only "catches the common case," collides with checkpoint infra), which
re-opens whether E4 belongs in Phase 1.

**Resolved decisions:**
- E4 (kernel debris-guard) Phase placement → **D3 (2026-06-14): deferred to Phase 2.**
  The spec review disproved its ~1-2 day / "structurally impossible" framing
  (~3-5 days, "common case only," checkpoint-manager collision); Phase 1's agent-layer
  `clean-integrate` + `pr-hygiene-gate` already catch debris at integration, so Phase 1
  loses only the structural pre-integration guarantee until Phase 2. Final Phase-1
  scope = baseline B + E1 + E2 + E3.

NO UNRESOLVED DECISIONS
