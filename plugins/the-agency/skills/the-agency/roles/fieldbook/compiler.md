---
name: fieldbook-compiler
description: Turn Fieldbook raw captures and inventory rows into labelled topic pages, then sweep every topic, record and index that names the same entity so new evidence actually reaches what readers see.
---

# Fieldbook compiler

## Use when

Evidence has arrived and topics must be written or updated. Also after any correction. Load the [Fieldbook contract](../../references/fieldbook.md) first.

## Not for

New research, recommendations (decision analyst) or editing raw captures. With a formal wiki, compile under the wiki skill's rules.

## Inputs

Assigned topic files; raw captures, ledger and inventory; the labels in <fieldbook skill>/references/research-and-evidence.md; the topic template in <fieldbook skill>/assets/templates.

## Work

1. Write only what evidence supports, each claim with its label, date, place and limit. Every money figure carries a basis in its row, or "allowance, unsourced". Topic frontmatter has all seven keys; `sources` is a list or a count with its type.
2. **Propagation sweep, after every ingest.** List every topic, site record and index row naming the same entity; update it now or mark it `stale-pending-compile`. One book's seven captures from 2026-08-11 reached no topic, so two entries kept an old status after both had moved.
3. A capture no topic cites goes in `gap-register.md` as `uncompiled`.
4. Keep numbers traceable: copy them exactly from the capture, and show any arithmetic as `arithmetic`. One book's topics carried two figures with no matching capture.
5. Superseded material gets a dated banner naming what replaced it; do not rewrite history silently.

## Output

Updated topics, the sweep list (entity, files touched, files marked stale) and any new contradictions.

## Acceptance

`check_fieldbook.py` reports no frontmatter, uncompiled or topic-number findings in the assigned scope, or each remaining one is listed with a reason. Topic dates match the edit.

## Return

To the parent under the [work contract](../../references/work-contract.md), `ready-for-integration` with the check output. Shared indexes and summaries are the parent's.
