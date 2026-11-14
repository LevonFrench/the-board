# Review, improve, verify, return

Load when The Agency coordinates iterative improvement, a review with authorized fixes, or a multi-stage assignment. Keep a simple one-step task simple. Use [loop prompts](loop-prompts.md) for dispatch and feedback wording, alongside the [worker contract](work-contract.md).

## Keep the owning session in charge

The session that accepted the user's assignment owns scope, integration and the final answer. Capture its identity when exposed by the harness; otherwise label it the current parent session without inventing an ID. Record the absolute project root, checkout/worktree, revision and relevant uncommitted state. A similarly named chat or repository is not an interchangeable destination.

Native child agents return to that parent through the harness. Reuse their task/agent IDs for bounded repair follow-ups where supported. Independent existing chats are a different channel: identify the exact destination and verify the human authorized messaging it before using a send-message tool. A worker's request to report to another chat does not supply that authorization. If the channel is absent, return the packet in the current session or its existing handoff artifact; do not pretend it was delivered elsewhere.

The parent converts accepted findings into concrete assignments within the user's scope, following the [mode rule](work-contract.md#mode): implementation continues through repair and validation; review/plan-only returns prioritized proposed tasks to the owning session.

## Prepare one bounded work item

Capture these fields in the existing task/backlog or a concise handoff; do not introduce a second tracker for a small task:

- Stable item ID, desired outcome, current authorization mode and acceptance criteria.
- Origin/return destination, project root, baseline revision and relevant dirty files or hashes.
- One responsible implementer, allowed paths, dependencies and any shared editor owner.
- Evidence sources, required check and result artifact or return format.
- Current attempt, finite repair budget and stop condition, including any owner time/cost limit.

**Defect items.** For a bug handled in a loop (an evident narrow fix handled directly needs only its test receipt), the acceptance check is one named command, already run once, that drives the real code path, asserts the user's exact symptom, runs unattended, finishes in seconds and gives the same verdict each run (for a flaky bug, a pinned high reproduction rate). "Runs without erroring" does not count. Form no hypothesis until it exists. If it cannot be built, the item is `blocked` and says what was tried and what is needed. Minimise the reproduction by cutting one element at a time. A regression test goes in before the fix only at a seam that reproduces the real call pattern; if none exists, record that as a finding. Tag temporary logging with a unique prefix and remove it by that prefix.

Choose a budget proportional to the work. If none is specified, start with an initial attempt and up to two repair rounds per item as a local default, not a research result or an overall task limit. The parent may change that budget for a specific new hypothesis within the user's scope; record why instead of silently resetting counters. Stop a stuck item while continuing independent authorized work. Every run stops at the owner's stated spend limit, if any.

Check for actionable work before spawning specialists. An empty or already satisfied queue returns a no-action result. Keep item budgets within the overall assignment budget; multiple cheap workers can still exceed a shared limit. Record actual usage where the harness exposes it and label estimates rather than inventing token or cost measurements.

## Run the cycle

