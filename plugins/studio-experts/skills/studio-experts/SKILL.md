---
name: studio-experts
description: >-
  Select and coordinate local Unity, Unreal Engine, Blender, Maya, ZBrush and Godot specialists
  for expert reviews, production plans, implementation, and fixes. Use when the user asks
  for a studio expert panel, a "studio review" or "studio agents", Scenario local experts,
  an agency-style engine/DCC review, or coordinated specialist work across an asset-to-engine
  pipeline. Select only relevant disciplines; ordinary single-tool tasks can continue through
  their existing tool skills. Not for software, web, or tooling projects that use none of the six apps.
license: Unlicense
compatibility: "Five of the six families need the pinned scenario-labs/skills files, which scripts/fetch_pinned_upstream.py fetches into vendor/. Godot works without them."
---

# Studio experts

One coordinator, six application families, 64 roles (six leads and 58 specialists): five pinned upstream
families under vendor/ and a local Godot family under local/ (written 2026-10-28 from the author's Godot research).
Scenario's hosted MCP is not required. This skill does not provide a running editor connection.
It supplies expertise and source helpers; select an available, verified execution channel separately.

## Establish the job

Read the project's CLAUDE.md (and AGENTS.md / HANDOFF.md if present) and relevant manifests/design decisions. Record the
user's outcome, mode (review / plan / implement / fix), exact target paths, source and destination
applications, actual versions, OS, render pipeline, platform, stage, constraints and acceptance evidence.
Review means reports only. Planning means a plan. Implement/fix means complete the authorized work,
not merely write recommendations. Infer mode from the request; do not request redundant approval.
Do not infer installed applications or requested versions from this collection's advertised targets.

## Select the panel

Read [the picker](references/picker.md), then the relevant rows in
[the complete role catalog](references/roles.md). Use the read-only search helper to shortlist:

```powershell
python '<absolute skill directory>/scripts/catalog.py' --family unity --query 'feet slide after retargeting'
python '<absolute skill directory>/scripts/catalog.py' --family maya --family unreal --query 'skeletal FBX import'
python '<absolute skill directory>/scripts/catalog.py' --family blender
```

Resolve the example path from this SKILL.md's real location before running. Search rankings are
retrieval hints, not a final panel, confidence score, or authority to execute. Read every shortlisted
role's full description, then its bundled SKILL.md and relevant references before assigning it.
The catalog emits absolute paths, family leads, validation limits and all family candidates by default.
All 64 roles are present once vendor/ is fetched (the 6 Godot roles always are): ignore upstream instructions to install missing siblings when they
exist here. Preserve sibling folders because helpers import the lead's scripts. `scenario-blender-blockout`, named by some Blender roles, is not bundled: it needs Scenario's plugin, so flag the gap.

Select by concrete responsibilities and evidence, using the picker decision record. State the panel
briefly (role, responsibility, why). A narrow fix usually needs 1–2 specialists; an extensive review
may need 4–8. These are guides, not quotas. Do not manufacture unrelated work to fill a panel.
The coordinator uses the appropriate family lead; do not add a redundant lead agent automatically.

## Coordinate

Use subagents when selected responsibilities benefit from independent review or separable work.
Give each worker [the brief and report contract](references/work-contract.md). Dispatch only as many
as capacity allows; queue the rest. If subagents are unavailable, apply the same lenses sequentially.
Every worker must receive the relevant safety/compatibility overlay, not only the upstream role.

Before launching, state the run's purpose and what ends it in one line, read the allowance and obey any local
usage rules, and ask the owner before launching more than 6 workers.

In Codex, dispatch one subagent per worker with the same briefs if subagents are available, on a cheaper model
with the effort set explicitly; otherwise apply the lenses sequentially.

In Claude Code, launch workers with the Agent tool: `subagent_type: general-purpose`,
`run_in_background: true`, and an explicit `model` (`sonnet` by default; `opus` only if the user asks for depth),
all independent reviewers in one message. Put shared context in a common brief file next to the reports and have
each worker read it, so every brief still stands alone. Do not read worker transcripts; wait for completion notices.

Independent read-only review can run in parallel. For implementation, assign nonoverlapping files
and explicit handoffs. Only one agent drives a given editor/project/session at a time, including
captures, play state, selection, asset imports and saves. Parallel workers may prepare source or
review artifacts; the designated editor owner integrates dependent changes. Never revert another
worker's or the user's work indiscriminately.

For reviews, write to the project's established review directory, or docs/reviews/<date>-studio-experts,
using a suffix if occupied. Individual reports and SUMMARY.md include verified findings, disagreements,
priorities, evidence, and unresolved questions. For small fixes, a concise result is sufficient.
The coordinator verifies high-impact findings, integrates authorized changes, and checks acceptance.
Always distinguish source/static, headless, live editor, player/device, visual and owner acceptance.

Blender workers follow the channel rules in [Blender agent notes](references/blender-agent-notes.md)
section 5. Explore live, ship headless: the deliverable is a re-runnable build script and acceptance is a
clean headless rebuild. Unattended or parallel Blender work is headless only, one Blender process per
worker. Visual acceptance between competing builds uses a fresh-context blind judge. The coordinator may
override these defaults with a stated reason.

## Local execution overlay — read before any bundled helper

Read [compatibility and safety](references/compatibility.md). It overrides conflicting upstream recipes.
For any Blender role, also read [Blender agent notes](references/blender-agent-notes.md): MCP channel limits,
the MCP security boundary and Blender changes after this pack was pinned (5.2.3, 5.3). It wins over vendored Blender files.
Prefer existing installed application skills and available tools for execution (including the user's
Unity CLI skills), with this pack supplying specialist reasoning. Inspect the actual helper and its
transitive calls before running it; importing a vendor module may itself have side effects.

- Never inspect or interact with authentication, activation, entitlements, account stores or license files.
  Specifically, never call Unity ut_env.license_ok or ut_env.preflight; they read licence state and are not patched in the upstream files this copy fetches.
- Never accept engine/DCC automatic upgrade, migration, patch or assembly-update prompts. Unity command-line
  launches include -disable-assembly-updater. If blocked, report the prompt and continue code-only work.
- No automatic application/package/plugin installs, bridge enablement, project version switches, cloud
  generation, publishing, store submission, or long production runs merely because an upstream recipe says so.
  Carry out separately authorized work within the user's scope and permission boundaries.
- Do not use HyperFrames. No persistent server starts just to select or review specialists.

Pinned upstream provenance and file hashes are recorded in
[source-lock.json](references/source-lock.json). Refresh only on request: a refresh pins a new commit and new hashes in the lock; the tooling for that is not included. Then
regenerate the catalog, and rerun validation before replacing the installed pack. Never silently pull main.

## Pinned upstream setup

The five Scenario families are not included. From this skill's folder, run:

```
python scripts/fetch_pinned_upstream.py
```

It needs Git and network access. It takes only the files `references/source-lock.json` lists from https://github.com/scenario-labs/skills at commit 7f4b801c7248d51b093ec365aceb114bd06139e6, byte for byte, into `vendor/`, then runs `scripts/catalog.py --verify`. A plain clone will not verify: it brings files the lock does not list and may convert line endings.

Without them, use the Godot family and say which families are unavailable. Review upstream scripts before running them. Do not run any helper that touches a licence, an account or a sign-in.

"Owner" in this skill means the person who gave the assignment.
