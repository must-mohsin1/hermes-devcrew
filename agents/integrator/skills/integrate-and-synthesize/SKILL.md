---
name: integrate-and-synthesize
description: "Merge verified task outputs into one coherent, green, well-documented deliverable."
version: 1.0.0
author: hermes-devcrew
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [integration, synthesis, merge, release, documentation]
    related_skills: [adversarial-review, decompose-goal]
---

# Integrate & Synthesize

Use as the final step: assemble reviewer-approved work into a shippable whole.

## Procedure
1. **Gate.** Confirm every task you're integrating passed `devcrew-reviewer`. Unverified work
   does not go in — bounce it back.
2. **Order.** Integrate in dependency order so each piece lands on a consistent base.
3. **Reconcile with intent.** On conflicts, understand *why* the changes disagree; pick the
   correct reconciliation and note it. Don't just take-theirs/take-mine.
4. **Cross-cutting coherence.** Check shared types/interfaces, naming, config, env, and docs agree
   across the merged pieces. Bump versions where needed.
5. **Prove it's green.** Run the full build and the combined test suite. Integration isn't done
   until the whole is passing — not just the parts.
6. **Tell the story.** Write the PR/changelog: what changed, why, how it was verified, and notes
   for reviewers/users.
7. **Close out.** `hermes kanban complete` the synthesis task with the final summary and where the
   result lives (branch/PR/tag).

## Guardrails
- If integration reveals a real defect, file it back as a task for the right specialist; don't
  silently patch around it.
- Ship/deploy only if the goal authorizes it — otherwise hand to `devcrew-devops` with a release note.
