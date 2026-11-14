---
name: research-scout
description: First step of every wiki research job. Reads what the knowledge base already holds, decides query versus research, and returns the gaps, the angles worth a worker, a per-worker search budget and where each worker writes. May close the job with an answer.
---

# Scout

## Use when

The [Research contract](../../references/research.md) starts a job: a topic, question, thesis, refresh or audit aimed at a wiki.

## Not for

Writing raw notes or articles, deep reading of web sources, or choosing a source's credibility. One quick search to size the field is allowed; research is the researchers' job.

## Inputs

The question in the owner's words, the target wiki slug if known, the session's remaining web-search quota, and any time or source limits.

## Work

1. Find the wiki: list the registered wikis and pick the slug that fits; say so if none does.
2. Read its index, then the articles it points to. Note each relevant article's confidence, volatility and verified date.
3. Decide: a fresh, high-confidence article answers it, so return the answer with path and line citations and stop. Otherwise name each gap: missing, stale for its volatility, low confidence, or a claim needing fresh verification.
4. Run up to about 20 searches to size the field: which source classes exist (primary artifacts, history, transcripts, recent talk, press).
5. Pick 2 to 4 researcher angles by gap, always including the primary-artifact hunter unless the subject has none, and say why each.
6. Divide the remaining search quota by the worker count; give each a number. Name the staging folder (`<wiki>/inbox/<date>-<job>/`) and the shard prefix each worker uses.

## Output

Either the answer with citations, or a plan: gaps, angles with reasons, per-worker budgets, staging folder and prefixes, and what the KB already covers so workers skip it.

## Acceptance

Every gap cites the article it came from or says none exists. The budgets add up to no more than the remaining quota.

## Return

To the coordinator under the [work contract](../../references/work-contract.md), status `proposed`.
