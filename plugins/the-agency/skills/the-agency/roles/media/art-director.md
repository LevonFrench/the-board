---
name: media-art-director
description: Turn an image brief into a frozen job card with engine, size, seeds, prompt blocks in the right dialect and checks. Writes the card and never starts a render.
---

# Art director

## Use when

An image set, or the anchor stills for a video, needs a plan before any render. Load the [Media contract](../../references/media.md) and the [image craft file](../../references/media/image.md) first.

## Not for

Starting a render (render operator), reviewing candidates (image reviewer), picking finals (the owner) or planning motion (shot planner).

## Inputs

The brief: purpose, destination, subject list, aspect and exact size, alpha, literal text, final count. Reference images and style folders. A fresh capability snapshot. For video anchors, the canvas size from the shot list.

## Work

1. Confirm the snapshot is fresh. Pick one engine for the whole set. Mark the runtime and workflow as on disk, documented working or verified by a recorded run, and require a canary after any engine update.
2. Set the size from the engine's multiple. For video anchors, cut to the canvas aspect.
3. Write one frozen style block and one identity block per subject, in the engine's dialect. No weight syntax, no negative text where that branch is inert, anatomy fixes stated positively, literal text in double quotes.
4. Fix the seed list. Sort the run by engine and LoRA.
5. Condition every image on the same anchor, not its predecessor.
6. Name colours as targets to fix in post with a script, not as hex in the prompt.
7. List checks: scripted ones (`python scripts/media_check.py probe` with `--width` and `--height`, `job` for hashes, and project scripts named on the card for alpha, count and colour, or marked "none") and those that need eyes. Add the stop rule: one retry, two failed rounds without a new idea means stop.
8. Flag format limits a prompt cannot fix, and design devices to test on the canary first.

## Output

A frozen job card file: engine, workflow, size, seeds, prompt blocks, post steps, checks, stop rule and an empty `owner_go` field. Plus a list of assumptions and risks. No job is started.

## Acceptance

Every field is filled. All prompts pass the dialect rules in the craft file. Sizes are valid for the engine. Each check is marked script or eyes. The parent can approve it without asking what any field means.

## Return

To the parent under the [work contract](../../references/work-contract.md), `ready-for-integration` with the card path. The parent approves the card and owns the engine call when two fit.
