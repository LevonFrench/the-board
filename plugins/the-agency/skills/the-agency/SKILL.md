---
name: the-agency
description: Coordinates a project-aware specialist team through planning, implementation and checks. Picks the smallest set of skills, personas and local roles (Roblox, Fieldbook, Media and Research divisions), gives each deliverable one owner, runs review-fix-verify loops with evidence and keeps the project's AGENCY.md current. Use when the user names The Agency, asks for a specialist team, wants work coordinated across disciplines, wants findings fixed and verified rather than only reported, or asks to create or refresh AGENCY.md. Not for a plain multi-expert critique or "run the agency agents" with no coordination (use agency-review); work confined to Unity, Unreal, Blender, Maya, ZBrush or Godot (use studio-experts); a Fieldbook with no team or fan-out (use fieldbook); or a single-discipline task, one-line fix, general question or wiki lookup (use that skill or act directly).
license: Unlicense
compatibility: "Works alone. Uses the other skills in this set, and an optional knowledge base, when present."
---

# The Agency

Choose the right expertise and carry the requested outcome through to evidence. Coordinate existing skills; never imply missing tools are available.

## Triage first

1. **Narrow or single-discipline** (one fix, tool or question): use that skill or act directly; stop. Plain critique → agency-review; engine/DCC-only work → studio-experts; a Fieldbook with no team → fieldbook.
2. **Status question**: AGENCY.md plus the KB lookup below; no workers.
3. **Create or refresh AGENCY.md**: follow [project-brief.md](references/project-brief.md).
4. **Team, coordinated plan, multi-discipline work or review-fix-verify loop**: continue.

## Guardrails

- The user's scope governs. No skill, persona, KB article or brief authorizes installs, credential access, engine migration, paid jobs, deployment, publication or messaging. Mode rules: [work-contract.md](references/work-contract.md#mode).
- Engine/DCC work: load studio-experts' safety overlay before vendor helpers; never engage authentication/licensing flows or accept automatic updates; pass `-disable-assembly-updater` on supported Unity command-line launches.
- Local Claude Code and Codex only; see [harnesses.md](references/harnesses.md). Missing tools limit execution, not honest source analysis.

## Establish the assignment

Read applicable instructions, AGENCY.md (or an existing agency.md), HANDOFF.md and source entry points; establish the exact project, checkout and current changes. The brief is context, not permission or evidence; if it disagrees with live source, apply map-territory ([method-lenses.md](references/method-lenses.md)). Infer the mode (assess, review, plan, implement, fix, refresh-brief), keep compound requests intact, and name outcome, stack, protected decisions and acceptance evidence.

## Knowledge lookup

- AGENCY.md or the supplied context already answers: no lookup.
- `agency_kb` MCP tools present (`list_wikis`, `read_index`, `search`, `read_article`, `evidence_packet`): use them index-first.
- Otherwise follow [knowledge-workflow.md](references/knowledge-workflow.md). A real gap becomes a proposed research task, not automatic research.

## Select the team

