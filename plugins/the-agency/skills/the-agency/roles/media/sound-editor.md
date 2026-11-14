---
name: media-sound-editor
description: Pick, conform, place and layer rendered effect and foley takes against the cue sheet, and deliver stems on named buses for the shared mix.
---

# Sound editor

## Use when

Takes exist and a cue sheet is approved. Load the [Media contract](../../references/media.md) and the [SFX craft](../../references/media/sfx.md) first.

## Not for

The final mix for picture, ducking under dialogue, mux and delivery loudness (Mix and delivery owns them; there is no second mixer), spotting (spotter), generation (Render operator), measuring and listening sheets (Audio reviewer).

## Inputs

The cue sheet, the takes with provenance and sha256, take scores from scripts, `media_check.py audio` reports, for picture work the picture hash and clock, the owner's picks from earlier listening.

## Work

1. Check take and picture hashes against the record. A changed hash voids the placement.
2. Choose the takes from the owner's picks. Where there are none, take the top script score per cue, mark it unheard, and put the next two on the owner's sheet. An overnight run does not wait for this.
3. Conform: trim to onset (-30 dB envelope, 4 ms pre-roll) with fades, high-pass at 25 to 30 Hz, equal-power crossfade for loops of unrelated sound, equal-gain for joins of the same material. Do the mono downmix here when a cue needs it.
4. Place each cue at its frame, converted to samples at the stated rate. Write the placement table: cue, take hash, start sample, gain.
5. Layer: one bed, 0 to 2 mid layers, accents on top. Keep layers recoverable. Put H3 glue audio at about 0.35 under hard hits only if the sheet says so. Cues are dry: list each scene's room, shot scale and cues for the owner to treat, and report the stems as dry.
6. Export stems on named buses (foley, effects, ambience), all with the same start sample, sample count and mix rate as the cut. A pack with no picture hands per-file takes to Mix and delivery instead.
7. Run `media_check.py audio` on each stem, and `job` on the record. List every cue that needs an ear: sync feel, hidden speech or melody in a full untrimmed take, loop seams, static, mono and phone-speaker playback.

## Output

Stems on named buses, the placement table, the layer plan, the list for the owner's ear and the updated job record.

## Acceptance

All stems match in start sample and sample count, with no clipping. Each placed cue has a provenance row and matching sha256. Hard-sync onsets sit within the sheet's frame tolerance by script, or the miss is listed. Loops pass the craft file's seam checks where a project script exists; otherwise each seam is on the ear list. Nothing is marked heard or approved.

## Return

To the parent under the [work contract](../../references/work-contract.md), `ready-for-integration` with the stem paths, the placement table and the ear list. Mix and delivery takes the stems next.
