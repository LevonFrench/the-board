---
name: media-arranger
description: Turn the owner's chosen music takes into a section map, an edit list, continuation and inpaint requests, and an assembled draft on the bar grid.
---

# Arranger

## Use when

Takes exist and the owner has picked which ones to use. Load the [Media contract](../../references/media.md) and the [Music craft](../../references/media/music.md) first.

## Not for

Choosing takes by quality (the owner's ear does that), generating audio (Render operator), balancing or mastering (music mixer), measuring (Audio reviewer) or changing the director's tempo, key or checkpoint.

## Inputs

The director's brief and manifest, the owner's picks, takes with their provenance and sha256, `media_check.py audio` reports per take, the job record.

## Work

1. Check each take's hash against the record. A changed hash voids the work built on it.
2. Write the section map in bars and in samples at the stated rate, counted from one origin. Use each take's measured downbeat and tempo where known, marked unconfirmed: the prompt tempo is not a guarantee.
3. Where a section needs more material, write a request manifest for the Render operator: source take hash, continuation point or mask region, large masks first, prompt second. Never start the render.
4. Write the edit list: cuts on bar lines near measured downbeats, snapped to a zero crossing or transient; crossfade length and type at each join (equal-gain for the same material, equal-power for unrelated sound); trims to the grid after the padding. For a loop pack, trim each take and list each seam.
5. Assemble the draft on CPU with ffmpeg from the edit list. Do not balance or master it.
6. If stems are needed, request them by the director's route and note which parts were generated alone and which were separated. Say that stems from either route can drift or carry artifacts.
7. Run `media_check.py audio` on the draft. List every join as a moment for the owner to hear, with its time.
8. Update the job record: needs with hashes, outputs with sha256.

## Output

Section map, edit list, request manifests, the draft WAV, the join list for the owner's ear and the updated job record.

## Acceptance

The draft length equals the measured bar count in samples, and any drift from the stated tempo is reported. `audio` shows no clipping and no head or tail silence beyond the plan. Every join is on the list. The job record validates with `media_check.py job`. The report says the draft is unheard.

## Return

To the parent under the [work contract](../../references/work-contract.md), `ready-for-integration` with the draft path, the join list and any request manifests waiting for the Render operator.
