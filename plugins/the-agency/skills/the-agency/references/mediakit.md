# Media kit

Every project keeps a media kit at `<project>/.mediakit`: the screenshots, logos, renders, video and audio that could show or promote the project. It fills up as a side effect of Agency runs. The [media kit curator](../roles/general/mediakit-curator.md) runs once when a run closes, picks from what the run already made, and copies the keepers in.

## When it runs

At the close of an Agency run, after the work is verified and before the final report, when the run made or touched visual or audio files: QA and review screenshots, design references the project owns, Fieldbook captures of the project itself, renders and media from the Media division, before-and-after images in a run record, or a logo or icon file the run added or changed. A run with nothing visual skips it and says so in one line. It is one pass, not a loop. Projects the owner does not own, such as third-party checkouts, vendored code and wikis, get no kit.

## What goes in

Only what the run already made. The curator never renders, records, captures or starts a GPU job for the kit. A kit item is something the owner would show someone:
- the project working: a real screen, a finished render, a clip of play or use;
- its identity: logos, icons, key art;
- progress worth showing: a clear before-and-after pair.

Not debug noise: half-loaded screens, error dialogs, test patterns, annotated diagnostic diagrams (lines, labels and "wrong" markers over the work), near-identical frames of one moment, or thumbnails of something already in the kit. A caption says only what the image shows: a diagnosis is not a before-and-after. When several captures show the same thing, keep the best one. When a newer capture shows a screen already in the kit, it supersedes the older item (`--supersedes`); the older file stays and is marked.

## What stays out

The curator looks at every file before adding it. These never go into the kit:
- anything that shows a key, token, password, account or billing page, or an email address or other personal data;
- a local path or machine name the owner would not publish, or a private chat or document;
- a person who is not the owner.

A doubtful file goes on the owner's list in the return, not into the kit. Third-party content in frame (another game's footage, a font, a stock image, a model output under another party's terms) is recorded in `--source-note` so whoever reuses it knows. The curator does not judge its rights.

## Layout

```
<project>/.mediakit/
  manifest.json      one entry per item: id, file, kind, caption, shows, source, run, commit, added, bytes, sha256, in_git, and supersedes / superseded_by
  .gitignore         keeps video/ out of git
  screenshots/  logos/  renders/  video/  audio/  other/
```

Files are named `<date>-<caption slug>.<ext>`. Originals are never moved or edited. Images, audio and the manifest are committed with the project's other changes when the run commits. Video stays out of git, and the manifest still lists it by hash, so a missing or changed video is caught.

## Commands

```
python -B <skill>/scripts/mediakit.py candidates <project> --path <run folder> [--path <output folder>] [--since <run start>]
python -B <skill>/scripts/mediakit.py add <project> <file> --kind screenshot|logo|render|video|audio|other --caption "<one line>" --shows "<what is on screen>" --run <run record> [--source-note "<...>"] [--supersedes <id>]
python -B <skill>/scripts/mediakit.py check <project>
```

`candidates` lists media files that are not already in the kit by hash, newest first, plus a count per folder. It skips `.git`, the kit, dependency folders and build output. Pass the run's record or summary with `--record` (repeatable): the files it names come first, because a record cites the frames that mattered. Real runs make hundreds of review frames, so the curator looks at no more than 30 files per run: first the referenced ones, then contact sheets, finals and the newest of each folder. Everything not looked at is skipped, not held. `add` skips bytes that are already in the kit. `check` must pass before the run closes.

## Return

The curator returns its items added, superseded and held for the owner (each held item with its reason and path), and the `check` result. The parent puts one line in the run's report, for example "Media kit: 3 added, 1 superseded, 1 held for you", with the kit's full path.