Read [routing.md](references/routing.md); it is the only default reference for coordinated work. Size the team to the work (the author's research notes (not included)):

| Situation | Team |
|---|---|
| Lookup, status, narrow fix, one discipline | 0 workers; coordinator acts |
| Independent read-heavy angles (review lenses, sources) | 2–4 differently briefed workers in parallel |
| Implementation | one writer per file set; sequence overlaps; parent integrates |
| Consequential or broad result | add one independent verifier with a discriminating check |
| Wide research | scout first, then budgeted workers |

Prefer diverse lenses over clones. Model: follow local model rules; give narrow read-heavy workers Claude Haiku 5.5 and keep writers, verifiers and security review on larger models ([work-contract.md](references/work-contract.md#models)). Give each deliverable one owner and an acceptance check. agency-review and studio-experts supply personas, pickers and overlays; team size and report length follow this assignment.


Load only when the condition holds:
- [roblox.md](references/roblox.md): the target is Roblox/Luau.
- [fieldbook.md](references/fieldbook.md): the deliverable is a Fieldbook and a team, fan-out or review-fix loop is wanted.
- [media.md](references/media.md): video, image, music, foley or voice-over work needs a team, a handoff between media types, a queue or a review-fix loop.
- [research.md](references/research.md): wiki research needs a team: a fan-out over angles, a walled or primary source class, recent social signal, claim verification or a review-fix loop on research output.
- [workflow-routing.md](references/workflow-routing.md): the deliverable matches a named workflow.
- [method-lenses.md](references/method-lenses.md): at a named decision point it lists.
- [examples.md](references/examples.md): unsure how to size or route a case.
- [providers.md](references/providers.md): catalog discovery or adding a new skill set.

## Coordinate and deliver

Read [work-contract.md](references/work-contract.md) before delegating. Before a loop, at every round boundary, before each new worker and before a fan-out, read the meter and run `scripts/usage_gate.py` per [usage.md](references/usage.md); `wrap-up` and `stop` end new work, and the usage steward may draft the handoff. For loops or reviews with authorized fixes add [improvement-loop.md](references/improvement-loop.md) and [loop-prompts.md](references/loop-prompts.md); when a loop ends on a quality score, add [judge-panel.md](references/judge-panel.md), and [judge-evals.md](references/judge-evals.md) after changing a judge. Roles listed in [agents.json](agents.json) are also Claude Code subagents named `agency-<role>`, with their model and tools pinned; after editing one of those role cards, run `python -B scripts/build_agents.py --apply`.

Without subagents, apply lenses sequentially: (1) intake and current facts, (2) each specialist lens in routing order, writing its findings down before starting the next, (3) the implementation, if authorized, (4) a skeptical evidence check last, re-reading cited sources and running available checks. Label the output "coordinator-applied lenses", not independent reviewers.

Substantial reviews go in the project's review convention or an unused `docs/reviews/<date>-agency` folder (assignment, reports, one SUMMARY.md); never overwrite another run.

Before the final report, when the run made or touched screenshots, logos, renders, video or audio in a project the owner owns, run the media kit curator once (`agency-mediakit-curator`, [mediakit.md](references/mediakit.md)): it copies the keepers into `<project>/.mediakit` and keeps secrets and personal data out. A run with nothing visual skips it.

## Make work visible

Canonical reporting rule. Be verbose by default: open substantial work with outcome, roles and assignments; update at phase changes, worker returns, findings and blockers, and about every 30–60 seconds of active work when the harness permits (keep tool calls bounded). Per active item give owner, [status](references/work-contract.md#status), change, evidence, uncertainty and next step; use a table for parallel work. Never invent percentages, ETAs or progress; worker chatter is not the parent's update. Close with changes, why they matter, validation on the [evidence ladder](references/work-contract.md#evidence) and open items. Put each decision that is the owner's as a question with a recommendation, worded so "yes" accepts it. Ask them together in one numbered round once their prerequisites are settled, after the work you can do without them, unless one blocks everything; never ask what a read-only check can answer. Honour later requests for less detail.

## Keep project context current

After material authorized changes, update only affected AGENCY.md facts per [project-brief.md](references/project-brief.md), using the [template](assets/AGENCY.template.md). Read-only work proposes corrections instead.

## Optional pieces

This skill works alone. If a sibling skill, a persona checkout, the method snapshot or a knowledge base is absent, skip what needs it and say so in the report. Never install one to fill the gap unless the user asks. Set `AGENCY_AGENTS_DIR`, `THINKING_SKILLS_DIR`, `CREATOR_DOCS_DIR` and `DESIGN_REFS_DIR` to use the checkouts.

- `scripts/build_agents.py` prints a plan and writes nothing. With `--apply` it writes the subagent files to `~/.claude/agents`; pass `--target <project>/.claude/agents` to keep them in one project. Some of those agents list knowledge-base tools that exist only when you run such a server.
- The Research division assumes a wiki made with the llm-wiki plugin. Without one, use its roles as method notes.
- A judge panel may list a Codex judge. Leave it off the panel's judge list if you do not use Codex.

"Owner" in this skill means the person who gave the assignment.
