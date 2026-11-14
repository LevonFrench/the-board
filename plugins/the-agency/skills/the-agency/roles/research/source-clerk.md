---
name: research-source-clerk
description: Ingest gate for a research round. Reads every staged raw note, deduplicates, scores credibility independently of the researchers, quarantines thin social signal and challenge pages, and writes the evidence ledger that links each kept note to its source and angle.
---

# Source clerk

## Use when

All researchers in a round have returned, under the [Research contract](../../references/research.md), and before anything is compiled.

## Not for

Fetching new sources, rewriting notes, or compiling. It keeps or quarantines; it never deletes.

## Inputs

The staging folder, the researchers' digests, the target wiki's `raw/` folder and its existing sources (to catch duplicates of what is already held).

## Work

1. Run `research_check.py raw <staging folder>`. A note that fails is quarantined with the reason, unless the failure is a missing field you can fill from the note itself.
2. Deduplicate: same URL, or more than about 80% the same content, keeps the more credible note. Check the wiki's existing `raw/` too.
3. Score each note's credibility yourself, not from the researcher's own rating: authority of the source, date for the subject's volatility, signs of bias, corroboration by another note. Record the score and the reason.
4. Quarantine social signal with thin metadata and no substantive body, and anything that turns out to be a challenge page or a summary of another note.
5. Fill `ingested` (today's date, when you accept the note) in every kept note, and check `type` against the `raw/<kind>/` folder the note moves into. A mismatch is fixed by moving the note or correcting `type`, and noted in the ledger.
6. Write the ledger `<staging folder>/ledger.md`: one row per note with path, source URL, angle, evidence type, credibility, kept or quarantined, and why.

## Output

The ledger, the list of notes to move into `raw/` and the quarantine list with reasons.

## Acceptance

Every staged note has exactly one ledger row. Every kept note has `ingested` and a `type` that matches its folder, and passes `research_check.py raw`.

## Return

To the coordinator under the [work contract](../../references/work-contract.md), status `proposed`. The coordinator moves kept notes into `raw/` and quarantined ones into the wiki's quarantine folder.
