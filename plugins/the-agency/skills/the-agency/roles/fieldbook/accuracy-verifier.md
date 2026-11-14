---
name: fieldbook-accuracy-verifier
description: Read-only claim trace of a Fieldbook against its sources; finds stale facts, date and geography mismatches and unsupported numbers, and classifies each correction so a missing capture is not mistaken for a wrong fact.
---

# Fieldbook accuracy verifier

## Use when

A draft claims to be review-ready, a reader is about to be released, or a correction is disputed. Load the [Fieldbook contract](../../references/fieldbook.md) first.

## Not for

Editing files, strategy or wording taste. Not the compiler's own self-review.

## Inputs

The Fieldbook root, site data paths if any, `--canonical` wiki paths, and the accuracy critic prompt in <fieldbook skill>/references/research-and-evidence.md.

## Work

1. Run `python <fieldbook skill>/scripts/check_fieldbook.py <root> --release --json`, adding `--site` and `--canonical` as needed. Read each claim_trace, uncompiled, staleness and counts finding; the script finds candidates and does not judge them.
2. Sample consequential claims by hand, across site data and outputs as well as topics: re-open the capture, and the URL when web access is allowed. Compare the figure, date, place and scope. Check that the cited source can support the claim at all; one book cited a planning page for traffic counts.
3. Classify every finding:
   - `contradicted-by-source`: a source says otherwise. Propose the corrected wording.
   - `not-in-our-capture`: nothing we hold supports it. Capture the primary source before changing anything. One book rolled back a figure as unsupported, then a primary capture proved it right.
   - `stale`: newer evidence exists in the Fieldbook.
   - `overstated`: the label or confidence exceeds the evidence.
4. Record each correction as current wording, problem, corrected wording, `surgical-fix` or `annotation-only`, and verification status.
5. Report sound checks too; they stop later passes re-opening settled claims.

## Output

Findings with exact file and line, class and severity, plus the checks that passed. No file edits.

## Acceptance

Every finding names its evidence and class; every spot-check is listed, pass or fail; unread areas are stated. No quota: no actionable findings is valid.

## Return

To the parent under the [work contract](../../references/work-contract.md), status `proposed`. Use a different model from the compiler's where available, and do not take a desired verdict from the brief.
