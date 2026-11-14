# Judge panel

Load with the [improvement loop](improvement-loop.md) when a loop's acceptance is a quality judgement (a page, a design, a document, a render plan, a skill) rather than a single pass/fail command. The loop ends when every judge on the panel reaches the target score, a programmatic check fails it, or a stop fires. It does not replace a test: where a command can decide, that command is the check and the judges score only what it cannot.

Script: [judge_panel.py](../scripts/judge_panel.py). It records rounds and says what happens next; it never dispatches a Claude worker, and the only thing it runs is the Codex judge. In the commands below `<skill>` is this skill's folder (the one holding `SKILL.md`) and `<run>` is the run folder.

## Set up the run

1. **Item and target.** One work item per run, with a target out of 10 the owner gave or accepted. Each small rise in the target costs far more rounds than the last, so start near 8 unless the owner asks for more. The target lives in `panel.json` only.
2. **Rubric.** A short markdown list of criteria in the owner's terms, one per line as `- <name>: <what to check>`, each one a thing a judge can check against the artifact. A name is one to four words; a bullet with more words before its colon is read as prose, not a criterion. `init` prints the criteria it found, so check that list before the first round. No weights, no target, no hint of the expected score. `record` rejects a verdict that leaves out a criterion named this way; a rubric in another shape is not checked, so the coordinator checks coverage by hand.
3. **Reference work.** Paths to comparable finished work, ideally better than the current candidate. Scores mean "against these"; without references judges drift high. Say so in the loop record when none exist.
4. **Run folder.** It holds the target, every score and every verdict, so judges must not read it. Put it outside the folder the judges read when you can (the coordinator's scratch folder, copied into the project's review folder after the loop ends); otherwise use the project's review convention, for example `docs/reviews/<date>-<item>/panel`. Either way the brief names the run folder as off limits. That line is the only guard: a read-only sandbox can still read it. Start it:

```text
python -B <skill>/scripts/judge_panel.py init <run> --item <id> --target 8 --rubric <rubric.md> --reference <path> --artifact <path>
```

