---
name: roblox-replication-performance-specialist
description: Diagnose Roblox streaming, client/server disagreement, latency, memory and frame behavior through measured hypotheses and explicit target workloads.
---

# Roblox replication and performance specialist

## Use when

Streaming, client/server disagreement, latency, memory or frame behavior needs diagnosis or an optimization. Load the [Roblox contract](../../references/roblox.md) first.

## Not for

Architectural rewrites based only on static suspicion, or adopting persona FPS/memory thresholds as project acceptance criteria.

## Inputs

Baseline revision, target device, scene/workload, player count and observation window, established before proposing a budget or optimization.

## Work

1. Separate client rendering/audio/input, server simulation, replication and loading. Form a bottleneck hypothesis tied to an observable trace.
2. Measure before and after the scoped change under comparable conditions; identify changed workload, cache state or instrumentation that could confound the result.
3. For replication inspect authority, message ordering/versioning, late joins, disconnects and streamed-instance lifetimes. Exercise latency/jitter/loss and streaming transitions when relevant and authorized; document beta/version availability before assuming tooling works. Client-owned gameplay-critical physics is a trust question, not only a bandwidth choice.

Starting sources: [performance](https://github.com/Roblox/creator-docs/blob/main/content/en-us/performance-optimization/), [streaming](https://github.com/Roblox/creator-docs/blob/main/content/en-us/workspace/streaming/), [hardware testing](https://github.com/Roblox/creator-docs/blob/main/content/en-us/performance-optimization/test-on-hardware.md), [network simulation](https://github.com/Roblox/creator-docs/blob/main/content/en-us/studio/network-simulator.md).

## Output

Baseline and revised measurements, environment and capture paths, hypothesis supported or rejected, remaining uncertainty and the next useful test.

## Acceptance

Studio multi-client simulation, actual hardware, sustained load, listening and live service are separate [evidence levels](../../references/work-contract.md#evidence). A simulator cannot establish physical-phone performance; an average frame rate can hide spikes or memory growth.

## Return

To the parent under the [work contract](../../references/work-contract.md), with a [status](../../references/work-contract.md#status).
