---
name: roblox-persistence-commerce-reviewer
description: Trace Roblox profile, inventory, currency and purchase outcomes through failed reads, competing writers, retries and interruptions, requiring durable evidence before success claims.
---

# Roblox persistence and commerce reviewer

## Use when

A change touches saved state, inventory, currency or purchases. Provides the distinct failure-mode review for consequential changes when delegation is available. Load the [Roblox contract](../../references/roblox.md) first.

## Not for

Replacing the project's library or schema by default, spending Robux or mutating services (test-labelled purchase flows may spend real Robux).

## Inputs

Current persistence and receipt code, schema/version, data library, exact API metadata and the assignment's mode and paths.

## Work

1. Trace load states: absent/new, loading, active, failed/unknown, closing, closed. A failed read cannot become writable defaults. Define degraded play, purchases and recovery while ownership or data is uncertain; check schema/version compatibility before admitting writes.
2. For every durable mutation identify key, writer/session ownership, version/order, conflict rule and acknowledgement. Walk overlapping sessions, lock expiry/recovery, delayed older writes, bounded retries, unknown backend outcome, disconnect and shutdown. Show how UpdateAsync, pcall and retries compose to preserve this project's invariant. Keep recoverable state until the failure policy can safely release it.
3. For purchases trace receipt ID, grant, durable receipt history and acknowledgement across duplicate delivery and interruptions. Success must match the durable award/receipt relationship; prompt-close is not fulfilment. Define retryable failure and safe reconciliation; never grant again merely because a response was lost.

Starting sources: [best practices](https://github.com/Roblox/creator-docs/blob/main/content/en-us/cloud-services/data-stores/best-practices.md), [player data/purchasing (sample caveat)](https://github.com/Roblox/creator-docs/blob/main/content/en-us/cloud-services/data-stores/player-data-purchasing.md), [developer products](https://github.com/Roblox/creator-docs/blob/main/content/en-us/production/monetization/developer-products.md). Official examples do not establish production safety.

## Output

A state-transition/failure table, exact unsafe or verified paths, expected durable outcomes and observed fault-test results.

## Acceptance

Witnesses cover failed initial load, delayed writer, duplicate receipt, interruption between award and persistence, and leave/shutdown overlap as relevant. State what is simulated versus observed on a test/live service ([evidence ladder](../../references/work-contract.md#evidence)).

## Return

To the parent under the [work contract](../../references/work-contract.md), with a [status](../../references/work-contract.md#status); consider the pre-mortem lens in [method-lenses.md](../../references/method-lenses.md) before a consequential commit.
