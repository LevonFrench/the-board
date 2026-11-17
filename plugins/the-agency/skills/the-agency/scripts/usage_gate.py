#!/usr/bin/env python3
"""Usage gate: turns one allowance reading into one action for an Agency run.

  usage_gate.py [--claude <file|-> [--model NAME]] [--codex <file|->] [--weekly N [--balance B]]
                [--state <run-state.json>] [--start] [--log <run-log>] [--at <label>]

Exactly one reading source:
  --claude  the JSON from the desktop app's get_usage tool (file path, or - for stdin)
  --codex   a JSON file with rate_limits.primary.used_percent and credits.balance, as in a Codex token_count event
  --weekly  a weekly percent given by hand (with --balance for a credit balance)

--state names a small run-state file holding the reading at the start of the run. The first check
with a missing file creates it; --start rewrites it. With it, "this run used N points" and "the
credit balance has started falling" can be computed; without it the script says they are unknown.

The thresholds are the constants below. Change them to match your own limits.

Actions, most severe first:
  stop        allowance at 100%, or the credit balance fell since the run started
  wrap-up     weekly total at 90% or more
  tell-owner  weekly total at 75% or more, or this run used 25 points, or one model's weekly
              window at 75% or more
  ask-owner   no usable reading (unavailable, not applicable): never a guessed number
  continue    none of the above

A Claude reading can also carry a weekly window for one model (for example "Weekly · Fable").
Sessions on that model stop when it fills, even while the all-models total is low. The gate
reports the highest such window as model_window, or the one --model names. At 75% it raises
continue to tell-owner. At 90% it also sets handoff_now: write the handoff at this boundary,
because the coordinator may stop before the next one. It never stops other work by itself.

Prints one JSON object. Exit 0 for continue and tell-owner, 1 for wrap-up, stop and ask-owner
(the run must not start new work), 2 for bad usage or an unreadable reading.
"""
import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

TELL_WEEKLY = 75
TELL_RUN_POINTS = 25
WRAP_WEEKLY = 90
STOP_WEEKLY = 100
BALANCE_EPSILON = 1e-6


class UsageError(Exception):
    pass


def percent(value, what):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise UsageError(f"{what} is not a number: {value!r}")
    if value < 0 or value > 100:
        raise UsageError(f"{what} must be between 0 and 100: {value!r}")
    return float(value)


def number(value, what):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise UsageError(f"{what} is not a number: {value!r}")
    return float(value)


def read_json(source):
    try:
        text = sys.stdin.read() if source == "-" else Path(source).read_text(encoding="utf-8-sig")
    except OSError as err:
        raise UsageError(f"cannot read {source}: {err}")
    try:
        return json.loads(text)
    except ValueError as err:
        raise UsageError(f"{source} is not JSON: {err}")


def claude_reading(data):
    """Returns (weekly or None, balance None, note). None weekly means no usable reading."""
    if not isinstance(data, dict):
        raise UsageError("Claude reading must be a JSON object")
    plan = data.get("plan", data)
    if not isinstance(plan, dict):
        raise UsageError("Claude reading has no plan object")
    status = plan.get("status")
    if status != "ok":
        return None, None, f"plan status is {status!r}"
    windows = plan.get("windows")
    if not isinstance(windows, list):
        raise UsageError("Claude reading has no windows list")
    weekly = []
    for window in windows:
        if not isinstance(window, dict):
            continue
        label = str(window.get("label", ""))
        if label.lower().startswith("weekly") and "percentUsed" in window:
            weekly.append((label, percent(window["percentUsed"], f"percentUsed of {label!r}")))
    if not weekly:
        return None, None, "no weekly window in the reading"
    for label, value in weekly:
        if "all models" in label.lower():
            return value, None, f"window {label!r}"
    label, value = max(weekly, key=lambda item: item[1])
    return value, None, f"no all-models window; highest weekly window {label!r}"


def claude_model_window(data, model=None):
    """Returns ((label, percent) or None, note) for a one-model weekly window in a Claude reading.

    With `model`, the highest weekly window whose label names it; without, the highest weekly
    window that is not the all-models one.
    """
    plan = data.get("plan", data) if isinstance(data, dict) else None
    if not isinstance(plan, dict) or plan.get("status") != "ok" or not isinstance(plan.get("windows"), list):
        return None, None
    found = []
    for window in plan["windows"]:
        if not isinstance(window, dict):
            continue
        label = str(window.get("label", ""))
        low = label.lower()
        if low.startswith("weekly") and "all models" not in low and "percentUsed" in window:
            found.append((label, percent(window["percentUsed"], f"percentUsed of {label!r}")))
    if model:
        found = [item for item in found if model.lower() in item[0].lower()]
        if not found:
            return None, f"no weekly window names {model!r}"
    if not found:
        return None, None
    return max(found, key=lambda item: item[1]), None


