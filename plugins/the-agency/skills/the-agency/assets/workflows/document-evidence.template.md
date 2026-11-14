# Checked extraction package: <document>

- Item/parent packet: <stable ID; absolute packet path>
- Authorized source: <absolute path; hash; page count and identity>
- Task-critical fields/excerpts: <what must be exact>
- Assigned input/output/temp paths: <absolute paths>
- Extractor/backend identity and mode: <version/model; native / single-page / joint multi-page>
- Page/resource/attempt budget and stop condition: <finite limits>
- Raw / normalized output and transformation notes: <separate absolute paths>

## Page inventory and QA

<!-- Include every page in scope, even empty/failed pages; explicitly record scope exclusions. -->

| File-page index | Printed label | Raw / normalized / page-image paths | Native/OCR route and reason | Complete / failed / review-required | QA evidence and remaining issue |
|---|---|---|---|---|---|
| <index; state indexing convention> | <label or none> | <absolute paths> | <route> | <status> | <check/uncertainty> |

Out-of-scope pages and reason: <page IDs or none>

## Excerpts, fields and uncertain spans

| Evidence ID | Source page and region/span | Raw text/value | Normalized text/value and transformation | Checked / uncertain | Check receipt or unresolved alternatives |
|---|---|---|---|---|---|
| <E-ID> | <page; region> | <exact transcription> | <preserve meaning and identity> | <state> | <evidence; do not guess> |

## Table / reading-order mapping

| Table/block ID | Page(s) and source region | Header / row / column or sequence mapping | Normalized artifact | Checked associations / remaining ambiguity |
|---|---|---|---|---|
| <ID> | <page and region> | <explicit relationships> | <absolute path> | <QA result> |

## Runtime and package receipt

- OCR prerequisites, if used: <isolated runtime, actual model/process identity, loopback binding evidence before input>
- Actual per-page latency/resource/error measurements: <method and results or unavailable; clean/difficult pages separate>
- Truncation/repetition/partial streams: <page IDs and resolution>
- Temporary files/process cleanup: <task-owned paths/processes and actual state; retained evidence>
- Claim handoff: <accepted evidence IDs; research owner; source-truth limits and unresolved pages>
- Wiki destination/compilation, only if requested: <registered absolute wiki path; source notes; actual lint receipts or not performed>
- Return: <worker status; addressed/unresolved IDs; checks run/not run; dependencies; remaining budget; next parent check>
