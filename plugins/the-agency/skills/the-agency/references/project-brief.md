# Maintaining AGENCY.md

Load when creating or updating a project brief. This file is the canonical home for brief rules; the always-loaded global rules only point here.

## Purpose and authority

Give a new agent a useful first minute: the project's idea, what matters now, protected decisions, authoritative links, and how to verify progress. This is a navigation/continuity brief, not a second wiki, transcript, backlog or permission layer.

Use the explicit project root or establish it from instructions, checkout and manifests. In a monorepo read the repo brief and relevant existing subproject brief, with scopes stated. Do not search the whole disk or create files in every directory. Prefer AGENCY.md for new files; maintain existing agency.md without a case-only duplicate. If both exist on a case-sensitive system, resolve scope before editing.

Current user and applicable global/project instructions govern actions. Confirmed decisions, current source/manifests, release records and receipts establish facts; the brief summarizes them. Resolve stale conflicts without overriding the owner. Do not promote session digests or reviewer recommendations into confirmed decisions.

## Content and size

Aim for roughly 60–120 lines when warranted; smaller projects need less. Omit empty sections and link detail. Preserve useful existing structure.

- Identity: idea, audience, concrete success criterion.
- Current state: stage, immediate objective, actual stack/platform and current limitation.
- Confirmed decisions/constraints: durable facts with source links; proposals separately.
- Read first: a few source entrypoints, handoff and master KB articles, absolute paths and why each matters.
- Work map: key areas, useful specialist hints and what could change those hints.
- Acceptance: known checks, each tagged with its [evidence ladder](work-contract.md#evidence) level where relevant.
- Next priorities/open decisions: short, ordered, linked to the maintained backlog.
- Active delegated work, when relevant: owning session/lead, immediate item and link to the current loop/handoff record. Keep attempt history and per-worker details in that record, not this brief; the link does not authorize messaging another chat.
- Freshness: actual verification date and scope, revision if relevant and unverified facts.

Link canonical KB articles and decision records by full absolute path; never invent KB master articles or copy private content. Check a known project wiki index or registered hub/project index; if absent, say so. If you keep a wiki, link its articles instead of copying them. A brief does not require creating a wiki or modifying its registry.

## Update triggers

On first substantial authorized write work in a project without a brief, create one from verified evidence. A read-only visit can identify the gap but does not authorize writing.

Update affected sections when purpose, stage, major architecture/toolchain, an owner decision, milestone/priority, canonical KB link or acceptance/release gate changes. Minor details and passing tests need not change the brief. Do not rewrite every turn or advance the whole-file verification date after checking only one claim.

Before finishing material work, check whether the brief became inaccurate. Re-read immediately before writing, merge only evidenced changes and preserve concurrent edits. Say what was inspected when status depends on a dirty checkout.

Replace superseded prose only when a current source establishes the replacement; keep history in existing handoff/decision records. Recommendations stay proposed until adopted. Unknowns remain unknown. Include no secrets or private-message contents.

Maintenance occurs during ordinary project work. This does not create a scheduler, watcher, hook, background service or estate-wide retrofit.
