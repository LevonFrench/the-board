# Fieldbook Site and Knowledge-Base Design

## Local static endpoint (required for a local Fieldbook)

For a local or private Fieldbook, ship a direct-open static reader alongside the Markdown research layer:

```text
fieldbook/
├── index.html          # file-openable entry; redirect + ordinary fallback link
├── README.md           # canonical Markdown start page
├── source-ledger.md    # canonical evidence record
├── topics/             # canonical compiled topics
└── site/
    ├── index.html      # reader UI
    └── styles.css      # relative local styling/assets only
```

The root endpoint and reader must work when opened from disk. Do not rely on a framework dev server, API, CDN, analytics tag, remote font, or public deployment. Use relative Markdown links so a reader can move from a summary to the underlying evidence. Mark private readers clearly; never expose internal absolute paths or restricted source data.

The reader should be legible to a partner who has not read the repository: provide a start-here card, topic anchors, evidence/gap/source routes, a visible update date, and concise caveat states. Markdown remains canonical; if a detailed claim cannot be traced to its Markdown topic or source ledger, leave it out of the reader.

## Web-app Fieldbooks (`output_mode: web-app`)

A built site is allowed when the owner wants search, filters or dynamic routes, and it needs a dev server or host. It does not replace the Markdown record, and site data carries source IDs that resolve to the ledger. Run the checker with `--site <data dir>` so site-only facts surface. Add a static reader, or record in `editorial-note.md` why none exists.

## Recommended information architecture

```text
Home
├── Best bets / current decision order
│   └── Business brief detail routes
├── Market map: population, geography, workforce, commerce
├── Sector modules: AI, delivery, drones, real estate, social signals
├── Original opportunity library: supporting hypotheses
├── Audits and rosters: websites, restaurant/order paths, providers, realtors
├── Research ledger: completed work and highest-priority gaps
├── Sources: searchable primary-source index
└── Review log: critic findings, applied corrections, remaining limits
```

Use distinct labels for distinct page purposes:

- **Market map**: what exists, where, and under what limits.
- **Business brief**: a buyer/offer/gate/stop-rule hypothesis.
- **Best bet**: the current qualitative decision order.
- **Original library**: prior or supporting hypothesis matrix.
- **Evidence page**: source records, research method, and refresh backlog.

## Home-page decision map

Above the fold, link to a single canonical path. A compact orientation block should answer:

1. **Decide:** Where is the current recommended sequence?
2. **Validate:** Where are the alternatives and their gates?
3. **Verify:** Where do sources, caveats, and research gaps live?

Do not give every hub the same visual priority. A partner should find the current 90-day decision in under one minute.

## Decision cards

Use the card for the subject kind in [subject-kinds.md](subject-kinds.md). For `market`, every business-detail page should show, near the top:

| Field | Purpose |
|---|---|
| First buyer | Who can say yes? |
| Smallest paid offer | What changes hands? |
| Cost to serve, price evidence | `none yet`, `national-benchmark`, `local-quoted` or `observed` |
| Evidence limit | What is still only a public signal? |
| Boundary | What role is excluded? |
| 30-day work | How will learning happen? |
| 90-day gate | What advances it? |
| Stop rule | What ends or narrows it? |

Use shared card components and data objects for consistent brief families. Do not hard-code repeated caveat copy across many pages if a reusable component or schema can prevent drift.

## Roster and audit UI

For long lists, provide:

- full-text search;
- category/model/status filters;
- result count with live announcement;
- source/evidence label on each record;
- direct official-site and evidence links;
- “unknown/not checked” as a first-class state;
- a detail page or expandable record for depth.

For a calculator: out-of-range input shows a visible error and suppresses outputs, never a silent clamp; name whose perspective it takes (client or agency); show pass-through costs apart from fees.

For screenshots, identify capture date, page type, actual URL, and whether two image cards came from the same route. Never make a cropped visual look like independent evidence.

## Editorial rules

- Use short, declarative headings. Explain specialized words before relying on them.
- Put one decision rule high on the page; move repeated legal/uncertainty prose into compact boundary blocks.
- Keep citations readable: source ID plus publisher/title in a drawer, card, or source index.
- Explain connections across modules. For example: merchant conversion can be the commercial wedge; social is the acquisition channel; delivery is later operating architecture.
- Treat dated source records as research artifacts, not permanent truth.

## Local knowledge-base protocol

When a `.wiki` exists:

```text
raw/       immutable captures and source notes
wiki/      compiled living topics
output/    partner briefs, audit reports, synthesis documents
_index.md  navigational cache and counts
log.md     append-only activity record
```

- Never silently overwrite raw evidence to fix a conclusion.
- Correct compiled topics and add an output/editorial report that names the change.
- Update affected index dates and summaries; generate output counts by script rather than typing them.
- A Fieldbook beside a wiki lives at `<topic>/output/projects/<slug>/` and cites its articles; it keeps no parallel compiled tree. Run the checker with `--canonical <topic>`.
- Keep a durable session checkpoint and append-only events when using the wiki workflow.
- Write cross-topic relationships in both Obsidian wikilink and regular Markdown-link form.

## Content data model

Prefer typed objects or records over page-only prose. A useful generic model:

```ts
type Brief = {
  slug: string;
  title: string;
  mode: "Local-first" | "Remote-first" | "Hybrid";
  tier: "test-now" | "queue" | "hold";
  tierReason: string;
  buyer: string;
  offer: string;
  thesis: string;
  costToServe: EvidenceState;
  priceEvidence: EvidenceState;
  evidenceLimit: string;
  boundary: string;
  first30: string[];
  gate90: string;
  killRule: string;
  sourceIds: string[];
  related: { label: string; href: string; detail: string }[];
};
```

`EvidenceState` is `"none yet" | "national-benchmark" | "local-quoted" | "observed"`; show `none yet`, do not hide it. Metric definitions carry a `notThis` field saying what they do not measure.

Do not store a 1-to-N order: one book's order kept reading as a ranking through four passes. Every row links a topic and its coverage status, or says `unresearched placeholder`.
