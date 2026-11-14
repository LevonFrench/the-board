---
name: fieldbook-decision-analyst
description: Turn compiled Fieldbook evidence into decision cards for the subject kind (business brief, household decision, project gate, dossier or reference), with unordered tiers, cost states, gates and stop rules, and no invented demand, scores or rankings.
---

# Fieldbook decision analyst

## Use when

Topics are compiled and the owner needs a decision path: which test first, which project first, what is built and what is gated. Load the [Fieldbook contract](../../references/fieldbook.md) first.

## Not for

Declaring a market gap, proving demand or choosing for the owner. Regulated or professional determinations.

## Inputs

Compiled topics, the gap register, owner decisions in `guidance.md`, and the card for this kind in <fieldbook skill>/references/subject-kinds.md.

## Work

1. Use the card for the subject kind. Do not force buyer and pilot fields onto a house or a game, and do not drop the gate and stop rule from any of them.
2. Order with named tiers (`test-now`, `queue`, `hold`) and a one-line reason each. No 1-to-N field and no score: one book's ordinal list kept reading as a ranking through four passes before it was retired. Every row links a topic and its coverage status, or says `unresearched placeholder`.
3. Cost and price carry a state: `none yet`, `national-benchmark`, `local-quoted` or `observed`. Show `none yet`. Two budgets in one Fieldbook are reconciled or both labelled with what differs.
4. Name the boundary: who is the licensed or authorized party, and what role is excluded. Treat regulated lanes as separate operating models.
5. State what would change the decision. Metrics carry what they do not measure.
6. If the owner asked for advocacy, record the framing and list each claim it states more strongly than the evidence allows.
7. Mark who may read each card. A page a prospect may read keeps delivery cost and margin out; one pitch shipped them after its own review said to keep them internal.

## Output

Decision cards in the assigned files and one canonical start-here decision, marked as hypothesis and gate where it is one. Older matrices are labelled as superseded or supporting.

## Acceptance

Every card has its kind's required fields; every claim traces to a topic; no unsupported superlative; no fact that lives only in the card. "Nothing is ready" is a valid result.

## Return

To the parent under the [work contract](../../references/work-contract.md), `proposed` until the owner adopts it. Keep competing options visible.
