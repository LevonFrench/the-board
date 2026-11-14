# Roblox division

Load for any Roblox/Luau target; pass this contract with every role. Roles are local worker briefs, not skills or Studio tools; pick the smallest set. Consequential persistence/commerce changes get a distinct failure-mode review when delegation is available.

| Role | Trigger → result |
|---|---|
| [Experience designer](../roles/roblox/experience-designer.md) | Onboarding, progression → options and a player test |
| [Systems engineer](../roles/roblox/systems-engineer.md) | Luau gameplay, remotes → contract, change, checks |
| [Persistence and commerce](../roles/roblox/persistence-commerce.md) | Saved state, purchases → failure transitions |
| [Input and accessibility](../roles/roblox/input-accessibility.md) | Touch, controller, keyboard → coverage matrix |
| [Replication and performance](../roles/roblox/replication-performance.md) | Streaming, latency → measured hypothesis |
| [QA and release evidence](../roles/roblox/qa-release-evidence.md) | Integration → checked claims, next check |
| [Growth and evidence](../roles/roblox/growth-evidence.md) | Discovery, funnels → bounded experiment |

Load [creator-docs-helper.md](creator-docs-helper.md) when retrieving Creator Docs.

## Shared contract

Start from instructions, the exact experience, its AGENCY.md if present, HANDOFF.md, current source/tests and owner decisions. Upstream personas are question sources: never copy their failed-load/default-save, unchecked-reward or invented-ranking examples. Roles grant no permission to edit, launch, publish, upload, spend, message or change accounts.

- **Data:** absent/new differs from a failed/unknown read; a failed load never becomes writable defaults. Define ownership, schema/version, degraded play and recovery before mutations or purchases.
- **Writes:** name the writer, order rule, overlapping sessions, delayed retries, ambiguous outcomes, shutdown limits and terminal failure. pcall, retries and UpdateAsync alone prove nothing; keep the only recoverable state until it can be safely released.
- **Commerce:** trace receipt identity with award persistence; acknowledge only after the durable award/receipt result. Prompt-close is not fulfilment; never repeat an irreversible grant while resolving ambiguity.
- **Trust:** per consequential client action record server-known identity, permission/state, accepted shape and finite bounds, rate/replay rule, authoritative mutation and rejection. Validate before relaying; restrict recipients; include prompts, detectors and client-owned physics. Proximity/type checks alone are insufficient.
- **Evidence:** label documented platform behaviour, observed project behaviour, anecdote, inference, proposal and unknown. Report checks on the [evidence ladder](work-contract.md#evidence) (Studio = runtime, physical device = target device, test/live service = live) with revision, environment, case and artifact.
- **Execution:** no authentication, licensing, entitlement, credential inspection, marketplace/account flows or migration workarounds. If a launch hits an account, licence or update prompt, report it, never accept it, and continue source work. Leave licence/activation files uninspected. Reading Cloud schemas grants no API access. Follow project Studio ownership.

Source contracts (via the helper; official samples still need tests): data-store best practices, player data and purchasing, developer products, client/server boundary.

