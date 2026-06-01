# hermes-devcrew ☤

**An autonomous, hybrid software-engineering team you install in one command.**

`hermes-devcrew` is a packaged team of seven domain-expert agents for the
[Hermes Agent](https://hermes-agent.nousresearch.com) platform. Give it a goal; the crew plans
it, builds it in parallel, reviews itself, and synthesizes the result — autonomously, on your
machine, against your repo, with your own API key.

It's not a framework or a fork. Each agent is a real Hermes **profile distribution**; the crew
coordinates through Hermes' built-in **kanban swarm** and **dispatcher daemon**.

---

## How it works

A "team" in Hermes is several **profiles** (isolated agents) sharing one **kanban board**:

| Team concept            | Hermes mechanism                                                    |
|-------------------------|--------------------------------------------------------------------|
| A team member           | a **profile** — isolated agent with its own persona, skills, model  |
| Their expertise         | each agent's `SOUL.md` doctrine + bundled `skills/`                 |
| The backlog             | the shared **kanban** board (`hermes kanban`)                       |
| Autopilot               | `hermes kanban daemon` — runs each task as its assigned profile     |
| Parallel → verify → ship| `hermes kanban swarm` — workers → verifier → synthesizer            |

Expertise lives in files that **travel with the distribution** (`SOUL.md`, `skills/`) — not in
memory, which stays on each user's machine. Secrets never ship: distributions only *declare* the
keys they need (`OPENROUTER_API_KEY`), and you supply your own.

---

## The roster

| Agent | Swarm role | What it does | Default model |
|-------|-----------|--------------|---------------|
| **architect** | anchor | Decomposes goals into a verifiable task graph; sets acceptance criteria | `deepseek/deepseek-v3.2` |
| **backend-dev** | worker | APIs, services, data, tests (test-first) | `mistralai/codestral-2508` |
| **frontend-dev** | worker | UI, components, state, accessibility | `mistralai/codestral-2508` |
| **devops** | worker | Containers, CI/CD, deploys, observability (reversible, least-privilege) | `mistralai/codestral-2508` |
| **reviewer** | **verifier** | Adversarial correctness + security gate before anything merges | `deepseek/deepseek-v3.2` |
| **integrator** | **synthesizer** | Merges verified work into one coherent, green deliverable | `deepseek/deepseek-v3.2` |
| **domain-expert** | worker | **Customizable** specialist that learns *your* codebase | `mistralai/codestral-2508` |

---

## Install

**Prerequisites:** [Hermes](https://hermes-agent.nousresearch.com/docs/) (`>= 0.12.0`), `git`,
and an [OpenRouter](https://openrouter.ai) API key.

```bash
# clone + install (recommended while iterating)
git clone https://github.com/REPLACE-ME/hermes-devcrew
cd hermes-devcrew
./install.sh

# or, once published, one line:
curl -fsSL https://raw.githubusercontent.com/REPLACE-ME/hermes-devcrew/main/install.sh | bash
```

The installer is idempotent. Useful flags / env:

| Flag / env | Effect |
|---|---|
| `--daemon` | start the autonomous dispatcher immediately |
| `--with-skill-packs` | also install standard Hermes skill packs per role (needs network) |
| `OPENROUTER_API_KEY=…` | pre-supply the key (no prompt) |
| `DEVCREW_SKIP_KEYS=1` | install without writing any key |
| `DEVCREW_BOARD=myproj` | name the kanban board |

---

## Drive the crew

```bash
# One-shot autonomous swarm: workers run in parallel → reviewer verifies → integrator synthesizes
hermes kanban swarm "Add OAuth login to ./myapp with tests" \
  --created-by devcrew-architect \
  --worker devcrew-backend-dev:"OAuth endpoints + session" \
  --worker devcrew-frontend-dev:"Login UI" \
  --verifier devcrew-reviewer --synthesizer devcrew-integrator

hermes kanban daemon     # execute the board autonomously
hermes kanban tail       # watch the crew work
```

Or just brief the architect and let it decompose:

```bash
hermes --profile devcrew-architect -z "Plan and execute: add OAuth to ./myapp"
```

See [`docs/usage.md`](docs/usage.md) for manual task assignment, monitoring, cron routines, and
per-agent model overrides.

---

## Make it *your* expert

The **domain-expert** is a template. After install, teach it your project:

```bash
hermes --profile devcrew-domain-expert -z "Onboard to /path/to/my/repo"   # it fills its own context
# or edit ~/.hermes/profiles/devcrew-domain-expert/SOUL.md  → the "PROJECT CONTEXT" block
```

That block is loaded every turn, so the more you put there (stack, invariants, glossary,
gotchas), the more expert the whole crew becomes about your codebase.

---

## Models & cost

One `OPENROUTER_API_KEY` powers everyone. Defaults favor cheap-but-strong open models
(DeepSeek for reasoning roles, Codestral for coders). Swap any agent's model anytime:

```bash
hermes --profile devcrew-reviewer model     # pick interactively
```

`config.yaml` is preserved across `hermes profile update`, so your model choices survive updates.

---

## Safety & guardrails

- **`--yolo` is off by default.** Destructive/networked actions are not auto-approved.
- Workers run in **isolated workspaces**; nothing is merged until the **reviewer** passes it.
- **devops** treats destructive/prod actions as hard stops requiring human approval.
- The board keeps an auditable event stream — `hermes kanban tail` / `log`.
- Review the trust model before pointing the daemon at anything important.

## Update / uninstall

```bash
hermes profile update devcrew-architect      # re-pull doctrine/skills; keeps your memory + keys
hermes profile delete devcrew-architect      # remove one agent
```

## License

MIT — see [LICENSE](LICENSE).
