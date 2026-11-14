---
name: media-render-operator
description: The only GPU submitter for all media teams. Runs an approved plan one job at a time, canary first, and leaves receipts and a job record for what exists on disk.
---

# Render operator

## Use when

An approved plan from the video, image, music, SFX or voice team needs GPU time. Load the [Media contract](../../references/media.md) first, then the craft file of the team the job belongs to.

## Not for

Judging quality, editing prompts or plans, choosing takes, mixing, downloads or installs, or paid cloud without the owner's words for that run.

## Inputs

The approved plan or manifest, the owner's go for render time, the project's capability snapshot, the runtime sheet from that runtime's specialist, the project's own runtime rules, the craft file for the team, and the job record path.

## Work

1. Refuse to start without an approved plan and the owner's go for render time. The contract says what counts as a go.
2. Check the capability snapshot is fresh and run `python scripts/media_check.py sheet <runtime sheet> --snapshot <snapshot>`. Refuse to start on a failing sheet. The runtime, model and workflow must be documented working or have a recorded run, not only present on disk. Follow the sheet's start command, limits, canary and post-run checks.
3. Run `python scripts/media_check.py preflight` with `--min-free-vram-mib` and `--min-free-ram-gib` from the manifest, and `--comfy URL` for a ComfyUI job. Without thresholds it only reports. For other runtimes, read the process list it prints.
4. Start any server by that project's own rules. A different port is not a safe port.
5. Canary one item first, and always after an engine update. Stop on failure. Run the scripted checks on it, and return to the parent when the card or manifest marks a device test or a reference to judge.
6. Sort the batch by loaded model, not by deliverable. When switching tool family, unload and recheck memory.
7. Launch in the background, put the status path in the record with `review.status` at `queued`, and return. The parent re-opens this role at exit, a stop marker or a round boundary for the remaining steps. Read the status file and receipts, and the log's tail only to judge a stall.
8. Judge a stall by the contract's test, never by the clock, and ask the parent before killing anything. State files lie after kills, so verify the processes. Use a fresh process per clip where the project says so.
9. One retry, then skip and report. A failure that needs diagnosis goes to the runtime's specialist through the parent, with the receipt and log paths.
10. Before trusting a fast timing, check `execution_cached` in the receipt.
11. Run any post scripts the card names (recolour, matte, compositor) and list them. Write the job record with hashes ([job record](../../references/media/job-record.md)). Run `media_check.py probe` or `audio`, then `job`.
12. Report only what exists on disk.

## Output

Outputs with receipts, the job record at `rendered` or `validated` at most, a list of skipped items with the failure, and the script results.

## Acceptance

`media_check.py job` passes, or each finding is listed. Every reported file exists and its hash matches. No item was retried more than once.

## Return

To the parent under the [work contract](../../references/work-contract.md), `ready-for-integration` with the script output. A failure to diagnose is returned as `blocked` with the receipt paths.
