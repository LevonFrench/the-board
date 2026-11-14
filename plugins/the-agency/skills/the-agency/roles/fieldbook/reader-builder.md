---
name: fieldbook-reader-builder
description: Generate the Fieldbook's static local HTML reader from canonical Markdown with the shared generator, or implement a site when the config calls for one, keeping every claim traceable to Markdown and every path private.
---

# Fieldbook reader builder

## Use when

`output_mode` is `both`, `single-file`, `web-fieldbook` or `web-app` and the Markdown is ready to show. Load the [Fieldbook contract](../../references/fieldbook.md) first.

## Not for

New claims, or any deployment. A custom site is only for an owner-requested `web-app`.

## Inputs

The compiled Fieldbook, the `reader:` config block, <fieldbook skill>/references/local-html-reader.md and <fieldbook skill>/references/fieldbook-site-and-kb.md.

## Work

1. Default: `python <fieldbook skill>/scripts/build_reader.py <root>`. Read its list of links dropped to text and fix the cause in Markdown where it matters. Never hand-edit generated pages; change Markdown or config and rebuild. It needs no pandoc, server, framework or remote asset.
2. It refuses to overwrite pages it did not generate. Move old pages to a legacy folder listed in `legacy:`, with a banner. Force only with the parent's approval.
3. `web-app` mode: use the actual stack and a matching implementation skill. Site data carries source IDs resolving to the ledger; shared components hold repeated caveats. Add a static reader or record in `editorial-note.md` why none exists. One book's site needed a dev server and held facts with no Markdown record.
4. Open the reader from disk and read it at narrow width when a browser is available. A visual pass is level 4 on the [ladder](../../references/work-contract.md#evidence); say so if it was not run.

## Output

The generated reader, the dropped-link list and known display limits for `editorial-note.md`.

## Acceptance

Build self-check passes. `check_fieldbook.py` reports no links, leaks, raw_tags or orphans findings, or each is listed with a reason, and the reader is reached from root `index.html` with a no-script fallback (or is the one file for `single-file`). Release status is visible on the reader.

## Return

To the parent under the [work contract](../../references/work-contract.md), with `ready-for-integration`, the check output and whether it was viewed. Do not deploy.
