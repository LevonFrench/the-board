# Reviewer brief template

Fill the `{…}` fields and hand this to each reviewer as its complete task. It must stand alone: the reviewer has not seen the conversation.

```text
Adopt the persona defined in {persona_path}. Read it first and work in that role{role_adaptation}.

Project: {one-paragraph project summary: what it is, stage (idea/design/prototype/production/live), stack/engine/platform, team size}.
The owner wants a critical review whose goal is improvement, written up as a detailed report.

Read in full: {primary target files}.
{Decision-status note, e.g. "The doc separates confirmed owner decisions from proposals. Do not argue against confirmed decisions unless you see a serious problem, and label that pushback clearly."}
Optional read-only context: {KB articles, related docs, manifests, code paths}.

Your focus: {5-10 concrete questions/areas specific to this persona AND this project}.
{Persona-specific deliverable, e.g. "Propose a concrete first arena with dimensions" / "Include ASCII wireframes" / "Model three rounds numerically".}

Write your report to {output_dir}/{slug}.md with these sections:
1. Verdict (3-5 sentences)
2. Strengths worth keeping
3. Problems and risks, ranked most severe first; each cites the file/section, explains the concrete failure scenario, and proposes a fix
4. Missing pieces
5. Concrete recommendations (numbered, actionable, each marked "now" or "later")
6. Questions only the owner can answer

Rules: be specific and critical, not generic; no filler or praise padding. Cite sections/lines. Do NOT edit any file other than your report. {Web research allowed/not needed.} Use full absolute paths. Keep it under ~{word_limit} words. Reply with a 5-line summary of your top findings when done.
```

## SUMMARY.md structure (written by the orchestrator, not a reviewer)

```markdown
# {Project} — agency review {YYYY-MM-DD}

Target: {files}. Reviewers: {n} ({list with persona file names}).

## Top findings (consensus first)
| # | Finding | Raised by | Severity | Suggested action |

## Where reviewers disagree
- {topic}: {reviewer A} says …; {reviewer B} says …. Recommendation: …

## Prioritised action list
1. … (now) — source reports: …

## Questions for the owner (deduplicated)
- …

## Reports
- [{persona}]({absolute path}) — one-line verdict
```
