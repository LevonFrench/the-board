---
name: fieldbook-release-steward
description: Own the Fieldbook jobs that otherwise have no owner; reconcile against newer source records, regenerate counts, keep status and editorial records true, and package and validate a reader before any handoff.
---

# Fieldbook release steward

## Use when

Before any handoff, release or ZIP; at the start of a refresh; or whenever a Fieldbook says what is current. Load the [Fieldbook contract](../../references/fieldbook.md) first.

## Not for

Publishing or deploying without the owner's words for that act. New research or rewriting conclusions.

## Inputs

The Fieldbook root, its source roots, <fieldbook skill>/references/validation-and-publishing.md and any owner packaging request.

## Work

1. **Reconcile before stating current status.** Compare each source root's newest dated record with topic `updated` dates. One Fieldbook stopped on 2026-08-25 and still stated its current authority unchanged two months and thirteen handoffs later. Add a reconcile item to `refresh-backlog.md`, set `reader.newest_source` so the reader shows it, and do not call it current until it is resolved.
2. Run `check_fieldbook.py`. Generate counts by script; handoffs link to the index and do not restate numbers. One book had six places disagreeing.
3. Keep one truth for status: `release_status`, topic status and commit language agree. Another book's note said the reader was never built after 17 pages were generated, and one book's docs said local-only beside a publish commit and hosting config. Hand the parent any publish or unpublish to record in the config and guidance.
4. Write `editorial-note.md`: scope, governing decision, corrections with their class, evidence limits, reader date and known display limits. Every script a note cites exists in the repo.
5. Quarantine: superseded pages move to a listed legacy folder with a banner; shared assets keep one copy with source path and hash.
6. Package only when asked: build a ZIP from a manifest, including the Markdown its pages link to, extract it to an empty folder and run the checks there. No secrets, source roots or private media.

## Output

Reconcile list, check output, updated editorial record, and the package with its receipt when requested.

## Acceptance

`check_fieldbook.py --release` has no errors, or each is listed for the owner with why it remains. The reader's date and status are true. An extracted package passes the same checks.

## Return

To the parent under the [work contract](../../references/work-contract.md). A release decision stays the owner's; report `ready-for-integration`, never `verified`.
