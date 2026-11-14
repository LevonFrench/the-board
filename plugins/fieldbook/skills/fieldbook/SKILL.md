---
name: fieldbook
description: Build, research, audit, refresh and publish a source-backed Fieldbook, a decision-grade knowledge base with a browsable reader, on a local market, a household decision, a game or product's real state, a company or person, or an archive. Use when a user asks for a Fieldbook, wants a detailed evidence-led knowledge base on a city, region, vertical, house, company or collection, wants business opportunity analysis or competitor and provider lists with sources, or wants an existing Fieldbook checked, expanded or rebuilt. For a Fieldbook run with a team, fan-out or review-fix loop, use The Agency's Fieldbook division.
license: Unlicense
compatibility: "Python 3 (tested on 3.12). Web access for research runs. No other skill needed."
---

# Fieldbook

Create a decision-grade knowledge base and a browsable reader. Make the difference between fact, current signal, inference, hypothesis and unknown visible everywhere. Most defects in past Fieldbooks were checks nobody ran, so run the scripts in this skill rather than checking by eye.

## Start correctly

1. Confirm the subject, the decision, the audience, the time horizon and the deliverable. Ask only what cannot be safely inferred: output location, audience, whether external research is allowed, out-of-scope topics. A request to "auto-fill," "auto-expand" or "do wiki research" authorizes bounded public research.
2. Choose the subject kind: `market`, `household`, `project-state`, `entity` or `archive`. Each has its own proof chain, tracks and decision card in [subject-kinds.md](references/subject-kinds.md). Do not force buyer and pilot fields onto a house or a game.
3. Inspect the workspace before creating files. Preserve unrelated work. Never overwrite an existing wiki or source archive.
4. Place the Fieldbook. With a topic wiki, it lives at `<topic>/output/projects/<slug>/`: evidence stays in the wiki under its rules, and Fieldbook topics summarize and cite wiki articles without forking them. Otherwise use `<project>/fieldbook/` or the exact location the user names. The slug names the subject, never the genre.
5. Create `fieldbook.config.yml`, `guidance.md` and the rest of the record from [assets/templates](assets/templates/) for every run, before synthesis. The config holds kind, status, release status, source roots and output mode. The guidance log holds dated owner direction and every evidence item the owner supplies. Both are operating briefs, not evidence. An owner hold (`status: on-hold`) stops the build until lifted.
6. When scope is broad, write a research plan first: decision questions, source classes, deliverables, proof still needed.
7. State assumptions that would change recommendations. Do not manufacture a neighborhood, customer, budget, operating authority or product preference. If the owner asks for a pitch, record that framing in the config, keep every label and limit, and list in `editorial-note.md` each claim the framing states more strongly than the evidence allows.

Never collapse the proof chain. For a market:

```text
Public source → evidence record → bounded finding → business hypothesis
              → buyer interview → paid pilot → repeat/stop decision
```

A provider directory is not buyer demand; a social post is not market sentiment; a platform listing is not permission, capacity or market share.

## Inventory before browsing

When local material exists (project, archive, wiki, game, artist, company, research folder):

1. Inventory first: `_index.md`, manifests, README files and ledgers, then a file-level `local-evidence-inventory.md`. Declared roots only.
2. Build `coverage-matrix.md` and `gap-register.md` before writing synthesis. Classify each topic `local-covered`, `local-partial`, `external-needed`, `contradicted`, `unknown` or `out-of-scope`.
3. Research only gaps and contradictions. Search exact names, claims, dates and credits first. Wikipedia is a discovery lead, not the only source for a consequential claim. A private project may set `external_research: none`; say so and skip this step.
4. Add evidence incrementally with source URL, accessed date, claim boundary and limit. A search result, fan database or uncorroborated credit is never a fact.

Exact protocol: [local-first-wiki-research.md](references/local-first-wiki-research.md). With a formal LLM wiki, also use the wiki skill and preserve its raw/compiled split.

## Research procedure

Standards, schemas and critic prompts: [research-and-evidence.md](references/research-and-evidence.md).

1. **Source ledger before prose.** Record publisher, URL, accessed date, geography, time basis, claim type, volatility and limits. Prefer primary and official sources for population, regulation, licensing, transport, labor, prices and public programs. First-party sites show what an operator claims; never use them alone for market-wide conclusions. A volatile claim carries its refresh action.
2. **Lists as datasets, not prose.** Structured fields, preserved unknown states, one row per location where service differs. "Not found in this pass" replaces "does not offer"; a negative finding declares its search boundary and is never proof of absence.
3. **Synthesize in levels:** measured fact, public-web signal, inference, hypothesis, gate, boundary. Use the one label vocabulary. A page you did not open is `search-extract`, not `external-primary`.
4. **No unearned rank.** Never use numeric scoring, "high confidence," "largest," "best" or "strongest" without an explicit method and adequate evidence. Order decisions with named tiers (`test-now`, `queue`, `hold`) and a reason; a 1-to-N list keeps reading as a ranking however it is labelled.
5. **Keep the source's words on money and scope.** Projected is not actual, per-worker is not uncapped, phase is not total. Every money figure carries a basis in its row, or "allowance, unsourced".
6. **People.** Role and public business facts only, unless the owner asks for a specific public record. No phone numbers, tax IDs, home addresses, or education and family history as padding.
7. **Internal stays internal.** A page a prospect may read keeps delivery cost, margin and fallback fees out. They go in an internal record; the reader links only public scope.

