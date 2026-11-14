---
name: prose-humanizer
description: Final prose pass on user-facing writing (copy, docs, emails, reports, briefs) that removes AI tells while keeping meaning, facts, qualifiers, attribution and voice. Uses the installed humanizer skill as its method and returns the edited text plus a change list to The Agency.
---

# Prose Humanizer

## Use when

A deliverable contains prose a person will read (site or product copy, README or guide, email, report, proposal, script) and the draft is complete enough that only the wording should change. Typical places: the prose finish of a [Research](../../references/research.md) round after the claim verifier, a Fieldbook after its clarity critic, the finish step of [Product Design](../../references/workflows/product-design.md), an editorial or marketing deliverable, or a document the owner asked to "humanize" or "make it not sound like AI".

## Not for

Drafting from scratch, changing what the text claims, fact-checking, translation, code, configuration, commit messages, data files, legal or regulated wording that must stay verbatim, or text the owner wrote and asked to keep as is.

## Inputs

The absolute path of the text (or the text itself), its audience and purpose, the owner's voice samples or style rules if any, protected spans (quotes, figures, names, product terms, commands, links, citations) and the parent's return destination. Writable path: the deliverable file only, or report-only when the parent asked for a proposal.

## Work

1. Method: in Claude Code invoke the installed `humanizer` skill; in Codex use its `humanizer` skill; if neither is available, read humanizer/SKILL.md and apply it by hand. Optional phrase reference: stop-slop, without its absolute bans.
2. Keep a copy of the original. Mark protected spans before editing: numbers, dates, names, quotations, citations and links, code and commands, data, and every qualifier that carries meaning ("about", "may", "in our tests"). None of these change.
3. Edit for the tells the method lists (contrast templates, staged openers, one-line closers, forced triads, stacked dashes, inflated or sales language, stock AI words, bold-label lists, filler) while keeping the writer's register and the document's structure, headings and formatting conventions.
4. Re-read the result against the original sentence by sentence: same claims, same certainty, same attribution. Reverse any edit that shifted meaning. Do not add facts, examples, opinions or calls to action.

## Output

The edited text (in place when writing is authorized) and a short change list: categories of tells removed, any sentence intentionally left as is and why, and any passage where meaning was ambiguous and was not changed.

## Acceptance

`python -B <skill>/scripts/prose_check.py <original> <edited>` passes: every number, quote, URL, link target, wikilink, code span, evidence-tier tag, frontmatter block and heading level survived. In a wiki article, `research_check.py article` passes again too. Protected spans are byte-identical to the input; no claim, number or qualifier was added, removed or strengthened; the parent or owner can accept or reject the change list item by item. Readability judgments are owner acceptance ([evidence level 7](../../references/work-contract.md#evidence)), not something the worker certifies.

## Return

To the parent under the [work contract](../../references/work-contract.md) with a [status](../../references/work-contract.md#status), file path, change list, protected-span check result and anything left unresolved. Model: a writer-tier model per [Models](../../references/work-contract.md#models).
