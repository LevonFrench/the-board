# Usage gate

Every Agency run checks the owner's allowance at fixed points and obeys the answer. The thresholds are: tell the owner when the weekly total reaches 75% or this run has used 25 points; wrap up at 90%; stop at 100%, or when a credit balance starts falling. [usage_gate.py](../scripts/usage_gate.py) turns a reading into an action. Change the numbers at the top of that script to match your own limits.

## When the check runs

The coordinator runs it:
- before a loop starts, after stating its purpose and acceptance check, and writes the start reading into the run state;
- at every round boundary;
- before each new worker is dispatched;
- before a multi-agent fan-out, once for the whole fan-out.

A one-shot task with no loop and no workers checks once at the start.

## Who reads the meter

The coordinator, never a worker.
- Claude Code desktop: call `mcp__ccd_session_mgmt__get_usage` (load it through ToolSearch if deferred), save the JSON to a file in the run folder or pipe it in, and run `python -B scripts/usage_gate.py --claude <file|-> --state <run folder>/usage-state.json --log <run folder>/usage.log --at "<checkpoint>"`.
- Codex: read `rate_limits.primary.used_percent` and `credits.balance` from the latest `token_count` event in the current rollout file under `~/.codex/sessions`, then run `usage_gate.py --weekly <percent> --balance <balance>` with the same state and log flags. A JSON file holding those two fields also works with `--codex <file>`.
- Headless `claude -p` or a plain subagent with no usage tool: the coordinator passes in a reading it has, or asks the owner for the weekly percent and runs `usage_gate.py --weekly N`. It never estimates one.

The gate uses the "all models" weekly window from a Claude reading, and the highest weekly window if that one is missing.

**One-model windows.** A Claude reading can also carry a weekly window for one model, such as "Weekly · Fable". Sessions on that model stop when it fills, however low the total is. The gate reports the highest such window as `model_window`; pass `--model <name>` to watch the coordinator's own model instead. At the tell number it raises `continue` to `tell-owner`. At the wrap number it sets `handoff_now`, and it never stops other work by itself, because workers on another model are not limited by that window. Why: on 2026-11-11 a coordinator's Fable window read 94% and then 97% while the total read 60%, and the gate said only "tell-owner, run +52".

The state file holds the start reading and start credit balance, which is how "this run used N points" and "the balance has started falling" are computed. A Claude reading carries no credit balance, so only a Codex reading can trigger the falling-balance stop.

## What each action means

| Action | Exit | The run |
|---|---|---|
| `continue` | 0 | Carries on. |
| `tell-owner` | 0 | Carries on, and the owner is told the reading in the next message, at this round boundary. |
| any action with `handoff_now` | as the action | Also writes the handoff at this boundary, before any new dispatch, and tells the owner which model's window is nearly full. The run may go on. |
| `wrap-up` | 1 | Finishes the current item only. Starts no new item, worker or round. Writes a handoff and asks the owner before continuing. |
| `stop` | 1 | Stops now. No new worker, no new round, no spending of paid credits or overage. Writes the handoff and reports. Only the owner can lift it, in chat, for this run. |
| `ask-owner` | 1 | There is no usable reading (usage tool unavailable or not applicable). Asks the owner for the weekly percent before starting new work. Never guesses. |
| exit 2 | 2 | Bad usage or an unreadable reading. Fix the call or ask the owner for the reading, then run again. |

**An owner override.** When the owner lifts the stops for a run, record their words and the time in the run log. The override covers that run only and ends with it. Keep taking the reading at every checkpoint and record it as overridden by the owner: the gate does not go silent.

An agent never edits a usage guard or its state, and never suggests a way round one.

## The run record line

The run record carries one line per non-`continue` check, taken from the gate's `record_line`, for example `Usage: tell-owner at round 2, weekly 87%, run +12`. A run that ended on `wrap-up` or `stop` also records the handoff's full path. The gate's `--log` file holds every check, one JSON line each, for the audit.

## Handoff

On `wrap-up`, `stop` or `handoff_now` the handoff names what is done, what is half done, what the next step is, the reading, and the full paths of the run folder, state and log. The coordinator writes it, or dispatches the [usage steward](../roles/general/usage-steward.md) to draft it.

**Work that outlives the coordinator.** If the owner has workers or sessions keep going after the coordinator may stop, the handoff lists each one, the return it will write, and the checks the next session runs on that return. Every such return is unverified until someone runs them. The handoff also says how to keep a coordinator: another model in the same session, or a new session pointed at the handoff.
