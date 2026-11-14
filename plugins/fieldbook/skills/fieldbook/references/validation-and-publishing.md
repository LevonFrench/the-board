# Validation, Performance, and Publishing

Run `scripts/check_fieldbook.py <root> --release` first. It covers the mechanical items below, and its warnings are candidates for judgement. Items it cannot cover are marked **(by hand)**.

## Pre-release checklist

### Research integrity

- [ ] Every consequential claim has source, date, geography, and limitation.
- [ ] Claim trace: every number, percentage and source ID in site data and HTML matches a capture or ledger row, or carries `inference` or `unknown`. A site fact with no Markdown record is captured first or removed.
- [ ] **(by hand)** At least six consequential claims traced to source wording: projected versus actual, phase versus total, per-worker versus uncapped.
- [ ] Every raw capture is cited by a topic or listed as `uncompiled`; nothing marked `stale-pending-compile` remains.
- [ ] Newest source record is not newer than the topics, or a reconcile item is open and the reader shows it.
- [ ] Counts come from a script. Status agrees across config, topics, editorial note and commits.
- [ ] No chat leftovers ("the article you pasted") or unwanted personal data in a deliverable.
- [ ] Public-platform results are not treated as market share, provider capacity, or permission.
- [ ] Legacy outputs do not contradict current decision pages without a superseded label.
- [ ] Counts derived from directories have a first-party verification path.
- [ ] Regulated/professional boundaries identify the responsible authorized party.

### Product clarity

- [ ] Home page points to one current decision path.
- [ ] Older hypothesis libraries defer to the current decision order.
- [ ] Every decision card has its subject kind's required fields, including a gate and a stop rule.
- [ ] Related modules explain whether they are channel, wedge, architecture, or vertical variant.
- [ ] Navigation exposes active location and remains usable on small screens.

### Technical checks

- [ ] Run the project lint task.
- [ ] Run production build.
- [ ] Check meaningful routes locally: home, best bets, one dynamic detail, each new hub, research, sources, review.
- [ ] For a local Fieldbook reader, generate it with `scripts/build_reader.py`, then open `index.html` from disk **(by hand)** and at narrow width when a browser is available. The checker verifies relative links, assets and path leaks in generated HTML and in anything it links to.
- [ ] Run whitespace/diff checks when a repository is available.
- [ ] Record pre-existing warnings separately from new failures.

## Performance work

Applies to a hosted site. Use a `web-perf` skill where the host has one (if you have none, say so rather than implying a performance check ran) when the user asks for Lighthouse, PageSpeed, Core Web Vitals, load speed, accessibility performance, or bundle optimization.

1. Retrieve mobile and desktop measurements from the requested public URL or PageSpeed API.
2. Trace the live page with the configured browser-performance tools when available.
3. Prioritize measured issues with meaningful estimated savings: image payload, LCP resource, render blocking, document latency, long tasks, layout shift, cache policy.
4. Map each live issue to source code or static asset before changing it.
5. Do not optimize a zero-impact audit hint just to make a checklist cleaner.
6. Rebuild, republish, and re-measure the same URL after the deployment settles.

Good marks do not justify speculative code churn. Report that the score is already strong and leave the stable implementation alone.

## Archives

The owner often asks for a ZIP. Build it from a manifest. Its pages may link only to files inside it, so include the Markdown they link to. Exclude secrets, source roots, private media and old archives. Test by extracting to an empty folder and running the checker there. Date the file name and do not keep superseded ZIPs in the reader's folder.

## Hosting by host

Publishing always needs the owner's words for that act. Prefer free routes.

- **Codex:** `sites:sites-building` and `sites:sites-hosting`, when the Sites plugin is present, using the steps below.
- **Claude Code:** with no site-hosting skill installed, hand over the local reader or single file. A private hosted page through the host's own artifact tool is an option only when the owner asks for a link.
- **Anything else:** treat it as a new capability and ask.

## Sites deployment (Codex)

Use `sites:sites-hosting` after a successful build whenever the user authorizes publication.

1. Read `.openai/hosting.json`; reuse its `project_id` if present.
2. Commit and push the exact validated source snapshot through the Sites workflow.
3. Package the built artifact with the provided package helper.
4. Save a version, set the requested access mode, deploy, and poll to success.
5. Open the successful URL in Codex and return the live link.

Do not expose credentials, temporary archive paths, repository tokens, internal IDs, or build-system details to the user.

For a public share link, make public access explicit. For local-only work, do not publish.

## Editorial pass report template

```markdown
---
title: "[Place] Fieldbook editorial pass"
type: report
sources: [relevant compiled topics]
generated: YYYY-MM-DD
---

# [Place] Fieldbook editorial pass

## Scope
[Review lenses, no new demand claims statement]

## Governing decision
[One current operating sequence]

## Material corrections
| Issue | Applied correction |
|---|---|

## Evidence limits that remain
- [Unproved buyer/pilot/permission facts]

## Related records
- [Dual-linked compiled topics]
```

## Public repository expectations

When releasing this skill publicly, include the skill folder, its references, agent metadata, license if the user selects one, and public-facing documentation that explains intended use, source standards, safety boundaries, and a simple invocation example. Keep user data, credentials, local research captures, browser cookies, API tokens, and deployment archives out of the repository.
