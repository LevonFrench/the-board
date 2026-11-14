---
name: mediakit-curator
description: Closing step of an Agency run. Picks the screenshots, logos, renders, video and audio the run already made that could show or promote the project, looks at each one, keeps secrets and personal data out, and copies the keepers into the project's .mediakit folder with a manifest entry. Never captures, renders, moves or edits anything.
---

# Media kit curator

## Use when

An Agency run is closing and it made or touched visual or audio files, under the [media kit contract](../../references/mediakit.md).

## Not for

Making new media of any kind, editing or re-encoding files, judging rights or licences, or projects the owner does not own.

## Inputs

The project's absolute path, the run's folder and record, any output folders the run wrote, the run's start time, and the project's existing `.mediakit/manifest.json`.

## Work

1. List the candidates: `python -B <skill>/scripts/mediakit.py candidates <project> --path <run folder> [--path <output folder>] --record <run record> --since <run start>`. With no run folder, give the folders the run wrote.
2. Choose at most 30 to look at: every `referenced` one first, then contact sheets, finals and the newest of each folder in `folders`. Look at each chosen candidate with Read (images directly; for video and audio use the file's name, its run record and any stills or contact sheet the run made). Sort each into keep, skip, or hold for the owner, using the contract's "What goes in" and "What stays out". Several of the same moment: keep the best one.
3. Read the manifest. A keeper that shows the same screen as a current item supersedes it.
4. Add each keeper: `mediakit.py add <project> <file> --kind <kind> --caption "<one line a reader could use>" --shows "<what is on screen, plainly>" --run <run record> [--source-note ...] [--supersedes <id>]`. Write the caption about the project, not the run, for example "Combat against the night-market boss", not "QA round 2 capture".
5. Run `mediakit.py check <project>` and fix what it names.

## Output

The items added (id, kind, caption), the items superseded, the files held for the owner (path and reason), the files skipped (count and the main reason), and the check JSON.

## Acceptance

`mediakit.py check` passes. Every added item was looked at. Nothing that shows a key, token, account page, personal data or a private path is in the kit. No original file was moved or changed.

## Return

To the parent under the [work contract](../../references/work-contract.md), status `ready-for-integration`, in the final message. The parent reports one line and commits the kit with the run's other changes.
