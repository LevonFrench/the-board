# The Board

Many agents and skills from other projects, working as one. For Claude Code and Codex.

This repo does not replace the projects it draws on. It brings them together. A coordinator picks the smallest team for a job from personas, specialist skills and methods that other people wrote, gives each piece of work one owner, and checks the result. What is written here is the part that joins them: the coordinator, the pickers, the contracts between workers and the checks. This project is not affiliated with any of the projects below.

## What it brings together

| From | What it contributes | How it gets here |
|---|---|---|
| [agency-agents](https://github.com/msitarzewski/agency-agents) | Personas for engineering, design, testing, product and more | You clone it. `agency-review` and `the-agency` read the personas at run time |
| [Scenario's skills](https://github.com/scenario-labs/skills) | 58 specialist roles for Unity, Unreal, Blender, Maya and ZBrush | `studio-experts` fetches them at a pinned commit |
| [cc-thinking-skills](https://github.com/tjboudreaux/cc-thinking-skills) | Structured thinking procedures | You clone it. `the-agency` reads them as method lenses |
| [Roblox creator-docs](https://github.com/Roblox/creator-docs) | The Roblox platform documentation | You clone it. The Roblox division looks things up in it |
| [ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | Design reference data | You clone it. `the-agency` queries it |
| [mattpocock/skills](https://github.com/mattpocock/skills) and fourteen other projects | Ways of working, such as delivery contracts, review loops, prose checks and audience panels | Adapted into `the-agency`'s workflows. Each is credited in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) |
| Optional tools: flawless-ui-ux, simcraft, cinematic-skill, agent-browser, the llm-wiki plugin | Checks, simulations, film scenes, browsing and a wiki | Named in the workflows and used only when you have them |

Their files are not copied into this repo: you fetch or clone each one yourself, under its own licence. The one exception is the names and one-line descriptions of Scenario's roles, which the picker needs and which stay under Scenario's MIT licence.

## What is written here

Four skills. Each installs alone.

| Skill | What it does | Needs |
|---|---|---|
| `fieldbook` | Builds a source-backed knowledge base with a browsable reader, and audits or refreshes one | Python 3 (tested on 3.12), web access for research |
| `agency-review` | Runs a multi-persona critique of a project, plan or codebase | A clone of [agency-agents](https://github.com/msitarzewski/agency-agents) |
| `studio-experts` | Picks Unity, Unreal, Blender, Maya, ZBrush and Godot specialists | Files from [Scenario's skills](https://github.com/scenario-labs/skills) at a pinned commit, fetched by its setup script. Godot works without them |
| `the-agency` | Coordinates a specialist team through planning, implementation and checks, with its own role cards for Roblox, Fieldbook, Media and Research work | Nothing required; uses the others when present. Its Research division assumes a wiki made with the [llm-wiki plugin](https://github.com/nvk/llm-wiki) |

## Quick start: Claude Code

```
/plugin marketplace add LevonFrench/the-board
/plugin install fieldbook@the-board
```

Then ask for a Fieldbook on a subject you know well, so you can judge the result. Install each skill once, by one route: two routes give you duplicate skills.

## Quick start: Codex

Clone this repo, then copy or link the skill folder you want into `~/.agents/skills`:

```
git clone https://github.com/LevonFrench/the-board
cp -r the-board/plugins/fieldbook/skills/fieldbook ~/.agents/skills/fieldbook
```

## What to know before running it

- **Cost:** `the-agency`, `agency-review` and `studio-experts` can start several agents. They state the team first, but they use your model allowance. Set a limit before a long run.
- **Data:** the skills are local Markdown and Python with no telemetry. Research runs fetch web pages, and your agent's own provider sees what it reads.
- **Scripts:** the Python scripts use the standard library (Fieldbook also uses PyYAML when it is installed) and read or write inside the folder you name. One exception: `the-agency`'s `scripts/build_agents.py --apply` writes subagent files to `~/.claude/agents`. It runs only when you ask, and without `--apply` it prints a plan. Read upstream skills before running their scripts: you clone those yourself, at a pinned commit.
- **Advice:** Fieldbook supports research. It is not legal, financial, medical or other licensed advice.

## Optional setup

| Variable | Points at | Used by |
|---|---|---|
| `AGENCY_AGENTS_DIR` | A clone of msitarzewski/agency-agents | `agency-review`, `the-agency` |
| `THINKING_SKILLS_DIR` | A clone of tjboudreaux/cc-thinking-skills | `the-agency` |
| `CREATOR_DOCS_DIR` | A clone of Roblox/creator-docs | `the-agency`'s Roblox division |
| `DESIGN_REFS_DIR` | A clone of nextlevelbuilder/ui-ux-pro-max-skill | `the-agency`'s design references |

If one is absent, the skill skips what needs it and says so.

## Keeping up with upstream

Your copy will drift as you adapt it, so updates never overwrite it. Ask `the-agency` what is new upstream, or run `python -B scripts/upstream_updates.py` from its folder. It lists which source repos changed, and for a pinned source it sorts each change by whether you edited that file too. It proposes and you choose. It runs no upstream code.

## Status

Developed and tested on Windows. The workflow in `.github/workflows/tests.yml` runs the tests on Linux, macOS and Windows on every push, so check its latest result for your system.

Run the tests yourself from the repo root:

```
python -B -m unittest discover -s plugins/fieldbook/skills/fieldbook/tests
python -B -m unittest discover -s plugins/studio-experts/skills/studio-experts/scripts
```

Fieldbook has the most test coverage. The Studio Experts tests skip what needs the Scenario files until you have fetched them. `the-agency` ships its scripts without their tests in this first version.

## Licence and credits

This project's own material is released into the public domain under the [Unlicense](LICENSE): no copyright is claimed and no credit is required. Material that comes from other projects keeps its own licence, listed in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). This project is unaffiliated with agency-agents, Scenario, Roblox or any engine vendor.
