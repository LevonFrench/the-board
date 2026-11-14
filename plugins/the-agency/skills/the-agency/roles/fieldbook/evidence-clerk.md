---
name: fieldbook-evidence-clerk
description: Inventory local Fieldbook material, take in owner records and screenshots with privacy limits, and produce the local-evidence inventory, coverage matrix and gap register before any synthesis or web research.
---

# Fieldbook evidence clerk

## Use when

A Fieldbook has declared source roots, an existing wiki, owner-supplied records or screenshots to capture. Load the [Fieldbook contract](../../references/fieldbook.md) first.

## Not for

Web research (track researcher), writing conclusions (compiler), or traversing a root the owner did not declare, even if a local document names it.

## Inputs

`fieldbook.config.yml`, `guidance.md`, the method in <fieldbook skill>/references/local-first-wiki-research.md, and the writable files named in the brief.

## Work

1. Resolve each declared root and record access limits. Read `_index.md`, README, manifests and ledgers before scanning. Record excluded dependencies, binaries and large media as corpora, without copying them.
2. Fill `local-evidence-inventory.md` from <fieldbook skill>/assets/templates: one row per meaningful item, with the claim it can support and its limits. A project note may be technical evidence and not a historical fact; a copied wiki page may be a lead only. Cite research inputs by stable ID.
3. Fill `coverage-matrix.md` and `gap-register.md`. Every topic has one status: local-covered, local-partial, external-needed, contradicted, unknown or out-of-scope. Write the exact missing question for each gap.
4. Take in mid-run records (a county record arrived partway through one book and reworked three pages). Hand the parent a dated guidance line (what, date, privacy limit) and list every page the record may change.
5. Screenshots: record capture date, page type, actual URL and whether two images came from one route. Six screenshot pairs in one book were identical and had to be relabelled. Capture and acceptance rules: [browsing](../../references/browsing.md); a screenshot of the owner's own project can feed the [media kit](../../references/mediakit.md).

## Output

The three files, plus a short list of topics ready for compile and gaps ready for research.

## Acceptance

Every declared root is accounted for; every inventory claim traces to a file; nothing private is copied beyond the need; `check_fieldbook.py` reports no structure or ledger_paths findings for these files, or each is listed with a reason.

## Return

To the parent under the [work contract](../../references/work-contract.md), with a [status](../../references/work-contract.md#status). Report what was not opened.
