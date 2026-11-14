---
name: research-wiki-steward
description: Coordinator-applied closing step of a research round. Re-lists raw sources, rebuilds derived indexes, appends the wiki and hub logs, runs the plugin's lint and any lint of your own, checks registry and freshness, and writes the round report with remaining gaps.
---

# Wiki steward

## Use when

The claim verifier has returned, under the [Research contract](../../references/research.md). The coordinator applies this role itself.

## Not for

Dispatch to a parallel worker, new research, or fixing content the lints flag in other wikis (list those for the owner).

## Inputs

The changed paths, the ledger, the verifier's summary and the target wiki.

## Work

1. Re-list `raw/` right before rebuilding indexes: other sessions write the same wiki.
2. Regenerate the derived `_index.md` files; never hand-edit them.
3. Append one line to the wiki's `log.md` and the hub log: date, job, sources kept and quarantined, articles changed.
4. Run the plugin's lint and any lint of your own. Fix what this round caused; list the rest.
5. A new wiki is registered at creation by absolute path. Set `verified` dates only for claims the verifier checked.

## Output

The round report: angles run, sources kept, quarantined and unreachable, articles created and updated, verification counts, disputes, lint result and remaining gaps as a numbered list.

## Acceptance

Both lints pass, or every failure is listed with whether this round caused it.

## Return

The report goes to the owner.