def model_check(action, reason, window):
    """Adds a one-model window to a decision. Returns (action, reason, handoff_now)."""
    if window is None:
        return action, reason, False
    label, value = window
    if value < TELL_WEEKLY:
        return action, reason, False
    handoff_now = value >= WRAP_WEEKLY
    if handoff_now:
        note = (f"window {label!r} is at {value:g}%, at or over {WRAP_WEEKLY}%: a session on that model may stop "
                "before the next boundary; write the handoff now and tell the owner")
    else:
        note = f"window {label!r} is at {value:g}%, at or over {TELL_WEEKLY}%; tell the owner at this round boundary"
    if action == "continue":
        return "tell-owner", f"{note}; {reason}", handoff_now
    return action, f"{reason}; {note}", handoff_now


def codex_reading(data):
    if not isinstance(data, dict):
        raise UsageError("Codex reading must be a JSON object")
    if "used" in data:
        used, balance = data["used"], data.get("balance")
    else:
        limits = data.get("rate_limits") or {}
        used = (limits.get("primary") or {}).get("used_percent")
        balance = (data.get("credits") or {}).get("balance")
        if used is None:
            raise UsageError("Codex reading has neither 'used' nor rate_limits.primary.used_percent")
    balance = None if balance is None else number(balance, "balance")
    return percent(used, "used"), balance, "codex guard"


