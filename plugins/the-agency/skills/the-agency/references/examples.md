# Worked examples

Load when unsure how to size or route a case. These are illustrative, not templates: size and route from the actual request. Each shows triage, team (sizing from [SKILL.md](../SKILL.md#select-the-team)), what to load and what comes back. Status words and evidence levels follow [work-contract.md](work-contract.md).

## 1. Web app bug fix — act directly

Request: "The settings page throws on save when the display name is empty; fix it."
- Triage: narrow, single discipline. If The Agency was invoked anyway, say so and act directly.
- Team: 0 workers. Loads: none beyond SKILL.md; the project's own test instructions.
- Work: reproduce with a command that shows the symptom, localize (scientific-method only if several causes fit), smallest fix, add or run the relevant test.
- Output: changed files, test receipt (ladder level 2), whether a browser check (level 3) was run. No AGENCY.md change unless the brief is missing and this is the first substantial write.

## 2. Godot or Unity game review — two lenses, report-only

Request: "Have The Agency review our Godot platformer's movement and onboarding; findings only."
- Triage: multi-discipline review, read-only mode.
- Team: 2 read-heavy workers with different briefs — gameplay/engine (for Godot or Unity, studio-experts' picker and safety overlay) and UX/onboarding (an agency-review persona) — plus the coordinator's skeptical check. No implementer.
- Loads: routing.md; persona and skill files of the finalists.
- Output: `docs/reviews/<date>-agency/` with assignment, two reports, SUMMARY.md; findings `proposed`, each with exact file lines and a confirming check. Runtime feel stays unverified unless the game was actually run.

## 3. Roblox purchase flow — coordinated review and fix

Request: "Our developer-product handler sometimes double-grants; coordinate a fix and verify it."
- Triage: consequential persistence/commerce change, implementation authorized.
- Team: systems engineer (writer), persistence-commerce reviewer (distinct failure-mode review), QA and release evidence as verifier. Three roles, one writer.
- Loads: routing.md → [roblox.md](roblox.md) (contract with every role); [creator-docs-helper.md](creator-docs-helper.md) for exact API lookups; pre-mortem from [method-lenses.md](method-lenses.md) before commit.
- Output: state-transition table, the change, duplicate-receipt and interruption fault-test results (level 2), Studio/test-service evidence only if actually run. The parent marks `verified` only after its own check; no Robux is spent.

## 4. Fieldbook with fan-out — Fieldbook division

Request: "Fan out agents and build a Fieldbook on whether a mobile detailing business could work in a small town. Local only."
- Triage: team wanted, research plus build. Without the fan-out request this is the `fieldbook` skill alone.
- Team: parent writes the config and guidance; 3 track researchers (market, competitors, regulation) in the first round; compiler; decision analyst; reader builder; accuracy verifier, clarity critic and strategy critic read-only; release steward. Cheap researchers, one writer per file set.
- Loads: routing.md → [fieldbook.md](fieldbook.md) (contract with every role); <fieldbook skill>/SKILL.md and its `market` card; wiki query first.
- Output: Markdown Fieldbook plus a generated reader at `<root>/index.html`; `check_fieldbook.py --release` receipt (level 2); reader opened from disk (level 3) if a browser ran; decision cards stay `proposed`; nothing published. Interviews and pilots remain the owner's.

## 5. Status question — brief and KB only

Request: "Where does the project stand and what is next?"
- Triage: status question. Team: 0 workers.
- Loads: AGENCY.md, HANDOFF.md; `agency_kb` `read_index` → `read_article` for linked master articles only if the brief does not answer.
- Output: short answer with absolute paths, the brief's last-verified date, and any brief-vs-source disagreement found (map-territory). No writes.

## 6. Broad multi-discipline review with fixes — full loop

Request: "Run The Agency over the app: UX, security and performance; fix what is clearly wrong and verify."
- Triage: team plus review-fix-verify loop, implementation authorized.
- Team: 3 differently briefed reviewers in parallel (UX, security, performance); then one writer per disjoint file set; one independent verifier for consequential fixes.
- Loads: routing.md, [work-contract.md](work-contract.md), [improvement-loop.md](improvement-loop.md), [loop-prompts.md](loop-prompts.md); [workflow-routing.md](workflow-routing.md) only if a deliverable matches a workflow (Product Design for an interface change).
- Output: triaged item list with IDs; per item `ready-for-integration` from workers and `verified` from the parent with ladder levels; deferred items and owner decisions in SUMMARY.md; AGENCY.md updated only for material changes.

## 7. Finished piece with several media types — Media division

Request: "Make a 60-second promo: rendered shots, narration, a music bed and foley, mixed together. Run it as a team."
- Triage: team wanted, several media types, handoffs and a final mix. One render or a question about what the machine can do would need no team.
- Team: VO director, then the render operator for voice lines; art director for anchors; shot planner; operator for video; footage reviewer; music director; spotter once picture is locked; sound editor; audio reviewer; one mix and delivery. The parent names the authority (here VO) and gets the owner's go for render time.
- Loads: routing.md → [media.md](media.md) (contract with every role); the craft file for each team as it starts; the project's capability snapshot first.
- Output: a job record beside each deliverable, `media_check.py` reports (level 2), sampled-frame reviews reported as sampled, and one short sheet of moments for the owner to hear and watch. Only the owner marks anything `approved`.

## One-line cases

- Early Unity game idea: design/product and UX lenses plus a skeptic; no deployment audit or Blender panel without relevant work.
- Sliding feet after Maya-to-Unity import: route to studio-experts (engine/DCC only); add gameplay only if speed is implicated.
- "Have experts critique this design doc": agency-review directly; The Agency adds nothing without coordination or fixes.
- Implement agreed onboarding fixes: one implementation owner plus a distinct UX check if warranted.
- "Get a team to refresh an older Fieldbook": Fieldbook division, release steward first to reconcile against newer handoffs; a researcher only if a gap needs the web.
- "Add a flooring page to my house Fieldbook": `fieldbook` skill directly; no team.
