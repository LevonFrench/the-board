# Worker and synthesis contract

Load before delegating any work. This file is the canonical home for the mode rule, the status vocabulary and the evidence ladder; other files link here.

## Mode

- **Read-only / review / plan:** findings, decisions or proposed tasks only. No source, brief, KB or artifact writes unless artifact output was explicitly authorized; proposed brief corrections stay in the response.
- **Implement / fix:** the authorized changes plus relevant checks, carried through repair and integration without asking again for the same permission. Recommendations alone do not finish it; do not stop at a panel report.
- Compound requests keep each part. A new finding cannot authorize deployment, account access, messaging another chat or unrelated work. An approval covers the item it named, not later work. An unattended worker takes a recommended option only for reversible in-scope choices; consent, spend, publication and destructive choices are returned to the owner as open decisions.

## Status

One vocabulary for status tables, work items, loop records and return packets:

| State | Meaning | Set by |
|---|---|---|
| queued | accepted, not started | parent |
| active | being worked or checked | parent |
| waiting | held by a dependency inside the assignment | parent |
| proposed | review/plan result; nothing changed | worker or parent |
| unverified | changed, but required checks were not run (say why) | worker |
| needs-repair | a check failed; repair round pending | parent |
| ready-for-integration | changed and candidate checks pass | worker |
| verified | integrated; required checks pass on the current result | parent only |
| blocked | external blocker, missing capability or budget exhausted | anyone |
| deferred / paused / cancelled | owner or parent decision; distinct from verified | parent |

A worker never promotes its own result to verified. One blocked item does not block independent work; report overall assignment status separately.

## Evidence

Ordered evidence ladder. Each level is distinct; a pass at one never stands in for another. Require only the levels relevant to the change and report the highest reached with revision, environment, case and artifact.

1. Source/static inspection (code, config, documents, cited KB lines)
2. Automated checks (unit, fault, headless, lint)
3. Runtime (app, editor or Studio run, multi-client simulation)
4. Visual/audio (rendered states, listening)
5. Target device (named physical hardware, sustained load)
6. Live service / publication
7. Owner acceptance (product, aesthetic, release decision)

**Blind visual judge.** For visual deliverables (3D assets, renders, scenes, UI looks) where builds or iterations compete, level 4 is judged by a fresh-context judge that compares review images with shuffled labels against a written rubric. The builder never grades its own visual work; on a tie keep the incumbent (earlier) version; with no incumbent (parallel first builds), the owner picks. Self-judging agrees with the true metric near chance (the author's research notes (not included)); a 2026-10-25 MCP-vs-headless Blender test used this method (the author's research notes (not included)).

**Honest results.** A check passes only if it ran more than zero cases and exited 0; a runner reporting zero cases is a failed lane, and a failed capture is an error, never clean or skipped. A red is pre-existing only if the unchanged baseline reproduces it; if that is ambiguous, it belongs to this change. A receipt names the command, the revision or hash of what it consumed, and the count; changed content makes it stale. A reported measurement states what was measured and its run-to-run variation: one run on each side makes no claim about the delta, and a gap smaller than the variation is no measurable change. A merge, a 200 or a reachable URL proves reachability, not that this revision is live.

Separate observations, inferences, hypotheses and proposals. Consensus is not proof. A timeout, tool failure or absent test is not a pass. Before accepting a consequential finding, end with an executable or source check (the skeptical check; see [method-lenses.md](method-lenses.md) for scientific-method and pre-mortem).

A return that changes files or a wiki states three things: how it was tested (the command and its result, or the check not run and why), the risk (what could break and who it affects), and how to undo it (the commit or rollback command, with full paths).

## Worker brief

```text
Outcome and mode:
Item ID, owning session and permitted return channel:
Absolute project root, checkout/revision and current stage:
Role/skill path and required wrapper/overlay (and method lens path, if any):
Relevant source paths and KB master articles:
Confirmed decisions, constraints and open choices:
Single responsibility and specific questions:
Writable paths (or report-only: no commands with the target as working directory), exclusions and shared editor owner:
Available evidence/tools and known limitations:
Requested model/effort and reason; observed model if exposed:
Dependencies and handoff artifact:
Required result, acceptance check (ladder level) and bounded budget:
Return also lists every edit to a test, CI, lint config, snapshot or acceptance text, for the reader to examine:
Attempt/repair limit and stop condition; resolved and unresolved finding IDs:
Progress return: phase, concrete result, blocker and next action at milestones:
Absolute output path:
Do not expand the team, modify other workers' files or start another panel.
```