def load_state(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except OSError as err:
        raise UsageError(f"cannot read state {path}: {err}")
    except ValueError as err:
        raise UsageError(f"state {path} is not JSON: {err}")
    if not isinstance(data, dict) or "start_weekly" not in data:
        raise UsageError(f"state {path} is not a run-state file")
    return data


def save_state(path, weekly, balance, source):
    state = {"started": datetime.now(timezone.utc).isoformat(timespec="seconds"),
             "source": source, "start_weekly": weekly, "start_balance": balance}
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes((json.dumps(state, indent=2) + "\n").encode("utf-8"))
    return state


def decide(weekly, balance, state):
    """Returns (action, reason, run_points, balance_change)."""
    run_points = balance_change = None
    notes = []
    if state is not None:
        start = state.get("start_weekly")
        if isinstance(start, (int, float)) and not isinstance(start, bool):
            if weekly >= start:
                run_points = round(weekly - start, 4)
            else:
                notes.append("weekly fell below the start reading (window reset), run points unknown")
        start_balance = state.get("start_balance")
        if balance is not None and isinstance(start_balance, (int, float)) and not isinstance(start_balance, bool):
            balance_change = round(balance - start_balance, 6)
    if weekly >= STOP_WEEKLY:
        return "stop", f"weekly allowance is at {weekly:g}%; spending past it needs the owner's OK for this run", run_points, balance_change
    if balance_change is not None and balance_change < -BALANCE_EPSILON:
        return "stop", f"credit balance fell by {-balance_change:g} since the run started; paid credits need the owner's OK", run_points, balance_change
    if weekly >= WRAP_WEEKLY:
        return "wrap-up", f"weekly total is {weekly:g}%, at or over {WRAP_WEEKLY}%; finish the current item, write a handoff, ask", run_points, balance_change
    if weekly >= TELL_WEEKLY:
        return "tell-owner", f"weekly total is {weekly:g}%, at or over {TELL_WEEKLY}%; tell the owner at this round boundary", run_points, balance_change
    if run_points is not None and run_points >= TELL_RUN_POINTS:
        return "tell-owner", f"this run used {run_points:g} points, at or over {TELL_RUN_POINTS}; tell the owner at this round boundary", run_points, balance_change
    reason = f"weekly total is {weekly:g}%"
    if run_points is not None:
        reason += f", this run used {run_points:g} points"
    else:
        reason += ", run points unknown (no run state)"
    return "continue", "; ".join([reason] + notes), run_points, balance_change


def main(argv=None):
    parser = argparse.ArgumentParser(prog="usage_gate.py", description=__doc__.split("\n")[0])
    parser.add_argument("--claude", metavar="FILE", help="get_usage JSON file, or - for stdin")
    parser.add_argument("--model", metavar="NAME", help="with --claude: watch the weekly window that names this model, e.g. Fable")
    parser.add_argument("--codex", metavar="FILE", help="Codex usage JSON file, or - for stdin")
    parser.add_argument("--weekly", type=float, metavar="N", help="weekly percent used, by hand")
    parser.add_argument("--balance", type=float, metavar="B", help="credit balance, with --weekly")
    parser.add_argument("--state", metavar="FILE", help="run-state file (created on first check)")
    parser.add_argument("--start", action="store_true", help="rewrite the run state from this reading")
    parser.add_argument("--log", metavar="FILE", help="append one JSON line per check to this run log")
    parser.add_argument("--at", metavar="LABEL", default="", help="checkpoint name for the log, e.g. 'round 2'")
    try:
        args = parser.parse_args(argv)
    except SystemExit as err:
        return 2 if err.code else 0

    def fail(message):
        print(json.dumps({"action": "error", "reason": message}))
        return 2

    try:
        sources = [name for name, value in (("claude", args.claude), ("codex", args.codex), ("weekly", args.weekly)) if value is not None]
        if len(sources) != 1:
            raise UsageError("give exactly one of --claude, --codex, --weekly")
        if args.balance is not None and args.weekly is None:
            raise UsageError("--balance goes with --weekly")
        if args.start and not args.state:
            raise UsageError("--start needs --state")
        if args.model is not None and args.claude is None:
            raise UsageError("--model goes with --claude")
        model_window = model_note = None
        if args.claude is not None:
            reading = read_json(args.claude)
            weekly, balance, note = claude_reading(reading)
            # With no all-models window the highest weekly window is already the weekly reading, so the automatic
            # lookup would only repeat it. A window the caller named is still looked up: its own reading and its
            # handoff signal must not vanish because the total is missing.
            if weekly is not None and (args.model is not None or not note.startswith("no all-models window")):
                model_window, model_note = claude_model_window(reading, args.model)
        elif args.codex is not None:
            weekly, balance, note = codex_reading(read_json(args.codex))
        else:
            weekly, balance, note = percent(args.weekly, "--weekly"), None, "given by hand"
            if args.balance is not None:
                balance = number(args.balance, "--balance")
        state, state_note = None, None
        if weekly is not None and args.state:
            if args.start or not Path(args.state).is_file():
                state = save_state(args.state, weekly, balance, sources[0])
                state_note = "run state written"
            else:
                state = load_state(args.state)
    except UsageError as err:
        return fail(str(err))

    if weekly is None:
        action, reason = "ask-owner", f"no usable reading ({note}); ask the owner for the weekly percent before starting new work"
        run_points = balance_change = None
        handoff_now = False
    else:
        action, reason, run_points, balance_change = decide(weekly, balance, state)
        action, reason, handoff_now = model_check(action, reason, model_window)
    if model_note:
        note = f"{note}; {model_note}"
    result = {"action": action, "reason": reason, "weekly": weekly, "run_points": run_points,
              "model_window": None if model_window is None else {"label": model_window[0], "percent": model_window[1]},
              "handoff_now": handoff_now,
              "balance": balance, "balance_change": balance_change, "source": sources[0], "reading": note,
              "thresholds": {"tell_weekly": TELL_WEEKLY, "tell_run_points": TELL_RUN_POINTS,
                             "wrap_weekly": WRAP_WEEKLY, "stop_weekly": STOP_WEEKLY}}
    if state_note:
        result["state"] = state_note
    if args.at:
        result["at"] = args.at
    shown = "unknown" if weekly is None else f"{weekly:g}%"
    result["record_line"] = f"Usage: {action} at {args.at or 'check'}, weekly {shown}" + (
        f", run +{run_points:g}" if run_points is not None else "")
    if model_window is not None and model_window[1] >= TELL_WEEKLY:
        result["record_line"] += f", {model_window[0]} {model_window[1]:g}%" + (", handoff now" if handoff_now else "")
    if args.log:
        try:
            line = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "at": args.at, "action": action,
                    "weekly": weekly, "run_points": run_points, "balance": balance,
                    "model_window": None if model_window is None else model_window[0],
                    "model_weekly": None if model_window is None else model_window[1],
                    "handoff_now": handoff_now, "reason": reason}
            log = Path(args.log)
            log.parent.mkdir(parents=True, exist_ok=True)
            with open(log, "ab") as handle:
                handle.write((json.dumps(line, ensure_ascii=False) + "\n").encode("utf-8"))
        except OSError as err:
            return fail(f"cannot write log {args.log}: {err}")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if action in ("continue", "tell-owner") else 1


if __name__ == "__main__":
    sys.exit(main())