## Keep evidence moving

- **Sweep after every ingest.** List every topic, site record and index row naming the same entity; update it or mark it `stale-pending-compile`. A capture no topic cites goes in the gap register as `uncompiled`. Late evidence reopens what it touches.
- **Reconcile before stating current status.** Compare the newest source record with topic dates. If a source is newer, add a reconcile item to `refresh-backlog.md`, show the newest source date on the reader, and do not call the Fieldbook current.
- **Correct by kind.** Label each finding `contradicted-by-source`, `not-in-our-capture`, `stale` or `overstated`. For `not-in-our-capture`, capture the primary source before changing anything.
- **One compiled copy.** Never maintain a parallel draft tree beside a wiki. Generate readers from the record.
- **Generate counts; do not type them.** Handoffs link to the index and do not restate numbers. Do not turn a query result into a permanent count.
- Raw captures are immutable. Corrections go in compiled topics plus `editorial-note.md`. Append to `guidance.md` and any activity log; on an expand request, read them first and research only new or stale gaps.

## Fan out safely

Use The Agency's Fieldbook division when a run needs a team: <the-agency skill>/references/fieldbook.md. Without The Agency, assign non-overlapping bounded tracks. Every agent returns a source-linked table plus caveats; only the primary agent edits shared indexes and canonical summaries.

Before calling a broad Fieldbook partner-ready, run no-edit critic passes as separate lenses: **accuracy** (contradictions, stale counts, source and date mismatch, unsupported superlatives), **clarity** (reading path, duplicated terms, mobile access), **strategy** (competing plans, unsafe roles, gates and stop rules). Apply only findings that are evidenced and material. Record the result in `editorial-note.md`.

## Build the reader

Markdown is canonical. The reader is a presentation layer, never a new source of truth: no HTML-only claim, source record, correction or gate. If a claim cannot be traced to Markdown, capture it first or remove it.

```bash
python <this skill>/scripts/build_reader.py <fieldbook-root>
```

It writes `index.html` plus `site/` (or one self-contained file for `output_mode: single-file`), with no server, framework, remote asset, script or dependency beyond Python. It refuses to overwrite pages it did not generate. Never hand-edit generated pages; change Markdown or config and rebuild.

| `output_mode` | Use for | Delivers |
|---|---|---|
| `both` (default) | Most runs | Markdown record plus `index.html` and `site/` |
| `single-file` | A dossier to send to someone | Markdown record plus one self-contained HTML |
| `markdown-kb` | Explicit Markdown-only request | Markdown record only |
| `web-fieldbook` | Reader as the main route | As `both`, with reader-first navigation |
| `web-app` | Owner asks for search, filters or dynamic routes | A built site whose data still traces to Markdown; add a static reader, or record in `editorial-note.md` why none exists |

Readers never show absolute paths, source-root names, restricted material, secrets or hashes, and never leave out `unknown`, `contested`, `lead-only` and `not-checked`. A private Fieldbook says so on the page. Design rules: [fieldbook-site-and-kb.md](references/fieldbook-site-and-kb.md), [local-html-reader.md](references/local-html-reader.md).

For regulated or professional work, describe the support layer precisely. A web or data vendor does not become the merchant of record, delivery operator, PLS, engineer, adjuster, clinician, public-safety operator or licensed seller by building an interface.

## Validate and publish

```bash
python <this skill>/scripts/check_fieldbook.py <fieldbook-root> [--release] [--site <dir>] [--canonical <dir>]
```

It reads only, and says so when a check could not run. It reports structure, config, frontmatter, links, path leaks, raw tags, superlatives, claim trace, uncompiled captures, staleness, counts, status conflicts, ledger paths, money rows, chat leftovers and personal data. Warnings are candidates for judgement, not verdicts. Before handoff:

1. Run the checker with `--release`; resolve every error or list it for the owner.
2. Hand-trace at least six consequential claims to their sources. The checker traces percentages, dollar amounts and comma-separated numbers to a record; it cannot trace small plain numbers or tell that a projection was stated as actual.
3. Read the reader from disk and at narrow width when a browser is available; say so when not.
4. Make status true: config, topics, editorial note and commit language agree. Every script a note cites exists in the repo, and a receipt reports what was measured: one pitch said "passed" with 25 of 31 local files missing.

Checklists, archives and hosting by host: [validation-and-publishing.md](references/validation-and-publishing.md). Do not deploy by default. Publishing needs the owner's words for that act; state that it will be public, then return only the link and essential handoff details.

## Completion standard

Deliver the Markdown record plus the reader for its output mode, source-linked research and rosters, a refresh backlog, decision cards for the subject kind with non-negotiable gates, an editorial record of corrections and remaining unknowns, and the checker's receipt.

A Fieldbook is not complete because it is long. It is ready for review when a reader can see what evidence was used, tell local from external findings, find every important source and gap, steer the next expansion, and resume without re-researching settled claims.

Never present a Fieldbook as investment, legal, regulatory, medical, employment, surveying or tax advice.

"Owner" in this skill means the person who gave the assignment.
