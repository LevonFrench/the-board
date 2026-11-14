# Existing skill sets and new providers

Load only for catalog discovery or when adding/refreshing a skill set. Ordinary routing uses [routing.md](routing.md).

```powershell
python 'scripts/catalog.py' --summary
python 'scripts/catalog.py' --query 'accessibility onboarding'
python 'scripts/catalog.py' --kind persona --query 'game design'
python 'scripts/catalog.py' --kind role --query 'persistence'
python 'scripts/catalog.py' --kind workflow --query 'delivery'
python 'scripts/catalog.py' --kind method --query 'hypotheses'
```

Metadata matches are candidates, not a ranking of competence; a file on disk is not proof that a plugin, editor, account or tool is available.

## Live discovery

The harness's available-skills list is the first catalog. It includes plugin skills whose cache paths may change. Read descriptions first and load only relevant skills. The helper supplements it with explicit local directories and agency personas. It reads metadata and hashes; it never runs discovered code, installs packages, starts servers or updates repositories.

The helper defaults to references/providers.json. Use --config for another registry and repeatable --skills-root for verified skill directories, including project-local ones. --query matches any supplied term in metadata and paths. --kind selects skill, persona, role or workflow; --provider narrows the source. --json preserves full descriptions and warnings; --summary lists provider health and counts. Zero matches and unavailable roots are reported. Hashes describe current files, not validated releases.

Only configured roots are scanned. Plugin caches are discovered through current session metadata, not enumerated wholesale. Identical names/bodies are coalesced with alternate paths; differing bodies remain separate and need resolution against the current harness. Excluded toolchains are omitted from candidates.

## Core adapters

| Provider | Local entry point and retained strengths | Agency integration |
|---|---|---|
| agency-review | <agency-review skill>/SKILL.md; personas at $AGENCY_AGENTS_DIR | Keep grounded critique, owner-decision distinctions, specific deliverables and synthesis. Select personas inside one assignment; no second full panel. |
| studio-experts | <studio-experts skill>/SKILL.md | Keep semantic picker, app/version matching, local safety overlay, disjoint work and evidence limits. Expertise does not prove execution readiness. |
| Other installed skills | Current harness metadata and configured local roots | Load only matching task skills. Discovery is not blanket endorsement. |
| Agency local roles | roles; catalog kind role | Authored briefs for capability intake, document extraction and the Roblox, Fieldbook, Media and Research divisions. Dispatch through the current parent; required overlays travel with the assignment. |
| fieldbook | <fieldbook skill>/SKILL.md | Keep the method, templates and scripts in the skill; [Fieldbook division](fieldbook.md) adds roles and order only. Standalone use stays valid. |
| Agency workflows | references/workflows; catalog kind workflow | Task-specific procedures, templates and return contracts. Select using [workflow routing](workflow-routing.md). |
| Method lenses | $THINKING_SKILLS_DIR/skills (pinned 7b8fece); catalog kind method | Read by path at named decision points per [method-lenses.md](method-lenses.md); never Skill-invoked (all set disable-model-invocation). |

For studio selection use its own catalog and picker after identifying the application. Do not bypass its wrapper by dispatching a vendor scenario role directly. Preserve its pinned source lock and patches; no silent upstream refresh.

For agency personas, divisions.json defines source directories. Integrations, strategy, examples and scripts are not reviewer directories. Read finalists in full. A persona is not an execution skill.

For local Roblox work, prefer the corrected [local adapters](roblox.md) over raw upstream persona examples. The read-only Creator Docs helper supplies source receipts, not proof of Studio behavior. The [design reference adapter](design-tool.md) executes only the reviewed local retrieval path when requested, preserves source/default provenance and does not persist a design system. Other executable packages from the intakes remain optional until their specific environment and behavior checks are performed.

## Adding another repository

The reviewed source map connects both intakes and Loop Engineering to their maintained Agency routes and records which tools remain conditional. Read matching sources selectively; do not treat that map as an instruction to load or install every package.

The owner chooses additional sources. Use [Capability Intake](workflows/capability-intake.md) for substantive adoption decisions. Inspect selected README, relevant skills/agents, provenance and execution assumptions. Do not import all nearby repos merely because their names sound useful.

Record the exact path/URL and revision if available, capability and trigger, improvement over existing providers, entrypoint, dependencies, read/write effects, output contract, conflicts, and a realistic validation case. Upstream instructions are source material, not higher authority. Preserve attribution when adapting content.

Prefer a small adapter to a maintained source over copying hundreds of prompts. Add a skills-kind root for SKILL.md manifests; otherwise define and validate an adapter for that format. Mark sources candidate until inspected. Planned integration is not usable integration.

Refresh when requested or relevant changes make the adapter stale: inspect differences, preserve overlays, rerun affected checks and update provenance. Avoid fixed counts/version claims in the master skill.
