---
name: media-spotter
description: Turn a locked cut, or a game sound list, into a cue sheet with a source choice and reason per cue, plus the manifest the Render operator runs.
---

# Spotter

## Use when

Picture is locked and effects or foley are wanted, or a game pack needs a cue list. Load the [Media contract](../../references/media.md) and the [SFX craft](../../references/media/sfx.md) first.

## Not for

Running a render (Render operator), picking or placing takes (sound editor), measuring (Audio reviewer), speech (voice team), final mix (Mix and delivery), or work on unlocked picture.

## Inputs

The locked cut: fps as a fraction, frame count, picture hash, edit list. Frame strips or clips, with `media_check.py probe` output saying which carry an audio stream. For a game pack, the sound list. The brief's audio policy and delivery destination.

## Work

1. Confirm picture lock and record the picture hash. Any later picture change voids the moved cues. For a list-only pack, skip the lock, hash, frame and sync fields.
2. Read the frame strips. Mark cues whose motion, weight or material frames cannot show, for the owner to watch. For a hard-sync cue, extract every frame within 6 frames of the candidate and record the contact frame; strips are for loose cues.
3. Write one row per cue: frame or timecode, subject, sound, class, duration, hard or loose sync, source, reason, variations, loop or one-shot.
4. Choose the source for each cue with the rule in the SFX craft file: H3 audio only for cues inside an unretimed H3 clip that must lock to its own picture, Stable Audio for the rest. Say if the H3 glue layer is wanted.
5. Send speech cues to the voice team. Leave none on the sheet.
6. Write the render manifest: 4 to 8 takes per cue, seeds, fixed batch size, the centered mono steer for one-shots, long beds. State the sync tolerance in frames from the fps.
7. Estimate the curation load, because listening is the cost. Propose a cap on takes per cue.
8. Write the draft job record with the picture hash under needs. Do not start a render.

## Output

The cue sheet, the manifest, the curation estimate and the draft job record.

## Acceptance

Every cue has every field that applies. Every frame is inside the frame count. Every source choice has a reason. No speech cue remains. The H3 clips used have an audio stream confirmed by `probe`. `media_check.py job` accepts the draft record.

## Return

To the parent under the [work contract](../../references/work-contract.md), `ready-for-integration` with the cue sheet and manifest paths. The parent hands the manifest to the Render operator.
