---
name: visibility-measurement
description: Design an evidence-linked AI-answer visibility panel using target-blind unaided prompt generation, contamination checks, separate aided denominators and a bounded future measurement plan.
---

# Visibility Measurement

**Conditional:** never exercised on a real project; treat the first use as a pilot.

## Use when

A concrete decision concerns a product's appearance in AI answers. The existing research/measurement lead owns the design. Produces a measurement plan and provisional panel.

## Not for

Running models, accessing accounts, publishing content or scheduling monitoring (existing explicit measurement authority can support a separate bounded run item), or simulated audience reactions presented as observed demand ([Audience Lab](audience-lab.md) is a different question).

## Inputs

The decision, target population, market side, geography/language, time window, model/retrieval/consumer surfaces and budget; real buyer-language/job evidence with source IDs and limitations.

## Work

1. State the outcome definition and denominator before prompts. Keep strategic-priority weights distinct from evidenced exposure/frequency weights. Unsupported structural cells stay provisional or quarantined.
2. Write a separate target-free generation brief with only justified category, audience/jobs and buyer language: no target name, aliases, URLs, campaign phrasing, marketing claims, current performance or unique clues. Keep the target key and contaminated controls outside it.
3. For unaided generation use a fresh-context worker only when delegation is available and authorized, passing solely the sanitized brief and permitted evidence; never fork target-bearing history. Without a target-free context, label output **unblinded draft**; telling a context to forget the target is insufficient.
4. QA prompts against the target/campaign key, evidence, realism and duplicates; leakage fails the unaided lane. Similarity nominates duplicates for judgment, not deletion. Use pass/revise/quarantine/reject with reasons.
5. Define aided and unaided lanes with separate counts and denominators; freeze prompt text/panel version, eligibility rules, weights and surface assumptions before a run, with an explicit accounting rule for missing outputs and failed runs.
6. Propose repeat runs, a variance pilot, actual-version/time records, budget/stop conditions and an analysis plan fit for the intended claim.

## Output

The [panel design, sanitized brief and QA ledger](../../assets/workflows/visibility-measurement.template.md), with a [work-item packet](../../assets/workflows/work-item.template.md) for a bounded generation/QA/run assignment; sanitized brief saved separately from target-bearing QA material. Prompt-to-evidence traceability, lane/denominator definitions, weighting rationale, contamination and duplicate decisions, blinding evidence/limits, version and run plan.

## Acceptance

The dispatch payload itself is checked for leakage. A small structural fixture is **provisional_directional**, not validated measurement; a useful paper pilot has six evidenced structural cells and two intentionally contaminated controls that fail unaided QA and stay outside counts. Mentions do not establish revenue, share or demand. Method provenance and limitations.

## Return

To the parent under the [work contract](../work-contract.md) with a [status](../work-contract.md#status); bounded repairs use the [improvement loop](../improvement-loop.md). Live measurements and observed variance need their own evidence.
