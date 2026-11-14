---
name: delivery-contract
description: Turn a substantial change or uncertain project behavior into a concise specification, dependency-aware work packets and observable evidence under the existing Agency improvement loop.
---

# Delivery Contract

## Use when

A substantial change needs an executable handoff, or architecture/behavior uncertainty obstructs implementation. The existing implementation lead or Software Architect owns the contract; specialists own bounded slices.

## Not for

Simple tasks (keep the same fields in the current handoff, no extra files or agents), issue publication, automatic branch reset/merge/cleanup, or nested orchestration.

## Inputs

Applicable instructions, AGENCY.md, current source/checkout, the user's actual request, baseline revision or hashes, dirty paths, protected behavior and permitted writes. Existing KB/index queries only where they answer an uncertainty.

## Work

1. Separate unresolved **decisions** from executable **implementation**. A decision item ends with an evidence-backed choice, rationale and remaining uncertainty, never a claim of shipped behavior. Use existing conversation evidence before another interview. For a costly-to-undo choice apply reversibility, then pre-mortem ([method-lenses.md](../method-lenses.md)).
2. Write the smallest useful behavior specification: audience, trigger, expected result, exclusions, failure states, compatibility and public test boundary, with a one-line note on what each proposed boundary catches and what it misses; a glossary only for ambiguous terms. Each requirement has an owner and observable evidence, or an explicit exclusion.
3. Divide work by verifiable behavior and dependencies; start with at most three slices for an initial pilot. Mechanical refactors may use expand/transition/contract phases with one final integration check.
4. Execute authorized slices through the [improvement loop](../improvement-loop.md). Before starting reviewers, resolve the fixed point and confirm the diff is non-empty; with no spec, skip the spec review and say so. Review **spec compliance** separately from **standards compliance** and report them side by side, never as one ranking; for standards, search the project for every file that documents how its code should be written rather than checking a fixed name or two; use tests with independently expected outcomes where meaningful.

**Optional orientation map.** Ordinary source reads and an existing code index come first. Consider Understand Anything only when a prewritten onboarding/impact question needs a graph and setup is within the task. Preserve the assigned checkout; allowlist safe inputs; record coverage and anchors; distinguish static links, inferred relationships and unresolved dynamic edges. The graph describes one revision and replaces neither source nor the owner's KB. Recorded limitations.

## Output

The [delivery template](../../assets/workflows/delivery-contract.template.md) and one [work-item packet](../../assets/workflows/work-item.template.md) per assignment (stable ID, owner, dependency, allowed paths, fixed criterion, evidence artifact, attempt budget, return channel), linked to the existing backlog rather than duplicating it.

## Acceptance

The parent checks requirement coverage, unresolved decisions, current diffs and interacting slices. Evidence stays separated by [ladder level](../work-contract.md#evidence); missing evidence is a visible gap, not spec compliance.

## Return

To the parent under the [work contract](../work-contract.md) with a [status](../work-contract.md#status); review/plan mode returns proposed packets. Provenance: an Agency adaptation of selected Matt Pocock decision/spec/ticket/test/review methods (delivery assessment); it does not invoke the originals, which keep their human-only flags.
