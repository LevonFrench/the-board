---
name: media-music-mixer
description: Prepare music stems at a common gain for the shared mix, or master a standalone track to its stated target, and record every setting and measurement.
---

# Music mixer

## Use when

An assembled music draft needs stems for the shared mix, or it is the final deliverable and needs a master. Load the [Media contract](../../references/media.md) and the [Music craft](../../references/media/music.md) first.

## Not for

The final mix for picture, dialogue ducking, mux and delivery loudness of a piece with picture: the shared Mix and delivery role owns those, and there is no second mixer. Also not for measuring and listening sheets (Audio reviewer), arranging (arranger) or GPU work.

## Inputs

The draft and stems with hashes, the brief's destination, loudness target, true-peak ceiling, sample rate and bit depth, and whether the track is the final deliverable.

## Work

1. Measure each stem with `media_check.py audio`. Record integrated loudness, true peak and silence.
2. Do not normalise stems one by one. Separated stems keep one common gain so they still sum to the mix. For parts generated alone, set a starting balance by role, measure it and send the balance to the owner's ear. Check low-end clashes and mono sum with measurements, and list what needs an ear.
3. Write the chain as ffmpeg filter settings, or as a written checklist the owner applies in their own audio editor. Record every setting.
4. For stems: export them on the music bus with one shared start sample and sample count, gain set to leave headroom. Do not apply the picture loudness target.
5. For a standalone master only: bring the track to the brief's loudness and true-peak ceiling in 32-bit float. Resample once, in float, if the destination is 48 kHz. Reduce to 16 bit last with triangular dither if the destination is 16 bit, and record it. Measure true peak on the final file.
6. Re-measure with `audio` using `--lufs`, `--lufs-tol`, `--true-peak-max`, `--max-head-silence` and `--max-tail-silence` from the brief. Keep before and after numbers.
7. Update the job record: chain, outputs with sha256, evidence at level 2.

## Output

Stems at a common gain on the music bus, the master if the track is the final deliverable, chain settings, before and after measurements, and a list of what the owner must hear: balance, low end, pumping, static.

## Acceptance

`audio` passes against the brief's numbers, or each miss is listed with its value. Stems share start sample and sample count. `media_check.py job` accepts the record. No claim that the result sounds good.

## Return

To the parent under the [work contract](../../references/work-contract.md), `ready-for-integration` with the output paths and measurements. The Audio reviewer checks this work, not the mixer.
