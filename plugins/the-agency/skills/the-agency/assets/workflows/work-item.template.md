# Work item: <stable ID> — <outcome>

<!-- Use in the existing task record, or copy to an authorized absolute output path. Remove unused fields. Bracketed values are placeholders, never evidence. -->

- Owning session and permitted return channel: <current parent identity if exposed; otherwise current parent session>
- Mode and authority: <review / plan / implement / fix; relevant user instruction and limits>
- Project root / checkout: <absolute paths>
- Baseline / current source state: <revision or hashes; relevant dirty paths>
- Accountable worker / role: <owner; absolute role or skill path>
- Writable paths / exclusions / shared editor owner: <exact scope>
- Dependencies and source/KB pointers: <item IDs and absolute paths or source URLs>
- Required artifact: <absolute output path; format>
- Attempt and finite repair budget: <current / limit; task-wide time or cost limit if supplied>
- Stop condition: <criterion pass, concrete blocker or stated budget>
- If this crosses sessions: <commit described; next session's purpose in the owner's words; start-with list>

## Acceptance

| Criterion ID | Required observable behavior/result | Exact check and evidence scope | Owner |
|---|---|---|---|
| <AC-ID> | <fixed expected outcome> | <evidence-ladder level: source / automated / runtime / visual-audio / target-device / live / owner> | <owner> |

Defect item, red command: <command and output, already run once; if none can be built, status blocked with what was tried and what is needed>

## Findings and progress

| Finding/item ID | Status | Evidence / current artifact | Resolved or remaining issue | Next action / owner / basis (ran, read, assumed) |
|---|---|---|---|---|
| <ID> | <state from references/work-contract.md#status> | <absolute path or source URL> | <concrete observation> | <action> |

Progress return: <phase, concrete result, dependency/blocker and next action at meaningful milestones>

## Candidate return

- Worker status: <proposed / unverified / ready-for-integration / blocked / deferred (references/work-contract.md#status)>
- Changed artifacts: <absolute paths; relevant revision/hashes>
- Addressed / unresolved finding IDs: <IDs and material caveats>
- Checks actually run: <check, observed result, receipt path, evidence scope>
- Checks not run and why: <specific gaps>
- Integration dependencies/conflicts: <facts or none observed>
- Remaining budget and next parent action: <bounded follow-up>

## Parent integration receipt

<!-- Parent fills this after checking the actual current result; author checks do not establish independent verification. -->

- Integrated revision/artifacts: <current identity>
- Criteria checked and evidence: <receipt paths; pass/fail/unknown>
- Gate edits: <none detected / N listed, M read, K findings / partial / unavailable>
- Final item state: <verified with evidence-ladder level / needs-repair / blocked / deferred>
- Remaining acceptance: <runtime, target device, publication, owner aesthetic or other relevant limits>
