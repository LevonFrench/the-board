# Select a workflow and an accountable owner

Load when a deliverable matches one of the triggers below. Load one matching contract, not the collection; combine stages only when the task genuinely spans them, keeping one parent and one owner per deliverable. Workflows are local instructions and templates; optional upstream executables have separate readiness.

| Task trigger | Contract | Owner and useful capability | State |
|---|---|---|---|
| Prepare a task from KB evidence, check a review claim, or find a knowledge gap | [Local knowledge workflow](knowledge-workflow.md) | Owning session; deterministic lookup first, a researcher only for an authorized gap | in use |
| Substantial feature, unclear current behavior, or an implementation handoff | [Delivery Contract](workflows/delivery-contract.md) | Existing architect/implementation lead; optional architecture map only for a real question | paper pilot |
| New interface or a concrete design/usability improvement | [Product Design](workflows/product-design.md) | Existing UI Designer/UX Architect and finish reviewer; [design reference retrieval](design-tool.md) when useful | paper pilot |
| Add or materially change a skill, tool or plugin | [Capability Intake](workflows/capability-intake.md) | [Capability Curator](../roles/general/capability-curator.md); security expertise for consequential findings | paper pilot |
| See what changed in the repos these skills came from, or bring in new upstream features | [Upstream Sync](workflows/upstream-sync.md) | Parent; [Capability Curator](../roles/general/capability-curator.md) for a material change |
| Offer/copy/product decision with first-party customer evidence | [Audience Lab](workflows/audience-lab.md) | Existing research/marketing lead | paper pilot |
| Difficult scanned/document content needs reliable extraction | [Document Evidence](workflows/document-evidence.md) | [Document Extraction Reviewer](../roles/general/document-extraction-reviewer.md); native extraction first | **conditional**: never run on a real project; OCR backend not installed |
| Existing discovery lead may support educational or public-facing work | [Editorial Opportunity](workflows/editorial-opportunity.md) | Existing research/editorial lead; the project's discovery and claim records | **conditional**: never run on a real project |
| Defined business question about presence in AI answers | [Visibility Measurement](workflows/visibility-measurement.md) | Existing research/measurement lead; target-blind worker when justified | **conditional**: never run on a real project |

"Paper pilot" means fixture cases in the author's build notes (not included), not real-project acceptance. A **conditional** workflow may be used, but say so in the assignment, treat the first real use as a pilot and expect its optional tooling to be absent.

For Roblox work load the [Roblox division](roblox.md) first, then a shared workflow only if it adds structure. Roblox Studio/device/service acceptance cannot be replaced by web UI recipes or source-only checks.

## How roles and workflows run

Roles live under roles (catalog kind `role`); workflows here under `workflows/` (kind `workflow`). Neither is a second router or a background agent: The Agency reads the selected file, adds a [work contract](work-contract.md) brief and dispatches it through the host's native workers, or applies it sequentially and labels that. Harness details: [harnesses.md](harnesses.md). Read the full candidate and its required overlay before dispatch; do not bypass the Roblox adapter with an unsafe upstream persona example.

## Dependencies and scope

Keep three readiness questions separate: can the brief be read, can its optional tool execute, and has the outcome been verified? SkillSpector, Unlimited-OCR and Understand Anything remain optional backends needing environment and behavior checks; never invoke their installers, hooks, account checks or whole-repo pipelines because a workflow mentions them. Adapted methods do not call their originals; human-only upstream skills stay human-invoked. Existing task authorization governs; do not add a confirmation step for an already authorized local edit or trial.
