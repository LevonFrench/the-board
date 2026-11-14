# Guided local-first Fieldbook research

Use this procedure for a subject that already has local files, a wiki, a codebase, a collection, or prior research.

## User steering contract

Create `fieldbook.config.yml` and `guidance.md` from [assets/templates](../assets/templates/) before substantive synthesis. Keep the configuration machine-readable and append every later instruction to the guidance log, along with each evidence item the owner supplies (what, date, privacy limit). A late record often reworks earlier pages, so list what it touches. Owner preferences such as full paths apply to chat handoffs; HTML stays path-free. Copy tables from the templates so their columns stay the same across runs.

Accept natural-language steering at any time and append it with a date. Interpret these as control commands, not evidence:

- `focus on …` / `expand …` — prioritize a topic and its open gaps.
- `freeze …` / `local-only` — stop external research for that topic or the run.
- `ignore …` / `out of scope …` — retain the omission in the gap register.
- `verify …` — audit a specific claim against primary sources.
- `write for …` — change audience and the output level without changing the evidence.
- `research gaps` / `auto-expand` — run the bounded external gap-fill pass.
- `refresh …` — revisit only volatile or unresolved records.

## Inventory before internet research

1. Check each declared source root resolves and record availability/access limits. Record it as a path relative to the Fieldbook or a stable ID; absolute paths belong in chat handoffs, never in the record, where they fail the release check. Do not auto-traverse another root merely because a local document mentions it.
2. Read existing `_index.md`, `README`, `AGENTS.md`, manifests, source ledgers and topic indexes before broad scanning.
3. Inventory local files by type and role: primary capture, project/code evidence, contemporaneous artifact, prior synthesis, image/media, source list, generated output, duplicate or unknown.
4. Extract only claims that the local material actually supports. A project note may be useful technical evidence but not a historical fact; a copied wiki page may be a lead rather than a source. Default-exclude dependencies, build artifacts, secrets, binaries and large media; record them as corpora/assets rather than ingesting or copying them.
5. Save `local-evidence-inventory.md` with one row per meaningful item:

| ID | Local path | Artifact type | Topic | What it supports | Confidence | Limits |
|---|---|---|---|---|---|---|

Do not copy copyrighted source material wholesale. Describe, link to local paths and quote minimally when essential.

## Coverage and gap controls

Create `coverage-matrix.md` before writing topic pages:

| Topic | Local evidence | Status | Exact missing question | Best external source class | Next action |
|---|---|---|---|---|---|

Create `gap-register.md` for anything not ready to publish:

| Gap ID | Topic | Why it matters | Search plan | Status | Resolution / limit |
|---|---|---|---|---|---|

Status meanings:

- `local-covered`: enough local evidence for the bounded claim.
- `local-partial`: publish only the supported portion and state what is missing.
- `external-needed`: public research is the next justified action.
- `contradicted`: competing claims need source comparison; do not choose casually.
- `unknown`: no adequate evidence found in the defined pass.
- `out-of-scope`: intentionally not researched.

## Bounded gap-fill research

For each `external-needed` or `contradicted` record:

1. Search the exact claim/name/date from the local evidence, then aliases and period terminology.
2. Prefer: official publisher/developer/creator material, archival catalog, contemporaneous manual/press, credited interview, institutional collection, then reputable specialist history.
3. Capture a source ledger row: publisher, title, URL, publication/access date, claim supported, evidence class, geography/time basis if relevant, and limitation.
4. Cross-check consequential credits, hardware/release facts, ports, release dates and creator biographies with at least two independent source classes when practical. If only one exists, label it as a source claim.
5. Put unresolved disagreements in a dedicated contradiction note. Never force a tidy timeline by discarding the inconvenient source.

Research should stop when the stated questions have an adequate, cited answer or when the next source class is unavailable. Add the remaining work to `refresh-backlog.md`; do not keep browsing just to make the Fieldbook appear complete.

## Output schema

Create an isolated output folder: `<topic>/output/projects/<slug>/` when a topic wiki exists, otherwise `<project>/fieldbook/` or the exact user-selected destination. Keep research inputs inside it, or declare one source root and cite items by stable ID; no `../../` links from the record. Name the slug for the subject. Tables come from [assets/templates](../assets/templates/).

```text
fieldbook/
  fieldbook.config.yml          # user-editable steering and publication controls
  README.md                    # browsable start page and reading routes
  raw/                         # optional: immutable captures and research notes
  guidance.md                  # user direction, not evidence
  local-evidence-inventory.md
  coverage-matrix.md
  gap-register.md
  source-ledger.md
  refresh-backlog.md
  editorial-note.md
  topics/
    history.md
    technology-or-work.md
    people-and-credits.md
    releases-ports-or-catalog.md
  site/                         # static local reader and its relative assets
    index.html
    styles.css
  index.html                    # direct-open endpoint to site/index.html
```

Adapt topic names to the subject. Every compiled topic starts with frontmatter containing `title`, `status`, `sources`, `local_evidence`, `confidence`, `updated`, and `open_questions`. Default `output_mode` to `both`: a Markdown-only request is the exception, not a reason to leave a local research run without an accessible reading route.

Use the one [label vocabulary](research-and-evidence.md#label-vocabulary) in ledgers and prose.

Every evidence item records origin, relative path or URL, captured/accessed date, revision/hash when permitted, release/rights constraint, claim IDs and limitations. Do not publish private absolute paths, hashes, credentials, or restricted media metadata.

## Completion and expansion

Do not call a Fieldbook complete because it is long. It is ready for a user review when the reader can:

1. see what local material was used;
2. distinguish local findings from external research;
3. find every important source and unresolved gap;
4. steer the next expansion using `guidance.md` or a plain-language request; and
5. resume incrementally without re-researching settled claims.

Before any handoff or statement of current status, compare each source root's newest dated record with every topic's `updated` date. If a source is newer, add a reconcile item to `refresh-backlog.md` and show the newest source date on the reader's orientation block. `check_fieldbook.py` reports this as `staleness`. After every ingest, run the propagation sweep in [SKILL.md](../SKILL.md#keep-evidence-moving).

On a later “expand” request, read `guidance.md`, `coverage-matrix.md`, `gap-register.md`, `source-ledger.md` and relevant topic pages first. Research only the new or stale gaps, update the indexes and append an editorial note describing what changed.

## Local reader contract

Build `index.html` and `site/index.html` with `scripts/build_reader.py` as a static endpoint for every `both` or `web-fieldbook` run. It is a local companion to the Markdown KB:

1. `index.html` redirects or links to `site/index.html`; the regular link is required as a no-script fallback.
2. `site/index.html` is responsive, self-contained except for relative assets in `site/`, and uses no remote assets, tracking, authentication, or development server.
3. Include an orientation/start-here view, topic navigation, key findings, source/provenance states and research gaps. Generated pages mirror the canonical Markdown files, which stay beside the reader.
4. Never include local absolute paths, private source-root names, restricted quotations, secrets, hashes, browser state, or unpublished credentials. Refer to evidence using safe relative links and summaries.
5. Treat the reader as a compiled view: summarize evidence with citations/labels; keep detailed source records and correction history in Markdown. Update its summary after any material Markdown change.
6. Before handoff, run `scripts/check_fieldbook.py` for relative targets and path leaks, then open the reader. Record reader date and known display limits in `editorial-note.md`.
