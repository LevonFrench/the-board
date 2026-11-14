# Subject kinds

Set `subject_kind` in `fieldbook.config.yml`. The kind decides the proof chain, the tracks and the decision card. Evidence labels, ledgers, registers and checks are the same for every kind. Mixed subjects pick the kind of the decision being made.

| Kind | Examples | Default output | External research |
|---|---|---|---|
| `market` | City, region, vertical, opportunity scan | `both` | Yes, by track |
| `household` | House, renovation, a large purchase | `both` | Gaps only |
| `project-state` | Game, app, company project | `both` | Often none |
| `entity` | Company or person dossier, competitor study | `single-file` | Yes, primary first |
| `archive` | Artist, game series, collection | `both` | Gaps only |

Decision cards are Markdown pages under `topics/`, such as `topics/decisions.md`, so they reach the reader.

## `market`

```text
Public source → evidence record → bounded finding → business hypothesis
              → buyer interview → paid pilot → repeat/stop decision
```

Tracks, run only those that help the decision: market and geography; workforce and institutions; commerce and channels; digital competition; sector modules; social evidence; business briefs.

Business brief card:

| Field | Purpose |
|---|---|
| First buyer | Who can say yes? |
| Smallest paid offer | What changes hands in 14–30 days? |
| Cost to serve | `none yet`, `national-benchmark`, `local-quoted` or `observed` |
| Price evidence | Same states. `none yet` is shown, not hidden |
| Evidence limit | What is still only a public signal? |
| Boundary | What role is excluded, and who is the authorized party? |
| 30-day work | How will learning happen? |
| 90-day gate | What advances it? |
| Stop rule | What ends or narrows it? |

Full template: [research-and-evidence.md](research-and-evidence.md).

## `household`

```text
Source → finding → option → quote or inspection → spend gate → do / re-scope / stop
```

Tracks follow the projects being decided: one per project, plus the property or item record, permits and licensing, and the resale or value effect when it bears on the decision. Owner-supplied records are often the best evidence. Log each with its date and privacy limit, and expect late records to reopen earlier pages.

Decision card:

| Field | Purpose |
|---|---|
| Decision owner | Who chooses? |
| Options | Do it yourself, hire, defer, sell as-is, or the real alternatives |
| Licensed or permitted party | Who must do or sign this work? |
| Test-first step | The cheapest thing that reduces the uncertainty |
| Cost band per option | Each band with its basis; `allowance, unsourced` when there is none |
| Gate before spending | What must be true first? |
| Stop or re-scope rule | What changes the plan? |

Keep one budget. If two views of cost exist, reconcile them or label what differs. Not advice: a licensed trade, inspector or agent still decides what is theirs.

## `project-state`

```text
Project record → stated status → gate → engine or runtime check → player or user check → decision
```

Tracks: current state, architecture, gates and boundaries, product direction, assets. Market tracks and business briefs do not apply unless the project is seeking a buyer. Project records change fast, so run the reconcile step before saying what is current.

Label each built claim with its highest state reached and never a higher one:

`owner-adopted`, `proposal-held`, `designed`, `accepted-leaf`, `composed`, `runtime-verified`, `player-verified`, `unknown`.

Designed is not verified, and verified is not built. Record how each count was taken so it can be repeated; "280 files" with no scope cannot be checked later.

Gate card, one per decision:

```text
CHECK: what is being tested
EXPECT: the exact result that passes, from a live command or observation
EVIDENCE: dated result, revision and artifact
ABANDON: what result ends this path
```

An EXPECT with a typed count goes stale; prefer a command the reader can run.

## `entity`

```text
Source → attributed claim → labelled inference → open question → who could settle it
```

Tracks: corporate record, people in role, money and deals, reputation and risk, market context. A single self-contained HTML is the usual deliverable, carrying the same labels and source IDs as its Markdown record.

Dossier card:

| Field | Purpose |
|---|---|
| Question | What does the owner need to decide about this entity? |
| Known | Attributed claims with date and source |
| Inferred | Named as inference |
| Not found | With the boundary searched |
| What would settle it | The record or person who could answer |

People: role and public business facts. No phone numbers, tax IDs, home addresses or personal biography unless the owner asked for a specific public record, and footers must match what the page does. Legal records state their status and date; an allegation stays an allegation. Dossiers age quickly: date them, and treat any past-due milestone as a refresh item.

## `archive`

```text
Local artifact or primary source → attributed claim → corroboration → contested or settled → reading route
```

Tracks: history, works and credits, people, releases or catalog, technology or craft. Cross-check consequential credits, dates and hardware facts across two independent source classes; otherwise label a source claim. Keep contradictions in a note rather than forcing a tidy timeline. Copyrighted or restricted material is described and linked, never copied wholesale.

Reference card: reading route, what is settled, what is contested, what is unknown, next source class to try.
