# Method lenses

Load at one of the decision points below, not as a general menu. A lens is a short structured procedure that a worker (or the coordinator) reads by absolute path and applies to the current evidence. Source: owner-approved pinned snapshot of cc-thinking-skills at $THINKING_SKILLS_DIR, commit `7b8fece345dfaa11773be7152ccd194589cb5437` (MIT). Evidence basis: the author's research notes (not included).

## Decision points

| Agency decision point | Lens (read this file) | Evidence that must be able to fail |
|---|---|---|
| AGENCY.md, HANDOFF.md, a KB summary or a report disagrees with live source | map-territory | The current file, command output or data actually observed |
| Disputed finding, bug localization, improvement-loop "discriminating check" | scientific-method | For a bug, a [red command](improvement-loop.md#prepare-one-bounded-work-item) first; pre-stated falsifier per hypothesis; executed read/grep/test results |
| Fault localized but it recurs, or the systemic cause is unknown | five-whys-plus | Cited log/code/config per "why"; counterfactual check per root |
| How much deliberation a consequential plan or decision deserves | reversibility | A concrete undo path and its cost |
| Costly-to-undo plan before commit (release, migration, schema, purchase or persistence change) | pre-mortem, after reversibility rates it hard to undo | Each top failure path bound to a verification checkpoint or gate |
| Product Design or Audience Lab: what to build, why adoption fails | jobs-to-be-done | Cited spec, tickets, analytics or product behavior; no invented quotes |
| Capability intake: can this claim about a candidate be asserted? | circle-of-competence; add lindy-effect only when long-term survival of a dependency matters | Source read or run this session; otherwise fetch or abstain |
| Ordering a backlog or choosing the next item | theory-of-constraints when one stage limits throughput; opportunity-cost when scarce time must be split | Measured queue/rate or a named best alternative with its value |

### Engineering methods (simcraft @58224d1, read by path)

These come from a second pinned source, simcraft. Read the SKILL.md and its reference.md as method text. Their scripts are POSIX-first: on Windows, `bisect.py`, `stress.py` and `bench.py` fail, and only `flake_rate.py` (with `PYTHONIOENCODING=utf-8`) and `env_report.py` ran in the trial (the author's build notes (not included)).

| Agency decision point | Method (read this file) | Evidence that must be able to fail |
|---|---|---|
| A regression with a known good point | bisect-anything | An oracle command that exits 0 on the good end and non-zero on the bad end, checked on both ends before any bisect |
| A test that fails only sometimes | flaky-test-killer | A measured failure rate before and after, with its interval. No retries, sleeps or longer timeouts as the fix |
| A claim that something is faster or slower | benchmark-honestly | Shuffled repeated runs with an interval, the same output on both sides, and the environment recorded |

Eight primary procedures across seven decision points; lindy-effect and opportunity-cost are conditional companions. Every lens file has its own "When NOT to use" section: obey it, and skip the lens for small, reversible or already-evidenced work.

## Rules

- **Structure, not a quality claim.** Packaged frameworks and personas show little or no measured accuracy gain; the source's own audit keeps all 28 procedures manual-only. Never claim a lens improved a result without a local with-versus-without comparison.
- **Pair every step with evidence that can fail:** an executed check, cited file lines or reproduced output. Imagined outputs do not count.
- **One short lens at a named decision point,** not a stack of frameworks. If none fits, proceed without one.
- **End critique with an executable or source check** before a finding is accepted; elaborate critique without that check raises false alarms (see [work-contract.md](work-contract.md#evidence)).
- **Label use** in reports: `Lens: thinking-<name> @7b8fece, applied by <worker or coordinator>`, plus its output block.
- **No personas as an accuracy device.** A lens changes procedure, not identity.

## How to use

1. Put the lens's absolute path in the worker brief (`Method lens:` line in [loop-prompts.md](loop-prompts.md)); the worker reads the file directly. Do not call the Skill tool: every lens sets `disable-model-invocation: true`, so model invocation is blocked.
2. Shortlist with `python 'scripts/catalog.py' --kind method --query '<term>'`.
3. If `git -C $THINKING_SKILLS_DIR rev-parse HEAD` differs from the pin, report the drift; refreshing the snapshot needs owner approval.

Do not adopt: `thinking-model-router` (The Agency already routes; a second router doubles routing), the upstream eval machinery, or global/auto-invoke installation.
