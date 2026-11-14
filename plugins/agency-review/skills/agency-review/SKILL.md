---
name: agency-review
description: >-
  Critique the current project for improvement using expert personas from the agency-agents
  collection ($AGENCY_AGENTS_DIR). Picks the best-fitting reviewers for this project
  (game design, engine, UX, security, product, testing, etc.), runs each as a separate reviewer
  that writes a detailed findings report, then writes a SUMMARY.md that merges consensus,
  disagreements, a prioritised action list and owner questions. Use when the user asks to "run
  the agency agents", "have experts review/critique this", "get write-ups on the design/code",
  or wants a multi-perspective improvement review of a project, design doc, plan or codebase.
license: Unlicense
compatibility: "Needs a clone of msitarzewski/agency-agents, found through AGENCY_AGENTS_DIR."
---

# agency-review — expert-panel critique from agency-agents

Goal: improvement. Each reviewer finds concrete problems in *this* project and proposes fixes, in a written report. You orchestrate: choose the panel, brief each reviewer, collect reports, synthesise.

Persona repo: `$AGENCY_AGENTS_DIR`, else an `agency-agents` folder in the current directory. Persona files are Markdown with `name`/`description` frontmatter, grouped in division folders (`game-development/`, `engineering/`, `design/`, `testing/`, `product/`, `security/`, …). `integrations/`, `strategy/`, `examples/`, `scripts/` are not personas.

## 1. Understand the target (read before choosing anyone)

- Establish what is being reviewed: the user's named files, else the project's main design/spec doc, README, and (for code) the architecture entry points. Note stage (idea / design / prototype / production / live), stack, platform, team size.
- Note which decisions are already **confirmed by the owner** (decision logs, "confirmed" sections, memory). Reviewers may challenge them only with clearly labelled pushback.
- Find related context worth passing along read-only: any knowledge-base articles you keep, manifests, prior reviews.

## 2. Choose the panel

List candidates: `python <this-skill-dir>/scripts/catalog.py <keywords…>` (or `--divisions a,b`). Read the persona file of every finalist before selecting it.

Selection rules:
- **6–12 reviewers.** Fewer for a small target; more only when distinct disciplines genuinely apply.
- **Match the actual stack.** Engine-/platform-specific personas only when they match (Unity personas for Unity, never Godot/Unreal/Roblox for a Unity project). Skip whole divisions that don't apply (sales, paid-media, healthcare… unless the project is in that domain).
- **Cover the disciplines the project actually has:** core design/product, architecture/engineering, UX/UI, art/visual tech, audio, networking, security, performance, economy/monetisation, content/narrative — whichever exist or are planned.
- **No overlap:** two personas with the same lens produce duplicate reports; keep the more specific one.
- **Always include one skeptic** (e.g. `testing/testing-reality-checker.md`) to challenge scope, assumptions and sequencing.
- Stage-appropriate: design-stage projects get design/architecture/UX/skeptic reviewers, not test-automation or API testers.

Before launching, tell the user the panel in one line per reviewer (persona + why), then proceed unless they asked to approve first.

## 3. Brief and run the reviewers

- Output folder: `<project>/<docs-or-design-folder>/reviews/<YYYY-MM-DD>/` (use the project's existing design/docs folder; create `reviews/<date>/`). If today's folder exists, add a suffix (`-2`). One report per reviewer: `<persona-slug>.md`.
- Build each brief from `references/report-template.md`. Every brief must stand alone and contain: persona path, project summary, exact files to read (absolute paths), the confirmed-vs-proposed rule, 5–10 **project-specific** focus questions for that persona, one persona-specific deliverable (wireframes, numeric model, arena dimensions, schema, first-5 list…), the six-section report format, the output path, a word limit (1,500–1,800), and "edit nothing but your report".
- **Before launching:** state the run's purpose and what ends it in one line, read the allowance and obey any local usage rules, and ask the owner before launching more than 6 reviewers. When The Agency dispatches this panel, its team sizing governs.
- **Claude Code:** launch all reviewers in one message with the Agent tool (`subagent_type: general-purpose`, `run_in_background: true`, an explicit model — `sonnet` by default, `haiku` for a narrow lookup-style lens, `opus` only if the user asks for depth). Do not read their transcripts; wait for completion notifications.
- **Codex:** if subagents/multi-agent spawning is available, dispatch one per reviewer in parallel with the same briefs. Otherwise run each review yourself sequentially: load the persona, write that report, then drop the persona before the next one.
- Reviewers never modify the reviewed project; if one does, revert its change and note it.

## 4. Synthesise

When all reports exist (check each file is present and non-trivial; re-run any reviewer that failed):
- Read every report. Write `SUMMARY.md` in the same folder using the structure in `references/report-template.md`: consensus findings first (raised by 2+ reviewers), then disagreements with your recommendation, a single prioritised action list (now / later) citing source reports, and deduplicated owner questions.
- Verify claims that drive top-priority actions against the source docs; drop or mark anything a reviewer misread.
- Do not apply recommendations to the project's docs or code unless the user asks. Offer to.
- If reviewers captured screenshots, renders or clips of the project, the-agency skill is installed and the owner wants a media kit, run its media kit curator once (`agency-mediakit-curator`, `references/mediakit.md` in that skill). The kit at `<project>/.mediakit` is then the one place a review writes outside its folder. Otherwise skip this step.

## 5. Report back

Give the user: the panel, the 5–8 most important findings with who raised them, the questions only they can answer, and full absolute paths to `SUMMARY.md` and each report. If the project is a git repo, offer to commit the reviews folder (don't commit unasked).

## Persona setup

Personas are not included. Clone https://github.com/msitarzewski/agency-agents and set `AGENCY_AGENTS_DIR` to the clone. If it is absent, say so and stop. This skill is unaffiliated with that project.

"Owner" in this skill means the person who gave the assignment.