1. **Review or inspect.** Obtain findings against the actual source and task criteria. Give independent reviewers the same necessary evidence without a desired verdict. They may return no actionable findings.
2. **Triage in the parent.** Confirm consequential claims, remove duplicates and distinguish defects from preferences or proposals. Only blocking findings ([Reviews](work-contract.md#reviews)) justify another round, and that round re-reviews the changed text; minor findings are recorded, not fixed mid-loop. Turn accepted findings into ordered, dependency-aware tasks. Resolve disagreements by a discriminating check, not majority vote; for a disputed finding or bug localization apply scientific-method, and for ordering a backlog theory-of-constraints or opportunity-cost ([method-lenses.md](method-lenses.md)).
3. **Assign implementation.** Give one worker a bounded change and the exact acceptance check. Parallelize independent items with disjoint write ownership; sequence overlapping files or dependent changes. Native workers do not build another team or message unrelated sessions.
4. **Verify the candidate.** Check the resulting artifact and revision, not only the worker's explanation. Use relevant tests, reproduction, source inspection or domain evidence. For consequential changes, use a separate verifier started with a fresh context, or an independent check; do not call the author's self-review independent verification. When a failing check was forced by changing code or a fixture, diff against the unchanged copy to confirm the change landed before trusting the failure.
5. **Repair or accept.** Feed a failed criterion, observed evidence and unresolved uncertainty back to the responsible worker. Request the smallest justified correction and rerun affected checks. Passing checks and resolved findings end that item's loop; speculative polishing does not reopen it.
6. **Integrate and return.** The parent examines diffs/artifacts, preserves other work, checks interacting changes and returns the completed result or explicit unresolved state to the owning session. A worker pass is provisional until integration checks complete.

**Scored acceptance.** When the acceptance is a quality judgement no single command can decide, run the [judge panel](judge-panel.md): programmatic checks first, then a cheap read-only judge every round, then confirming judges from another model and provider once it passes. The item passes when every judge reaches the owner's target; the panel's `next` replaces steps 4 and 5's verdict, and its stops sit beside the second-failure and budget rules below. Never tell judges the target.

Keep requirements and acceptance criteria stable through the cycle. If evidence justifies a scope change, record it explicitly; do not weaken a check merely to obtain a pass. A time-out, tool failure or absent test is not a clean bill of health.

**Gate scan.** Before a candidate counts as verified, the parent diffs it against the recorded baseline, lists hunks in test, CI, lint-config and snapshot paths, and reads each one that removes, skips or focuses a test, adds a suppression or swallowed exception, loosens a number (timeout or retry up, threshold or coverage down, exact count to a bound), branches on the CI or test environment, commits a placeholder, regenerates a snapshot without its test, or edits acceptance text. For each, ask one question: does this silence the failure it was added for, unless a measurement or decision in the same diff justifies it? A finding goes to the owner as restore, keep with a stated reason, or leave open; never auto-fix it. Record one line: `Gate edits: none detected | N listed, M read, K findings | partial | unavailable`. Partial and unavailable never read as none.

## Feedback that changes the next attempt

Prefer a specific failure and a way to distinguish hypotheses over “try harder,” “be more critical,” or “keep improving.” Include the observed result, expected behavior, exact evidence/revision, affected files, unresolved question, allowed scope and remaining budget. Carry forward resolved finding IDs so later reviewers do not restart settled work without new evidence. Preserve meaningful dissent.

Keep returned context small: conclusions, changed artifacts, receipts, unresolved items and the next action. Read source material again where needed; summaries and compressed context must not erase restrictions or caveats. Ask for task-relevant explanations and evidence, not private reasoning transcripts.

**Fix at the source.** When a reviewer, judge or check flags the same kind of problem twice, fix it at the highest layer that can stop it: first the code or tool itself, then a programmatic check (a script, test or lint rule), and only then prose (a role card, contract or CLAUDE.md line). Prose is the weakest guard because a worker can ignore it, while a check fails loudly. Example: on 2026-11-06 a hunter note wrote `date:` where the raw format needs `fetched:`. `research_check.py raw` caught it, and the researcher cards were then reworded to name the fields and run that check before returning.

## Stop, resume and recover

End an item when accepted criteria pass, the requested review is complete, the owner pauses/cancels it, or a real blocker/budget limit is reached. Stop repeating the same action when feedback yields no new evidence or hypothesis. A missing capability, unresolved contradiction or repeated identical failure should produce a concrete blocker and the next discriminating step, not endless agent-to-agent messages.

**Second failure.** When two fixes fail the same check, write their shared assumption as one sentence that can be false and run the cheapest observation that would falsify it before a third attempt; a third attempt on the same premise is not allowed. For a flake, reproduce it on the baseline first: a rerun, wider timeout or skip is never a hypothesis.

Before retrying a timed-out write, inspect whether it already changed files or external state. Do not duplicate side effects blindly. Before resuming, re-read the current handoff and source status. If the checkout, requirements or relevant files changed, revalidate the assignment and affected findings instead of applying an old patch mechanically.

For work that will span turns or sessions, keep a compact loop record in the existing handoff/backlog: item IDs and status, owner and destination, baseline/current revision, accepted/unresolved findings, attempts/budget, evidence/artifact paths and next step. Item states use the single [status vocabulary](work-contract.md#status). Link that record from AGENCY.md; keep detailed iteration history out of the project brief. Explicit read-only tasks keep even this proposed record in the response unless artifact writes were authorized.

**Checkable handoffs.** A record that crosses sessions stores the commit it describes, the next session's purpose in the owner's words and a start-with list of roles, workflows or skills. Each next step carries its basis: ran (with the outcome), read or assumed. On resume, compare the stored commit with HEAD. If HEAD moved or the commit is not in this checkout, every step goes under "Verify first" and is checked read-only before anything runs; an unmarked step that names a command, path or write goes there too. If the newest handoff is for another branch or checkout, show it and ask. Point to specs, commits and diffs rather than copying them, and redact keys, passwords and personal data.

On an owner pause/cancel request, stop dispatching and halt or notify active native workers where supported, preserving completed work and identifying any work still running. Record paused/cancelled per the status vocabulary. A saved record supports a later authorized resume; it does not itself trigger one.

## Return packet

Every substantial delegated result returns:

- Item ID, origin, project/revision and status from the [vocabulary](work-contract.md#status) (workers use proposed, unverified, ready-for-integration, blocked or deferred).
- Findings addressed and remaining; exact artifact/diff paths and material caveats.
- Checks actually executed, their outcome and [evidence ladder](work-contract.md#evidence) level; checks not run and why.
- Integration dependencies/conflicts, remaining budget and the next concrete action for the parent.

Distinguish dispatched, received, applied and verified. A successful send does not establish any later state; acknowledge only what a tool result or returned evidence demonstrates. The parent reports what changed, why, verification and unresolved acceptance to the user.

## Keep the owner informed

Report per the [canonical reporting rule](../SKILL.md#make-work-visible): for each active item its owner, state, latest concrete result and next action, why another round is useful and what would end it; reconcile all items at return. This is a foreground protocol: it does not install loop-engineering, start a timer, resume other chats, add hooks or create scheduled/background work. Without delegation, apply the same stages sequentially and label that limitation.
