# Using hermes-devcrew

A practical guide to driving the crew after `./install.sh`.

## Mental model

- Each agent is a Hermes **profile** (`devcrew-architect`, `devcrew-backend-dev`, …).
- They share one **kanban board**. Tasks are claimed atomically and run in isolated workspaces.
- The **dispatcher daemon** turns the board into autonomous execution.
- A **swarm** is a ready-made graph: parallel workers → verifier → synthesizer.

## 1. The fast path — one autonomous swarm

```bash
hermes kanban swarm "Build a CSV export endpoint in ./api with tests" \
  --created-by devcrew-architect \
  --worker devcrew-backend-dev:"Implement /export endpoint + tests" \
  --verifier devcrew-reviewer \
  --synthesizer devcrew-integrator

hermes kanban daemon      # start autonomous execution (Ctrl-C to stop)
hermes kanban tail        # live event stream
```

`--worker` is repeatable; format is `PROFILE:TITLE[:SKILL,SKILL]`.

## 2. The architect-led path

Let the architect decompose a fuzzy goal onto the board, then run it:

```bash
hermes --profile devcrew-architect -z "Plan and execute: add rate limiting to ./api"
hermes kanban daemon
```

## 3. Manual control

```bash
hermes kanban ls                                   # see the board
hermes kanban create "Add /health endpoint" --assignee devcrew-backend-dev
hermes kanban link <parent-id> <child-id>          # dependency / ordering
hermes kanban assign <task-id> devcrew-devops
hermes kanban show <task-id>                        # task + comments + events
hermes kanban dispatch                              # one dispatcher pass (no daemon)
```

## 4. Monitoring

```bash
hermes kanban tail        # follow events live
hermes kanban stats       # throughput / state counts
hermes kanban runs        # execution runs
hermes logs               # Hermes logs
```

## 5. Per-agent tuning

```bash
hermes --profile devcrew-reviewer model            # change its model
hermes --profile devcrew-backend-dev config set agent.reasoning_effort high
hermes --profile devcrew-domain-expert skills install <skill>   # add a capability
```

## 6. Recurring routines (optional)

Give an agent standing duties with cron:

```bash
hermes --profile devcrew-devops cron add "0 3 * * *" "Audit dependencies in ./repo and open tasks for any CVEs"
hermes --profile devcrew-devops cron list
```

## 7. Customizing the domain-expert

```bash
hermes --profile devcrew-domain-expert -z "Onboard to /path/to/repo and fill your PROJECT CONTEXT"
# or edit ~/.hermes/profiles/devcrew-domain-expert/SOUL.md directly
```

## 8. Updating

```bash
cd hermes-devcrew && git pull
./install.sh                       # re-installs; preserves each agent's memory, sessions, keys
```

Distribution-owned files (`SOUL.md`, `config.yaml`, `skills/`) refresh on update; your
`config.yaml` model overrides are preserved unless you pass `--force-config` to
`hermes profile update`.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Agent won't run / auth error | `hermes --profile devcrew-<role> auth add openrouter` (or set `OPENROUTER_API_KEY` in its `.env`) |
| Model not found | `hermes --profile devcrew-<role> model` and pick an available OpenRouter slug |
| Daemon does nothing | Board may be empty or all tasks blocked — `hermes kanban ls` |
| Install can't find Hermes | Install Hermes first: https://hermes-agent.nousresearch.com/docs/ |
