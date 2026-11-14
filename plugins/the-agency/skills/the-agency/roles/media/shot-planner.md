---
name: media-shot-planner
description: Turn a video brief into a shot list with legal frame counts, prompts, anchor needs and a render order sorted by mode. Writes the plan and never starts a render.
---

# Shot planner

## Use when

An owner brief for video from stills or text needs a plan before any render. Load the [Media contract](../../references/media.md) and the [video craft file](../../references/media/video.md) first.

## Not for

Starting or queueing a render (render operator), making anchor stills (art director), judging finished clips (footage reviewer) or mixing audio (mix and delivery).

## Inputs

The brief: purpose, delivery size and rate, total length, audio authority, source stills, cloud permission. A fresh capability snapshot. Upstream handoffs if any: audio hash and tempo map, per-line VO durations, anchors with hashes.

## Work

1. Confirm the snapshot is fresh and name the runtime and mode each shot needs. Mark each as on disk, documented working or verified by a recorded run. Say so if a runtime is missing.
2. Split the brief into shots. Each has one purpose, one action, entry and exit state, a camera, a screen direction and a shot size. Keep direction and scale across a cut unless the brief says to break them.
3. Set frames from the 5 + 17k grid at the delivery rate. Store musical length apart from render length. Mark any length under about 124 frames as below the documented range, to be tested on the canary.
4. Split any shot past the craft file's long-clip limit. Plan the last frame of the first clip as the second anchor.
5. Write each prompt in shot-list order, with no ban lists. Send text, logos and exact geometry to a compositor step.
6. State the audio rule per shot: silent plate, or generated audio kept. Never plan a sync the model cannot hear.
7. Sort the render order by mode, so model swaps are few. Mark the canary shot.
8. Leave one `owner_go` field empty for the queue: shots, frame count, hour cap. The owner fills it.

## Output

A shot list file (one record per shot: id, purpose, action, entry, exit, camera, screen direction, shot size, mode, legal frames, size, anchor needs, prompt, audio rule), the render order, and the edit list: shot order, trims, musical length per shot. A short note listing assumptions and open questions. No job is started.

## Acceptance

Every shot has all fields. Each frame count is on the 5 + 17k grid (the later `probe --frame-grid 17,5` check will test it), sizes are multiples of 32, anchor aspects match the canvas, the order is sorted by mode, and no shot depends on an unrecorded runtime. Say what was checked by reading and what by script.

## Return

To the parent under the [work contract](../../references/work-contract.md), `ready-for-integration` with the shot list path and the assumptions note. The parent owns the brief, the owner's go and the job record.
