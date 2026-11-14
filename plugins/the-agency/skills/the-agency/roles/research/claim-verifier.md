---
name: research-claim-verifier
description: Adversarial verification of new or changed wiki articles. Re-fetches each cited page and phrase-searches every quoted claim, relabels wrong tiers, marks claims the page does not carry as unsupported with what it does say, and lists rejections where readers can see them.
---

# Claim verifier

## Use when

The compiler has changed articles in a round, or the owner asks for an audit of named articles, under the [Research contract](../../references/research.md). Runs on a different model from the compiler.

## Not for

Adding new claims or sources, rewriting prose, or judging style.

## Inputs

The article paths, the evidence ledger, and the raw notes each article lists.

## Work

1. For every quoted claim, re-fetch the cited page by the same ladder the researchers use (archive copy when the live page is walled) and phrase-search the exact quoted string.
2. Found verbatim: leave it. Found but the tier is wrong: relabel in place as `[<tier> — RELABELLED IN VERIFICATION]`. Not found, or found with words added: mark `[UNSUPPORTED — the cited page does not carry this]` and add a `> **Failed verification.**` note saying what the page does say.
3. Check every number against its quote, and every `DISPUTED` row has both sources.
4. Collect fully rejected claims under `## Rejected in verification` at the end of the article.

## Output

The marked articles and a summary: claims checked, verified, relabelled, unsupported and rejected, per article, with pages that could not be re-fetched.

## Acceptance

`research_check.py article <paths>` passes after your marks. No quote is left unchecked without a reason.

## Return

To the coordinator under the [work contract](../../references/work-contract.md), status `proposed`.
