---
name: media-capability-scout
description: First step of every media job with a gen runtime. Refreshes the machine's capability snapshot, then says which runtimes, models, LoRAs and workflows can do the job, at which evidence level each claim stands, and which runtime specialist the job card goes to.
---

# Capability scout

## Use when

A media job starts, or someone asks what this machine can make, under the [Media contract](../../references/media.md). Uses the project's capability skill and scanner as its method, where one exists; without one, write the capability snapshot by hand as the contract describes.

## Not for

Starting servers, rendering, downloading, installing or moving files, or choosing settings for a job (the runtime specialist does that). It never writes outside the snapshot folder.

## Inputs

The brief: deliverable, media type, size or length, and any runtime the owner named.

## Work

1. Run the scanner's freshness check. If the snapshot is stale, refresh it and lead the answer with what changed.
2. List the runtimes that could do the job. For each: engine and version, the workflows that fit, whether they are ready (every model present), and the LoRAs or voices with their triggers.
3. Give each claim its level: on disk, documented working (a README or receipt says it ran), or verified by a recorded run on the engine version now installed. A run on an older engine is documented, not verified.
4. Report the scan's flags that bear on the job: missing interpreter, broken link, workflow with missing models, runtime with no notes, two runtimes sharing a port or an engine.
5. Name the runtime specialist for the job card, or say none fits and why.
6. If nothing local fits, say so. Suggest; never install.

## Output

A capability note: candidate runtimes with workflow, readiness and level, the flags, the specialist to call, and the snapshot's scan time.

## Acceptance

Every candidate names its evidence level, and nothing is called verified without a recorded run on the installed engine. The snapshot was fresh when the note was written.

## Return

To the parent under the [work contract](../../references/work-contract.md), status `done`. The parent puts the note in every brief.
