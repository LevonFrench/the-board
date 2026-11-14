---
name: research-compiler
description: Coordinator-applied step that compiles kept raw notes into wiki articles in batches of 5 to 10, with an evidence tier on every non-obvious claim, a verbatim quote for every number, disputes recorded, the primary URL on its own line and hub-and-spoke links. Never dispatched in parallel.
---

# Compiler

## Use when

The source clerk's ledger is accepted and the kept notes are in `raw/`, under the [Research contract](../../references/research.md). The coordinator applies this role itself.

## Not for

Dispatch to a parallel worker (only the orchestrator writes compiled articles), new research, or editing raw notes.

## Inputs

The ledger, the kept notes, the wiki's existing articles on the subject and the plugin's compile protocol.

## Work

1. Compile in batches of 5 to 10 notes, following the plugin's compile protocol. A bulk batch of 30 or more has shipped placeholder shells before.
2. Tag every non-obvious claim `[primary]`, `[community]`, `[press]`, `[inference]` or `[UNKNOWN]`. Give every number a verbatim quote from its note. A datamined value never inherits the authority of an official page beside it.
3. When credible sources conflict, state both, name the favoured reading and why, and mark it `DISPUTED`. Record confirmed non-existence as a finding.
4. Put the primary source URL on its own line; list the raw notes under `sources:`. Engine-general or cross-project knowledge goes to a hub topic, linked from the project wiki, not copied.

## Output

New or updated articles and the list of paths changed.

## Acceptance

`research_check.py article <paths>` passes, and each article's confidence follows its corroboration.

## Return

The changed paths go to the claim verifier, with the ledger.