`--judges` sets the panel, first judge then confirmers, comma separated; the default is `haiku,sonnet,codex`. `--depth quick|standard|deep` sets how many of them a pass needs (see [Review depth](#review-depth)); the default is `standard`. `--growth-limit` sets the size warning (default 2, a multiple of the round 1 size). `--max-rounds` defaults to 3, the improvement loop's first attempt plus two repairs; raise it only with the owner's say-so. `init` makes `verdicts/` and `verdict.schema.json` in the run folder. When the owner allows more rounds, record it, so the run folder shows who raised the budget:

```text
python -B <skill>/scripts/judge_panel.py extend <run> --rounds 4 --reason "<who allowed it and why>"
```

## Run a round

A round judges one candidate, named by a commit or by a hash of the files being judged: `python -B <skill>/scripts/judge_panel.py hash <file> <file> ...` prints one (list the files in the same order every round). A fix makes a new candidate and a new round. The script refuses a new round on the same candidate as the round before it, and refuses to open a round until the last one has failed.

When the candidate is a set of files, also record them each round, before briefing:

```text
python -B <skill>/scripts/judge_panel.py snapshot <run> --round N --candidate C <file> <file> ...
```

`snapshot` copies the text files into the run folder and records their total size and hashes. A round's snapshot is write-once: repeating it with the same files is a no-op, and any other change fails, so snapshot the change as the next round. The next round's brief uses the copies to show the judge what changed, and `status` uses the sizes to report growth. A candidate that is only a commit needs no snapshot; the brief then says no diff is available.

1. **Checks first.** Run every programmatic check that applies (tests, lint, a measured number) and record each one:

```text
python -B <skill>/scripts/judge_panel.py check <run> --round N --candidate C --name <check> --passed true|false --detail "<one line>"
```

   A failed check fails the round whatever the judges say. The script cannot know which checks exist, so when none applies, say so in the loop record.
2. **First judge.** Write the brief to a file and give that file to a fresh read-only worker on Claude Haiku 5.5 using the [Loop Judge](../roles/general/loop-judge.md) role. In Claude Code that worker is the `agency-loop-judge` subagent (Haiku, read-only tools); the Sonnet confirmer is the same subagent with its model set to Sonnet:

```text
python -B <skill>/scripts/judge_panel.py brief <run> --candidate C --judge haiku --round N > <brief file>
```

   The brief carries no target and no earlier score, and the worker gets nothing else from this run: no prior verdicts, no repair notes, no "it should pass now". From round 2, `--round N` adds two things as text: the diff since the previous round's candidate (capped in size) and the blocking items earlier rounds posted. The judge is told to review the changed parts first and not to repeat a posted finding; one that still stands is listed again with the prefix `still open:`. Pass `--round` for every brief; the `codex` command does it for you. Save its JSON reply as `<run>/verdicts/round-N-haiku.json` and record it:

```text
python -B <skill>/scripts/judge_panel.py record <run> --round N --candidate C --judge haiku --verdict <run>/verdicts/round-N-haiku.json
```

   If `record` rejects the verdict, send the judge the error once and record its corrected reply. A second rejection counts as no verdict: dispatch a fresh judge on the same candidate.
3. **Confirmers.** Only when the first judge reaches the target with no introduced blocking item does `status` ask for `confirm:sonnet`, then `confirm:codex`, as far as the depth asks (a quick run has no confirmer; a standard run stops at Sonnet). Dispatch the Sonnet judge like the first one. Run the Codex judge with:

```text
python -B <skill>/scripts/judge_panel.py codex <run> --round N --candidate C --project <folder>
```

   `<folder>` must hold the artifacts and references but not the run folder; the script refuses one that contains it, because Codex can read everything under `<folder>`. It runs `codex exec` in a read-only sandbox at medium effort and records the verdict; pass `--model` for a cheaper Codex model, `--effort` for another reasoning effort, `--timeout` in seconds (default 1800), `--judge` when the panel names its Codex judge differently, and `--codex-bin` when `codex` is not on PATH. The brief and reply are saved in `verdicts/`. On a timeout or error nothing is recorded. If the reply is rejected, run the same command once more (each run is a fresh judge); a second rejection counts as no verdict. When the loop runs inside Codex, set `--judges` so the first judge is Codex's cheapest worker and the other-provider confirmer is a Claude judge; dispatch each as a worker given the brief, and record its reply with `record`.
4. **Read the result.** `status <run>` prints JSON with `next`:

| next | Do |
|---|---|
| `judge:<name>` / `confirm:<name>` | Dispatch that judge on the same candidate |
| `repair` | Turn the judges' introduced blocking items and the criteria scored below the target into one repair assignment, then start a new round on the new candidate |
| `pass` | Every judge the depth asks for reached the target and none listed an introduced blocking item: the item's acceptance is met. An introduced blocking item fails the round at any score |
| `stop:no-progress` | Two failed rounds in a row with no score gain, or the same check failing in both (a round failed only by checks is compared by its checks). Stop and report the blocker with 2 to 3 options; go on only with a new hypothesis the owner accepts |
| `stop:budget` | The round budget is spent. Step back and reconsider the approach before asking for more rounds: more passes over the same plan have not worked. Report where it stands. When a round is both over budget and stuck, this one is reported |

Besides `next`, `status` prints `depth`, a `backlog` when judges posted pre-existing items (see below) and `size` when snapshots exist: bytes per round, `growth` against round 1 and a `warning` past the growth limit.

The panel score is the lowest score among the judges the depth asks for. `status` exits 0 only on `pass`, 1 for every other `next`, and 2 when the run folder or its `panel.json` is missing. `brief` and `hash` print and write nothing; `extend` writes `panel.json`; the other subcommands exit 0 when they wrote their record and 2 when they refused one.

## Rules that keep the scores honest

- Judges are read-only and fresh every round. A judge that saw an earlier round, the target or the repair notes is not a judge for this round.
- Never tell a judge the target, the previous score or what the coordinator hopes for. Scores rose when judges were told the target, and when they re-scored unchanged references.
- Every criterion score needs evidence: a file and line, a command and output, or a quotation. The script rejects a verdict with empty evidence but cannot tell whether the evidence is true, so the coordinator re-checks at least one citation per verdict before acting on it.
- Feed repairs from the verdicts' blocking items and evidence, not from the numbers. "Get to 9" is not feedback.
- Fix the class, not the line. Each blocking item names a `class`, the kind of defect. The fixer fixes every instance of that class in the candidate and rechecks, so the next round does not find the same defect on another line.
- Between rounds the fixer acts only on introduced blocking items and on criteria scored below the target. Never on nits, preferences or summary remarks: they bloat the change and give the next judge new things to find. When `status` warns that the candidate has grown past the limit, check that the fixer is not doing this.
- At the round cap, step back. A `stop:budget` means the approach is not converging. Reconsider the approach (the plan, the rubric, the references) and bring the owner a different plan, not the same plan with more rounds.
- Check usage at every round boundary against the allowance hard stops the [improvement loop](improvement-loop.md#prepare-one-bounded-work-item) cites, reading usage the way those rules say for the harness. An allowance stop there outranks `next`: at the notice level, report the reading with the round result; at the wrap-up level, finish the current round, write the loop record and ask before another; at the limit, dispatch nothing more and report where the run stands.
- Calibrate the judges, not only the candidates. After any change to a judge's card, brief, tools or model, run the [judge calibration set](judge-evals.md): it counts missed bugs and false blocks on known cases. Add a case whenever a real defect got past a panel.
- The judges' opinions are evidence for the owner, not a verdict on taste. Report the scores, the spread between judges and their dissent.

## Introduced and pre-existing findings

Each blocking item is an object: `item` (what is wrong and where), `origin` and `class`. `origin` is `introduced` when this candidate's change created or worsened the defect, and `pre-existing` when it was already there before the change. A judge who cannot tell says `introduced`. Only introduced items fail a round. Pre-existing items do not block the pass; `status` lists them under `backlog` with their round and judge, and the loop record hands them to the owner as work for another item. A plain-string blocking item, as older verdicts wrote it, is read as introduced, so earlier run folders still load.

## Review depth

`init --depth` sets how many judges a pass needs. Choose it from the change's blast radius, never from who or what wrote it. A judge's pass never stands in for the owner's approval: the panel is evidence for the owner, and a change that needs the owner's say-so still gets it at any depth.

| Depth | Judges | Choose it when |
|---|---|---|
| `quick` | The first judge only | The change is small, easy to undo and touches nothing shared: a wording fix, a local script, a draft the owner will read anyway |
| `standard` | First judge and the Sonnet confirmer | The default: a page, a document, a skill or a render plan that others will use but that is easy to revert |
| `deep` | First judge, Sonnet and Codex | The change is hard to undo or touches many files or other people's work: a shared rule, a public release, anything that moves data or spends money |

`record` refuses a judge the depth does not ask for. A run folder made before depth existed has no depth and keeps asking for every judge.

## Report

Each round's line in the loop record: round, candidate, each judge's score, checks, `next`, and what the repair targets. Close with the final panel score, the number of rounds, the run folder and any judge disagreement over 2 points.
