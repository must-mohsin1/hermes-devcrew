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
  serialization at dispatch, kernel-side debris rejection) — that is **Phase 2**.
  Phase 1 gives the release-manager the doctrine + harness to *catch* these like the
  operator did; Phase 2 makes the kernel *prevent* them.
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
- **Pragmatic limit:** targets the **structured** sections the planner already writes
  (acceptance-criteria file refs, the assignee table, "missing/exists" statements) +
  a grep pass over cited `file:symbol` pairs. Does not NLP-parse free prose; the agent
  handles design-intent claims by judgment. Still auto-catches the A1 false premise
  and phantom assignees.

### 5.3 `clean-integrate` (script)
- **Does:** refuses/strips `git add -A` debris; reconstructs one commit per
  decomposition lane off current `origin/main`; excludes gitignored/debris paths;
  outputs a clean branch + a report.
- **Interface:** `clean-integrate <repo-path> <lane-map>` → branch + report + exit code.
- **Lane→file map source:** derived from the spec's per-lane file references (the
  planner already writes a "BLAST RADIUS" file list per lane), then agent-confirmed
  against the actual changed-file set (`git status`); files changed but not claimed by
  any lane are flagged (this is how the `3c62c38` debris and the composition-shape
  straggler would surface). The map is an explicit artifact, not an inference hidden
  inside the script.
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

Net: the agent's judgment is guarded by two mechanical gates (the harness) **and** the
human PR approval. Even if the release-manager drifts or rubber-stamps, a
`pr-hygiene-gate` failure or the human catches it.

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
- **Phase 2:** kernel-harden the invariants (dispatch-time same-tree serialization,
  kernel-side debris/`git add -A` rejection, deepened evidence gate) so Phase 1 no
  longer depends on agents following doctrine.
- **Phase 3:** throughput — parallelism, retry economics, budgeting — once correctness
  is locked.

Each phase is its own spec → plan → build cycle.
