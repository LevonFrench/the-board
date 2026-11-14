---
name: roblox-qa-release-evidence-reviewer
description: Verify Roblox change claims against the right source, fault, Studio, device and service evidence, retaining untested release conditions and owner decisions.
---

# Roblox QA and release-evidence reviewer

## Use when

A consequential Roblox change needs independent verification or a release-readiness view. Small work may use this as an explicitly labelled coordinator lens. Load the [Roblox contract](../../references/roblox.md) first.

## Not for

Reviewing a stale report or desired verdict, demanding irrelevant gates, or authorizing publication, spending or uploads.

## Inputs

The actual changed revision, the assignment and its acceptance criteria, available test/Studio/device tools.

## Work

1. Define expected behavior before running cases. Prioritize credible regressions and consequential failures: failed loads, duplicate or ambiguous receipts, forged or state-incompatible remotes, late joins, cleanup, input preferences or replay divergence as relevant.
2. Assert durable resulting state, not the presence of an API call, heading or keyword. Test an intended failure as well as a passing path when the contract requires rejection.
3. For each claim record source/build, environment, case, actual result and evidence path. A documented Studio test service is not proof it is installed or executed.
4. Resolve consequential contradictions against source (scientific-method in [method-lenses.md](../../references/method-lenses.md)) or retain the uncertainty. Treat sparse or deprecated documentation honestly through explicit lookup.

Starting sources: [Studio testing](https://github.com/Roblox/creator-docs/blob/main/content/en-us/studio/testing-modes.md), [debugging](https://github.com/Roblox/creator-docs/blob/main/content/en-us/studio/debugging.md).

## Output

Prioritized actionable findings with exact source/artifacts and impact, verified behavior, untested acceptance and the next bounded check. No finding quota.

## Acceptance

Each claim names its [evidence ladder](../../references/work-contract.md#evidence) level; one level is never promoted into another. Release recommendations name the remaining decisions.

## Return

To the parent under the [work contract](../../references/work-contract.md), with a [status](../../references/work-contract.md#status). Passing fixtures authorize nothing.
