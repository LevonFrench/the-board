---
name: document-evidence
description: Turn authorized difficult documents into page-traceable checked extraction and an evidence-aware research handoff, with native text first and conditional OCR or wiki compilation.
---

# Document Evidence

**Conditional:** never exercised on a real project, and the OCR backend it can escalate to is not installed. Native extraction works; OCR steps end in a visible blocker until a runtime is established.

## Use when

An authorized answer or ingestion depends on scanned pages, complex reading order, tables/formulas or inconsistent extraction. The [Document Extraction Reviewer](../../roles/general/document-extraction-reviewer.md) owns transcription; the existing research/wiki owner owns source claims and compilation.

## Not for

Documents that ordinary extraction handles reliably, automatic installs/downloads, or document uploads.

## Inputs

Authorized source identity, page count, needed claims/fields, a task-owned input/output/temp location, and the available document/PDF tools (load their skill).

## Work

1. Establish an extraction baseline with available tools; compare native extraction with rendered pages.
2. Escalate only affected pages to an available in-scope OCR route under the role's OCR boundary. Missing runtime or unknown model identity leaves a visible blocker and a usable partial extraction.
3. Preserve raw output, normalized output, transformation notes and the page map. Mark every in-scope page **complete**, **failed** or **review-required**, with explicit exclusions. Check task-critical numbers/identifiers and used excerpts against page images; keep table cell/header associations and uncertain spans.
4. Hand checked evidence to the research owner with exact page anchors, uncertainty and limits. Source authority, provenance, independence and claim support are assessed separately from transcription accuracy.
5. Compile only when the task calls for KB mutation: load the wiki skill and your own wiki rules, if you keep any, query first, follow normal retention/batching, and run the wiki's lint after mutations. Cross-project knowledge lives in its hub topic.

## Output

The [extraction package and ledgers](../../assets/workflows/document-evidence.template.md) with the [work-item packet](../../assets/workflows/work-item.template.md): source/hash, page map, raw/normalized paths, page-status/uncertainty/table ledgers, checked-source handoff and actual resource/QA receipts. Full paths and page identifiers survive later summaries.

## Acceptance

No uncertain or failed page silently becomes complete knowledge through summarization. Single-page success does not establish joint multi-page parsing. The eight-page synthetic fixture is a conditional pilot against manual ground truth.

## Return

To the parent under the [work contract](../work-contract.md) with a [status](../work-contract.md#status), unresolved pages, claims, checks not run and remaining budget. The parent verifies the handoff; downstream research/wiki acceptance is stated separately.
