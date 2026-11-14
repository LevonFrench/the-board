---
name: product-design
description: Improve a concrete interface problem using existing brand and content authority, traceable design references, scoped implementation and relevant visual, state and accessibility evidence.
---

# Product Design

## Use when

A new interface or a named usability/visual defect. The existing UI Designer/UX Architect owns the contract; Brand Guardian joins when identity matters; the UI Finish-Gate Reviewer checks the result where available. Reference scouting is a temporary assignment, not a permanent role.

## Not for

Invented realism for a real product (fake dates, metrics, names, screenshots or measurements), overriding established brand choices the task does not change, or persisting generated design documents before reconciliation.

## Inputs

The actual screen, audience/task, real content, design contract and existing Master/page decisions; the defect and expected improvement.

## Work

1. Build a preserve/change map before proposing a direction. When what to build or why adoption fails is unclear, apply jobs-to-be-done ([method-lenses.md](../method-lenses.md)).
2. Choose task-relevant references. The optional [design retrieval adapter](../design-tool.md) returns source identities, defaults/abstention and raw JSON; keep these with the query and source revision; query stack guidance separately where the tool requires it. Matches guide judgment, not effectiveness.
3. Reconcile with the real project: reject category mismatches (landing-page hero/CTA defaults for a dense dashboard). A protected Master or no-overwrite behavior does not reconcile a new page override. With missing tools, abstention or weak evidence, use the project contract plus direct inspection and label fallbacks as coordinator judgment.
4. Implement authorized scope through the [improvement loop](../improvement-loop.md). Label synthetic fixture content clearly; never simulate commands.
5. Check the states relevant to the change: named viewports, narrow width, long labels, keyboard/focus, contrast, loading/error/empty, touch and reduced motion as applicable, recording exact state and artifact. WCAG 2.2 detail for these checks (24x24 targets, 200% text, 320 px reflow, focus not obscured) is in flawless-ui-ux/skills/flawless-ui-ux/references/interaction.md, "Accessibility acceptance"; read it by path.
   - **Optional rendered sample.** The checker is https://github.com/smokeeaasd/flawless-ui-ux, reviewed at 82d9355. It is not included: clone it, install its dependencies yourself, and skip this step without it. Run it against a local dev server.
     - Take a baseline with `node flawless-ui-ux/bin/flawless-ui-ux.js inspect --project <abs project> --source <relative file> --url http://127.0.0.1:<port>/<route> --viewport 1440x900 --viewport 390x844 --output <new folder outside the source tree>/baseline --format json`.
     - After each repair round, run `verify <baseline>/run.json --output <folder>/round-N --format json`.
     - Use the same viewports, sources and URL every round.
     - It checks the initial state only: contrast, names for buttons, links, inputs and images, text under 12 px, horizontal overflow, broken images and page errors.
     - Keyboard and focus, long labels, loading, error and empty states, touch and reduced motion stay manual. A removed focus outline passed it in the trial.
     - Exit 1 means confirmed findings. Exit 0 can still carry `needs-review` findings, so read `findings` in run.json every time. Exit 2 means coverage was partial, which is not a repair.
     - It checks no gutters, padding or alignment, and it runs five axe rules. On a real landing page it found 1 of 12 findings; a hero with no side gutter from 521 to 1180 px passed it. Read a screenshot at each breakpoint band of the stylesheet yourself.
     - Never run its `install` command.
6. Finish prose preserving meaning, qualification, attribution and code/link/data boundaries. Assign the [Prose Humanizer](../../roles/general/prose-humanizer.md) role (installed `humanizer` skill) for user-facing copy; stop-slop is optional phrase guidance, not blanket grammar bans or a self-score gate.

## Output

The [design contract and evidence template](../../assets/workflows/product-design.template.md), plus a [work-item packet](../../assets/workflows/work-item.template.md) for delegated repairs: preserved decisions, source/default provenance, rejected mismatches, expected behavior and actual state checks.

## Acceptance

A named defect with current source/rendered evidence and the smallest justified correction, judged against the same criterion across repair rounds. Source review cannot establish rendered behavior or full accessibility; owner aesthetic acceptance is reported separately ([evidence ladder](../work-contract.md#evidence)). Low-dependency pilot: branded landing page, dense dashboard, chip-overflow and unknown-category queries without persistence, then one screen/defect. Findings and adaptation limits.

## Return

To the parent under the [work contract](../work-contract.md) with a [status](../work-contract.md#status); design-only requests return proposals, implementation requests include changes and checks.
