# Fieldbook division

Load for any Fieldbook run that needs a team, fan-out or review-fix loop; pass this contract with every role. A plain build, audit, refresh or page edit uses the `fieldbook` skill alone. Roles are local worker briefs, not skills or background agents; pick the smallest set. The method lives in the `fieldbook` skill at <fieldbook skill>/SKILL.md (references, templates and scripts beside it). Read it before dispatch; this file adds who does what. Built from an audit of every built Fieldbook: the author's build notes (not included).

| Role | Trigger → result | Model |
|---|---|---|
| [Evidence clerk](../roles/fieldbook/evidence-clerk.md) | Local files, owner records, captures → inventory, coverage, gaps | `haiku` |
| [Track researcher](../roles/fieldbook/track-researcher.md) | One external-needed track → raw captures, ledger rows, rosters | `haiku`; `sonnet` for contradictions |
| [Compiler](../roles/fieldbook/compiler.md) | New evidence → labelled topics, propagation sweep | `sonnet` |
| [Decision analyst](../roles/fieldbook/decision-analyst.md) | Compiled topics → decision cards, tiers, gates, stop rules | `sonnet` or `opus` |
| [Reader builder](../roles/fieldbook/reader-builder.md) | Compiled Markdown → static reader or site | `sonnet` |
| [Accuracy verifier](../roles/fieldbook/accuracy-verifier.md) | Draft → claim trace, classified corrections | `sonnet` or `opus`, not the compiler's |
| [Clarity critic](../roles/fieldbook/clarity-critic.md) | Draft reader → first-time reader's path, fixes | `sonnet` |
| [Strategy critic](../roles/fieldbook/strategy-critic.md) | Decision cards → conflicts, unsafe roles, push-backs, defense | `sonnet` or `opus` |
| [Release steward](../roles/fieldbook/release-steward.md) | Any change or handoff → reconcile, counts, editorial record, package | `sonnet` |

## Team for the job

| Job | Team |
|---|---|
| One question, one page, a small correction | 0 workers: the `fieldbook` skill directly |
| New broad Fieldbook (`market`) | Clerk if local files exist; 2–4 researchers per round; compiler; analyst; reader; all three critics; steward |
| Household decision (`household`) | Clerk; 2–3 researchers; compiler; analyst; accuracy verifier; reader; steward |
| Project state (`project-state`: game, app, company) | Clerk; compiler; accuracy verifier; steward; reader. No researcher unless the config allows external research |
| Company or person dossier (`entity`) | Clerk if local files exist; 2–3 researchers; compiler; analyst; accuracy verifier; reader (`single-file`); steward |
| Archive, artist, collection (`archive`) | Clerk; researchers on gaps only; compiler; accuracy verifier; reader; steward |
| Team refresh or expansion of an existing one | Steward first (reconcile); then researchers on stale gaps only; compiler; verifier |
| Team audit with no edits | Steward's checks plus the three critics, report-only |

Three critics are separate lenses and stay separate: they found different real defects on one book, three times. A role that would repeat a script's work is dropped; most defects the audit found were checks nobody ran, not missing people. Add a role only for a demonstrated need. An ideation panel ran once on one book and its pick was not adopted; it is not a standing role.

## Order

1. **Brief (parent).** Subject kind, decision, audience, release status, source roots and budget, in `fieldbook.config.yml` and `guidance.md`. Parent owns both; workers propose entries.
2. **Inventory (clerk).** Local before web. Coverage matrix and gap register exist before any synthesis.
3. **Research (researchers).** Non-overlapping tracks, external-needed or contradicted gaps only, one round at a time.
4. **Compile (compiler), then decide (analyst).** Sweep after every ingest. Late evidence reopens what it touches.
5. **Build a draft (reader builder).** Critics and the checker need a reader to read.
6. **Check (steward's scripts), then critique (verifier and critics, read-only).** Parent triages. Fixes return to the owning role.
7. **Rebuild, then release (reader builder, steward).** Reader is regenerated from Markdown, checked, and recorded.

Each round ends with `python <fieldbook skill>/scripts/check_fieldbook.py <root>`, reported as evidence level 2. Test the assembled Fieldbook, not a page in isolation.

## Shared contract

- **Proof chain:** source → evidence record → bounded finding → hypothesis → the kind's test (buyer and paid pilot, or quote and spend gate, or engine and player check). Arrows do not collapse. A directory is not demand, a listing is not permission, a passing test is not a shipped build.
- **Labels:** use the skill's vocabulary everywhere and no other (research-and-evidence.md). External-primary means the page itself was opened; a search-result extract is `search-extract`. Negative findings say "not found in this pass" with the boundary searched.
- **Markdown is canonical.** No fact exists only in a site, data file or reader. One book's site carried 23 of 149 sources with no wiki record, so the trace runs on site data too.
- **Writers:** parent alone edits `fieldbook.config.yml`, `guidance.md`, indexes and the canonical summary; other writers get named files and never overlap. Raw captures are immutable.
- **Wiki:** where a topic wiki exists it holds raw and compiled evidence, under the wiki skill's rules; the Fieldbook links or summarises and never forks it; long tables render through `reader.wiki_articles`. Query the wiki first; research only a real gap ([knowledge-workflow.md](knowledge-workflow.md)).
- **Privacy:** owner records and household details stay out of HTML beyond what the decision needs. Readers never contain absolute paths, source-root names or secrets. Full paths belong in chat handoffs.
- **Permission:** roles grant nothing. No publication, deployment, outreach, purchase, account action or login-walled scraping without the owner's words for that act. Public social evidence only, by normal browser access. An owner's request for a pitch is recorded as framing; it does not remove labels or limits.
- **Advice:** research and product design only; never investment, legal, regulatory, medical, employment, surveying, tax or public-safety advice. The licensed or authorized party stays named.
- **Budget:** state rounds and workers before each fan-out. One 26-agent pass cost about 1.2M tokens and was parked for quota. Stop researching when questions are answered or the next source class is unavailable; remaining work goes to `refresh-backlog.md`.

Evidence ladder for this work: level 1 source and citation reads; level 2 `check_fieldbook.py`, reader self-check; level 3 reader opened from disk; level 4 narrow-width and visual read; level 6 publication; level 7 the owner's decision. Buyer interviews, quotes and pilots are the owner's, reported as such.

Worker results use the [work contract](work-contract.md); reviews with authorized fixes also use [improvement-loop.md](improvement-loop.md). Standalone use of the skill keeps its own flow; this division is for runs that need a team.