Start each worker with a fresh context window, never a fork of the parent; the brief carries what it needs. An independent verifier sees the candidate and criteria, not the author's reasoning. A bounded repair may continue its own worker ([improvement loop](improvement-loop.md)).

Pass task-relevant KB excerpts or links ([knowledge-workflow.md](knowledge-workflow.md), [evidence return](../assets/evidence-return.template.md)). Workers cannot infer access or permission from a report. Model choice follows [Models](#models); never invent model IDs; queue workers within capacity. Keep architecture, ambiguous decisions, difficult repairs and final integration in the owning session unless a demonstrated need warrants another assignment; escalate a worker only for a concrete unresolved failure, with its evidence and remaining budget. Record model, token or cost values only when the harness exposes them; otherwise mark them unknown.

## Models

Pass an explicit model on every worker; an omitted model inherits the coordinator's. Local model rules win. In Claude Code:

| Worker | Model | Why |
|---|---|---|
| KB research, scouts, source fetch/extraction, note writing | `haiku` (Claude Haiku 5.5) | Narrow, high-volume work at a fraction of the cost |
| Read-only evidence gathering: current-state or map-territory reconciliation, doc-vs-receipt audits, inventory, log and receipt reading | `haiku` | Close to Sonnet on knowledge work; reads, does not decide |
| Implementation writers | `sonnet` or `opus` | Haiku 5.5 is markedly weaker on complex agentic coding |
| Independent verifiers of consequential results, data-safety pre-mortems | `opus` or `sonnet`, different from the author's | Rigor and model diversity |
| Security review | `sonnet` or `opus` | Haiku 5.5 safeguards block offensive-security analysis |

Escalate a Haiku worker only after a concrete failure, with its evidence. Codex: use the equivalent cheapest capable worker model.

## Reviews

Do not seed a desired verdict. Each report states scope and evidence, findings with exact references and impact, remedies, uncertainty and acceptance checks, and separates facts from inferences and challenges to confirmed decisions. No finding quota or padding; no actionable findings is valid.

A finding is blocking if it would fail a check, break running behaviour, or lose data or secrets; the rest are minor. It must quote the line that proves it; one that cannot is unverified and stays out of the main report. The parent drops or downgrades, and says so, findings that are style-only, hypothetical with no input that reaches them, or "I would have done it differently" with no failing case. Data loss, a bypassed trust boundary and uncapped spend stay blocking.

A finding that would change the owner's stated scope or direction is the owner's decision, even when reviewers agree: queue it with its cost if wrong and never auto-apply it.

## Implementation

Assign nonoverlapping writable files and integrate dependencies in sequence; writes stay single-threaded per file set. One owner controls each live editor/session. Overnight, unattended or parallel workers on Blender and other engine/DCC apps use headless/batch runs, one app process per worker, never a shared live editor session; live editor/MCP sessions are for watched work with one driver. Blender specifics: studio-experts `references/blender-agent-notes.md` section 5 (`<studio-experts skill>/references/blender-agent-notes.md`). Inspect unexpected edits and preserve user/other-agent changes; never blindly revert them.

## Synthesis

Verify consequential findings against source; resolve disagreement with the cheapest discriminating check or preserve the uncertainty. Prioritize by impact, evidence, dependencies and cost, not votes. Workers send milestone/blocker updates to the parent; the parent owns the user-facing account ([reporting rule](../SKILL.md#make-work-visible)). Review/repair cycles follow [improvement-loop.md](improvement-loop.md); messaging an independent chat needs the human's authorization and an exact destination.

A substantial SUMMARY.md holds outcome, scope/revision, team and reasons, verified priorities with citations, disagreements, ordered actions, actual validation receipts by ladder level and owner decisions.
