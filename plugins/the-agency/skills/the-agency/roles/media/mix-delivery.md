---
name: media-mix-delivery
description: Own cut assembly, premix, per-file finishing of packs and VO lines, mux, loudness to the job's target and the final probe, working on CPU.
---

# Mix and delivery

## Use when

Shots need assembling from an edit list, a pack or VO lines need per-file finishing, or stems and a locked picture are ready for the final file. Load the [Media contract](../../references/media.md) first, then the craft file of the team the job belongs to.

## Not for

Choosing takes, placing cues, layering or editing music (sound editor, music mixer, arranger), GPU work (render operator), judging the result (audio reviewer), or setting `approved`.

## Inputs

Stems on named buses (dialogue, music, foley, effects, ambience), the shot planner's edit list and clips, or finished per-file takes for a pack, the VO guide file, the locked picture and its hash, the job record with authority, clock, sample rate and loudness target, and each upstream job record.

## Work

1. Check the stems share a start sample, sample count and mix rate. Return any that do not to the role that made them, with the numbers.
2. Read the loudness target, authority and clock from the job record. If one is missing, stop and ask the parent. Do not pick a target.
3. Premix on CPU, at low priority, between GPU jobs. Change gain and bus balance only, and duck music and effects under dialogue with a sidechain compressor keyed from the dialogue bus, settings recorded. Report dialogue against the other buses over dialogue spans; the owner judges intelligibility. Never rewrite the authority's audio: no stretch, speed or trim. A supplied master keeps its level unless the brief says otherwise.
4. Return a stem that fails a creative check, such as a masked line or a wrong take, with the moment and the number. Do not fix it here.
5. Assemble the cut from the edit list, build the VO guide file and place lines on the dialogue bus with room tone under them. Conform picture by the video craft file's encode spec: frame rate as a fraction and frame count must match the locked cut. A changed picture hash voids the work; stop and report.
6. Measure programme loudness, set the target with one static gain (`volume=` from the measurement), then re-measure true peak. Use `loudnorm` only with all four measured values and `linear=true`, confirm its output says linear, and set the output rate: when it cannot stay linear it silently goes dynamic, compresses and writes 192 kHz. If the gain would break the ceiling, stop and report; a limiter is the owner's choice. A loudnorm export has come out 960 samples short: pad or trim to the exact sample count, then count.
7. Do not cap output with `-frames:v` when the filter chain expands the stream. Trim by duration or sample count and verify.
8. Mux the master audio once, into one audio stream. For PCM, sample count and hash equal the master. For AAC, duration matches the picture within one AAC frame (1024 samples), and loudness and true peak are measured on the decoded deliverable, leaving 0.5 to 1 dB of true-peak margin. Record the master's sha256. Check no promotion or re-mux step stripped audio.
9. For a pack or VO lines, work per file instead: clean head and tail, level, format and names from the brief, with no shared sample count.
10. Run `python scripts/media_check.py probe` or `audio`, then `job`. Run a full decode.

## Output

The final file, the updated job record at `validated` at most, and a sheet for the owner: file, time, what to listen or watch for, and any failing number beside it.

## Acceptance

Sample counts, stream counts, loudness and true peak are inside the job's target, or each miss is listed. The final file exists and its hash is in the record.

## Return

To the parent under the [work contract](../../references/work-contract.md), `ready-for-integration` with the probe output and the sheet. Only the owner approves.
