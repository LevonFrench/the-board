# Fieldbook

`fieldbook` is a Claude Code and Codex skill for building a source-backed Fieldbook from a local archive, a wiki or public research. It covers five subject kinds: market, household, project state, entity and archive.

It turns broad questions—“What can we sell here?”, “Who are the incumbents?”, “Where are the buyers?”, “Should we build this?”—into a disciplined flow from public evidence to buyer interviews, paid pilots, and a clear stop decision.

## What it covers

- City and regional market research: population, geography, labor, training, commuters, permits, development, and institutions.
- Local commerce: restaurant/delivery inventories, grocery/alcohol/regulated-commerce boundaries, providers, and direct-order gaps.
- Sector modules: AI consulting, real estate/listing media, drones/geospatial, social signals, healthcare/ABA, or user-defined verticals.
- Interactive Fieldbook websites: executive path, searchable rosters, linked evidence, business-brief detail pages, sources, research ledger, and editorial review log.
- Local HTML endpoints: every guided Fieldbook can ship as a direct-open, static `index.html` reader while Markdown remains the canonical evidence layer.
- Business opportunity design: buyer, smallest offer, authority boundary, 30/90-day gate, cost-to-serve, and stop rule.
- Critic/editorial passes, scripted validation and reader generation, performance checks, and optional publication where the host supports it.
- Guided local-first research: inventory an existing project/wiki first, make coverage and gaps explicit, then perform bounded wiki/web research only where local evidence is incomplete.

## Use it

```text
Use $fieldbook to build a source-backed business intelligence Fieldbook for [place].
Start with a research plan, create a browsable local knowledge base and website,
rank only qualitative business tests, run an accuracy/clarity/strategy critic pass,
and keep the result local until I explicitly authorize publication.
```

For an existing archive, game, artist, company, or collection:

```text
Use $fieldbook for [subject]. Start with these local folders: [paths].
Write guidance.md so I can steer the work, inventory local evidence before browsing,
show the coverage and gap registers, then auto-research and expand only the gaps.
Keep source provenance visible and do not overwrite the original wiki.
```

The resulting local Fieldbook includes `index.html` and `site/index.html`, so it can be opened directly from disk without hosting. The reader mirrors the canonical Markdown topics, evidence ledger, coverage matrix, and gap register.

## Core rule

Keep the proof chain visible:

```text
Public source → evidence record → bounded finding → business hypothesis
              → buyer interview → paid pilot → repeat/stop decision
```

The skill forbids treating a directory, platform listing, social post, permit, training course, or provider claim as proof of paid demand, capacity, legal authority, or market share.

## Contents

- [SKILL.md](SKILL.md): the operational workflow.
- [Research and evidence standards](references/research-and-evidence.md): source hierarchy, roster schemas, claim matrix, social-media protocol, critic prompts, and business-brief template.
- [Fieldbook site and knowledge-base design](references/fieldbook-site-and-kb.md): information architecture, UI/data model, editorial rules, and wiki protocol.
- [Validation and publishing](references/validation-and-publishing.md): release checklist, Lighthouse/PageSpeed process, archives, hosting by host, and editorial report template.
- [Guided local-first research](references/local-first-wiki-research.md): user steering, local inventory, gap register, bounded external research and incremental expansion.
- [Subject kinds](references/subject-kinds.md): proof chain, tracks and decision card for each kind.
- [Templates](assets/templates/): blank config, registers, ledger, editorial note and topic.
- `scripts/check_fieldbook.py` (read-only validator) and `scripts/build_reader.py` (static reader generator). Python only; tests in `tests/`.

For a run that needs a team, The Agency's Fieldbook division assigns these jobs to workers: <the-agency skill>/references/fieldbook.md.

## Install

Install it as a Claude Code plugin from this repo's marketplace, or copy this folder into `~/.agents/skills` for Codex. Keep the books you build outside this folder.

## Boundaries

Fieldbook supports research and product design. It is not investment, legal, regulatory, medical, employment, surveying, engineering, tax, or public-safety advice. It requires the responsible licensed or authorized party to remain visible in regulated and professional workflows.
