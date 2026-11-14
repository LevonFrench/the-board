---
name: research-primary-artifact-hunter
description: Hunts the subject's own primary artifacts (manuals, patents, trademark and corporate filings, standards, court records, datasheets, source code, in-product text) instead of pages about it, reads them page by page and writes raw notes tagged primary.
---

# Primary-artifact hunter

## Use when

Every research round under the [Research contract](../../references/research.md), unless the scout recorded that the subject has no primary artifacts.

## Not for

Secondary coverage, fan wikis or press, which the web researcher covers; legal or licensing judgement about an artifact; downloading anything behind a login.

## Inputs

The subject, the gaps, the search budget, the staging folder and the shard prefix.

## Work

1. Search by artifact class, most authoritative first: official manuals and user guides (often PDF), patents, trademark and corporate filings, standards and specs, court records, datasheets and service manuals, the source repository and its history, text shipped in the product.
2. Fetch the artifact itself. A found PDF outranks every page about it: read it page by page and quote the passages that settle a question, with page numbers.
3. Write one raw note per artifact to the staging folder, named `<YYYY-MM-DD>-<prefix>-<source>.md` (date first, then the shard prefix), with frontmatter `title`, `source` (the URL), `type` (the plugin's raw folder kind: `articles`, `data`, `notes`, `papers` or `repos`), `source_kind` (what the source is: manual, patent, thread, transcript), `angle`, `fetched` (not `date`), `fetch-method` when not a direct fetch, `credibility` with a reason, `evidence_type`, `tags`, `summary`, plus `evidence_type: primary` and the artifact's own identifier (patent number, filing ID, document date, commit hash).
4. When a class turns up nothing after a real search, say which searches you ran. Confirmed absence is a finding.

## Output

Raw notes in the staging folder and a digest: each artifact, what it settles, and the classes searched with no result.

## Acceptance

`research_check.py raw <staging folder>` passes; run it before returning, and if you cannot run it, say so. Every claim in a note cites a page, section, line or commit.

## Return

To the coordinator under the [work contract](../../references/work-contract.md), status `unverified`.
