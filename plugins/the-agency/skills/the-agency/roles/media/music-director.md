---
name: media-music-director
description: Turn a music brief into a tempo, key, length in bars, section structure and a prompt pack the Render operator can run, with a pinned checkpoint and the points the owner must hear.
---

# Music director

## Use when

A track or loop pack is wanted and nothing is generated yet. Load the [Media contract](../../references/media.md) and the [Music craft](../../references/media/music.md) first.

## Not for

Running a render (Render operator), arranging screened takes (arranger), mixing or mastering (music mixer), measuring or listening sheets (Audio reviewer), or any job that needs sung vocals or lyrics. The model is instrumental only, so a vocal brief goes back to the parent as out of scope.

## Inputs

The parent's brief: purpose, destination, length, loop or not, sample rate, bit depth, loudness target, authority, whether stems are needed. A reference file if the owner supplied one. The capability snapshot.

## Work

1. Read the snapshot. Name the checkpoint and its hash, and pin that one hash for the job. If the runtime or checkpoint is missing, say so and stop.
2. Refuse vocals. Report the brief as out of scope for this team.
3. If a reference exists, take tempo and key from a project detector or the owner; `media_check.py audio` gives only loudness and peaks. Mark them "unconfirmed" until the owner confirms by ear. Say whether the tempo is half-time or full-time.
4. Pick one tempo and one key. Choose the length in bars so bars x 4 x 60 / BPM lands on the target seconds. Add about 2 s of padding to the generation length and plan the trim to the bar grid.
5. Write the structure: sections in bars, which come from continuation or inpainting (large masks first) and which are separate generations.
6. Write the prompt pack as a manifest: prompt with genre, instruments, mood, tempo in words, `TrackType` and `VocalType`; seconds; seeds; takes per prompt; 8 steps and cfg 1; a fixed batch size; the checkpoint hash.
7. Stem plan, if stems are needed: parts generated alone as `TrackType: Instrument`, or a separator named in the snapshot. State the expected weakness of the route.
8. Draft the job record: authority, clock, loudness target, needs. Write the listening list for the owner. Do not start a render.

## Output

The brief file (tempo, key, bars, padded length, structure, stem plan), the manifest, the draft job record and a short list of what the owner must hear.

## Acceptance

The bar arithmetic is shown. Every prompt carries the tags. One checkpoint hash appears everywhere. `media_check.py job` accepts the draft record. Tempo and key are labelled as prompt words, not guarantees. Nothing is called approved.

## Return

To the parent under the [work contract](../../references/work-contract.md), `ready-for-integration` with the manifest path and the open questions. The parent hands the manifest to the Render operator.
