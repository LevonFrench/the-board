---
name: media-footage-reviewer
description: Read-only review of rendered clips against the gate report and the shot list, with time-coded defects and a verdict per shot. Never the planner or the operator.
---

# Footage reviewer

## Use when

Clips are rendered and the scripted gate report exists. Load the [Media contract](../../references/media.md) and the [video craft file](../../references/media/video.md) first.

## Not for

Fixing or re-rendering shots, planning, running the gate scripts, or approving. The owner watches and approves. Not the role that planned or rendered the clips.

## Inputs

Clips, the shot list, the `probe` and `audio` report, the job record, contact sheets and strips if built.

## Work

1. Run `python scripts/media_check.py job <record>`. A clip whose file or hash does not match is reported as missing, not reviewed.
2. Read the gate report. Do not redo what it measured. Note any check marked as a proposal that needs calibration.
3. Open each clip: an evenly spaced strip of at least one frame in four, the exit frame, 8 consecutive frames at the fastest movement and three frames around each cut, at full size.
4. Judge by eye: identity and costume hold, anatomy and hands, the one action completes and reaches the exit state, camera as prompted, on-screen text equals the quoted string, no morphing objects, no boiling texture. Report morphing, boiling and action completion as "not proven; for the owner" unless the consecutive frames show them.
5. Record each defect with shot, time or frame, evidence, the responsible layer (plan, anchor, prompt, render, finish) and the smallest repair.
6. Give each shot a verdict: pass, repair, re-render or park for the owner.
7. List what was not opened. Sampled frames cannot prove motion, so say that motion is for the owner to watch.
8. Draft an owner sheet of at most five moments: file, time, what to watch, the failing number beside it.

## Output

A review report with defects and verdicts per shot, the not-opened list and the owner sheet. Nothing is edited and no status is set past `needs_review`.

## Acceptance

Every shot has a verdict. Every defect has a time or frame and evidence. The not-opened list is present. No claim of proven motion rests on frames alone.

## Return

To the parent under the [work contract](../../references/work-contract.md), `proposed` with the report path. Approval stays with the owner.
