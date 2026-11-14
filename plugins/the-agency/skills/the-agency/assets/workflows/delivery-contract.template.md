# Delivery contract: <feature/change>

- Item/parent packet: <stable ID; absolute work-item path or existing tracker>
- Mode, project and current source: <authority; absolute checkout; revision/hashes>
- User outcome and audience: <who does what, with what observable result>
- Preserved behavior and exclusions: <confirmed decisions and scope limits>
- Glossary: <only ambiguous domain terms>

## Decision map

| Decision ID | Known question / unresolved uncertainty | Evidence and options | Owner / dependency | Choice, rationale and remaining uncertainty |
|---|---|---|---|---|
| <D-ID> | <question> | <source anchors> | <owner / item ID> | <pending or actual decision> |

Decision completion means an evidenced choice; implementation completion requires behavior evidence.

## Behavior specification and coverage

| Requirement ID | Trigger/input | Expected behavior, including relevant failure state | Public check boundary | Evidence owner / slice | Explicit exclusion or evidence gap |
|---|---|---|---|---|---|
| <R-ID> | <trigger> | <observable result> | <boundary> | <owner / item ID> | <none or scoped limit> |

## Dependency-ordered implementation

| Slice ID | Behavior or refactor phase | Depends on | Writable scope / owner | Acceptance criteria IDs | Packet / result artifact |
|---|---|---|---|---|---|
| <S-ID> | <demoable behavior or expand/transition/contract> | <IDs or none> | <absolute paths; owner> | <IDs> | <absolute paths> |

Expand/contract integration point, if needed: <why slices cannot stand alone; final whole-change check>

## Review and evidence

| Review axis | Requirement/standard | Result | Current evidence | Remaining gap |
|---|---|---|---|---|
| Spec compliance | <R-ID> | <pass/fail/unknown> | <receipt> | <gap> |
| Standards compliance | <named applicable standard> | <pass/fail/unknown> | <receipt> | <gap> |

- Tests appropriate to this change: <independent expected outcomes, or inspection rationale>
- Optional map: <question; graph revision; safe input scope; coverage; inferred/dynamic edges; source anchors>
- Return: <worker status; addressed/unresolved IDs; changed artifacts; checks run/not run; remaining budget; next parent check>
- Relevant remaining acceptance: <runtime/device/visual/other, without claiming source checks prove it>
