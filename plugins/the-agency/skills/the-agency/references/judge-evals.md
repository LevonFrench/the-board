# Judge evals

A judge is a reviewer. Like any reviewer it can miss a bug, or block clean work for no good reason. This set measures both, so a change to a judge is tested instead of trusted.

The cases live in `evals/judge/`. Each one is small. `scripts/judge_eval.py` lists them, briefs them and scores the verdicts. It never calls a model: running the judges costs tokens, so the coordinator decides when.

## What a case holds

```
evals/judge/<case-id>/
  candidate/   the files the judge reads
  rubric.md    criteria in the `- name: what to check` shape judge_panel.py parses
  case.json    id, kind, origin, expect
```

- `kind` is `bug` (a past incident with the defect still in) or `clean` (known-good work, often the fix).
- `origin` says where the incident came from: a run folder, a commit, a round.
- `expect` holds `pass` (true or false), `max_score` for a bug or `min_score` for clean work, and `must_block`. A bug must raise at least one blocking item. Clean work must raise none.

A judge passes a candidate when its score reaches the pass score (6 by default) and it lists no blocking item. The judge never sees this number, the kind or the expectation.

## What the score reports

- **missed bugs**: a bug case the judge scored high, passed, or did not block.
- **false blocks**: a clean case that got a blocking item. This is the noise count.
- **score gap**: the mean clean score minus the mean bug score. A wider gap means the judge tells good from bad.
- **missing verdicts**: cases with no verdict file. A missing verdict counts as a miss.

## Add a case after a real incident

Add a bug case only when an engineer confirmed the defect and you know where it lived.

1. Make a folder under `evals/judge/` named for the defect, for example `raw-note-schema-bug`.
2. Copy the smallest version of the candidate that still shows the defect into `candidate/`. Keep file names as they were when the defect depends on them.
3. Write `rubric.md` as the real review would have had it. Do not name the defect in the rubric. A rubric that says "check for X" is a hint, not a test.
4. Fill in `case.json`: `kind` `bug`, the `origin` (run folder, commit or round), and `expect` with `pass` false, a `max_score` of 5 and `must_block` true.
5. Add the fix as a clean case with the same rubric: `kind` `clean`, `pass` true, `min_score` 7, `must_block` false.
6. Add clean cases that have no incident behind them too. Without them you cannot count noise.

Keep file text free of words like "bug", "fixed" or "wrong" inside the candidate. Folder names are hidden from the judge (see below), file content is not.

## Run a calibration

1. `python scripts/judge_eval.py list` shows the cases.
2. For each case, `python scripts/judge_eval.py brief <case-id>` prints the brief. It copies the files to a neutral temp folder named by hash, so no path shows the case id or kind. Pass `--stage <folder>` to keep the copy where you choose.
3. Give the brief to the judge: the `agency-loop-judge` agent, or Codex read-only. Give it nothing else.
4. Save each reply as `<case-id>.json` in one verdicts folder. A blocking item may be a string or an object with an `item` key.
5. `python scripts/judge_eval.py score <verdicts-folder>` prints JSON per case and totals. Exit 0 means every case met its expectation, 1 means a miss, 2 means bad usage.
6. Keep the verdicts folder next to the change you are testing, so the score can be compared later.

Read `bugs_blocked`, `bugs_unblocked` and `false_blocks` first. They count what a real round would have done, since a blocking item fails a round at any score. `missed_bugs` and `clean_misses` also apply each case's score bounds, which are stricter. A judge that blocks a bug but scores it 7 still stops the round, but its score is a poor signal on its own.

Stage each case in a folder with a random name. A folder named after the case puts words like `bug` or `fixed` into every path the judge reads. When a judge's miss turns out to be a fault in the case, fix the case on its merits, then rerun that case for every judge, not only the one that missed.


## When to rerun

Rerun the whole set after any change to a judge's prompt, agent card, tools or model, and after a change to the verdict schema or `judge_panel.py`'s brief. Compare the totals with the last run. A new miss or a new false block means the change made the judge worse. Do not ship it until that is understood.

The set is a sample, not proof. A judge that passes it can still miss a new kind of bug. Add a case each time one gets through.
