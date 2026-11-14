# Evidence return

Use this template to return a local wiki lookup to the owning Agency session. It is a report format, not a wiki write request.

```text
Assignment/item ID:
Owning session / return channel:
Project root, checkout and revision:
Question and selected wiki scope:
Authorization mode for this work:
Retrieval route (MCP tool or CLI command) and date:
Overall status: ok | partial | no_match | unavailable | error
Errors[]:
Judge: mode=off; status=not_run

Evidence candidate:
  Wiki slug:
  Canonical absolute path:
  Physical lines (YAML frontmatter included):
  File SHA-256:
  Excerpt SHA-256:
  Updated:
  Verified:
  Source URLs:
  Truncated: true | false
  Exact excerpt:

Finding or task claim this evidence informs:
What the excerpt establishes:
What it does not establish / applicability limits:
Conflicts, stale or unknown fields:
Gap or next authorized research question:
Parent verification needed:
Proposed brief upkeep, if material:
Files changed by lookup: none (read-only)
```

Include one `Evidence candidate` block per returned candidate. Preserve exact source text and physical lines; do not paraphrase inside the excerpt field. Do not report a finding as verified from a KB citation alone. The parent owns triage, source/code checks, authorized wiki changes and integration.

## Retrieval

Retrieve through a knowledge-base tool, when you have one, as described in [knowledge-workflow.md](../references/knowledge-workflow.md), which also defines the status values and candidate fields above. A stale expected hash requires a fresh lookup, not reuse of the old excerpt. This packet does not establish a running connector, hosted call permission, source freshness, article truth or implementation acceptance.
