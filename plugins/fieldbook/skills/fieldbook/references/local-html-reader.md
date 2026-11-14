# Local HTML reader

Use this reference when a Fieldbook needs a browsable local endpoint. The intended deliverable is a static, private-first reader that opens from disk and sits beside—not instead of—the Markdown knowledge base.

`scripts/build_reader.py <root>` generates all of this from Markdown and needs only Python. Set title, topic order, footer, accent and `newest_source` in the `reader:` config block. Do not write a one-off generator per Fieldbook; `output_mode: single-file` covers the one-document case. This reference is the contract the generator meets, and the standard for a custom reader when the owner asks for one.

## Required structure

```text
fieldbook/
  index.html
  README.md
  source-ledger.md
  coverage-matrix.md
  gap-register.md
  editorial-note.md
  topics/
  site/
    index.html
    styles.css
```

`index.html` provides the user-facing entry point. It may immediately route to `site/index.html`, but must contain a normal anchor fallback. All styles, images, and scripts must be relative files under the Fieldbook output; prefer no script at all for a research reader.

## Reader anatomy

1. **Orientation** — subject, private/public status, update date, and how to use the reader.
2. **Start here** — the current decision, research question, or recommended reading sequence.
3. **Topic navigation** — compact anchors/cards leading to major compiled areas.
4. **Findings and limits** — each concise claim carries an evidence/provenance state and meaningful date/limit.
5. **Evidence paths** — explicit links to the pages for the README, relevant topics, source ledger, coverage matrix, gap register, and editorial note. Generated pages mirror the Markdown, which stays beside the reader. Guidance and inventory are left out of a single file or a non-private reader by default; `reader.include_internal` overrides.
6. **Next research** — unresolved questions and the user’s steering route through `guidance.md`.

## Safety and fidelity

- Markdown is canonical. Do not make an HTML-only claim, source record, correction, or decision gate.
- Summarize instead of duplicating long source passages or private local material.
- Do not reveal absolute file paths, source-root locations, restricted filenames, hashes, credentials, browser state, cookies, or unpublished material.
- Preserve `unknown`, `contested`, `lead-only`, and `not-checked` as visible states.
- Do not create a false impression of live data: date static rosters and state the appropriate refresh action.
- Superseded pages move to a folder listed in `legacy:`, with a banner saying what replaced them; the checker skips them and says so. Keep one copy of any shared asset and record its source path in `editorial-note.md`.
- A reader may link only to files that are safe to read: do not link a config or inventory that holds an absolute path.

## Validation

Before handoff, run `scripts/check_fieldbook.py <root>`: it verifies both HTML files, the root endpoint, every relative `href`, `src` and CSS `url()`, in-page anchors, raw label tags, orphan pages, and `file:` or drive-root paths in HTML and anything HTML links to. Confirm the page reads well at a narrow viewport when visual inspection is available. Keep the run local unless the user explicitly asks to publish.

## Rendering wiki articles directly

Where a topic wiki holds long tables a reader should browse, list its articles under `reader.wiki_articles`, as paths relative to the Fieldbook root and inside a declared source root. `build_reader.py` renders them as Full data pages with no copy in the Fieldbook, and topic links to those articles work. `reader.wiki_note` sets the note on each page, for example to explain the wiki's tags. `reader.labels` sets short nav names by page slug. Correct these pages in the wiki and rebuild.
