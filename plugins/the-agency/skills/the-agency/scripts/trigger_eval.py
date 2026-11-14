#!/usr/bin/env python3
"""Check that a skill's description routes the right prompts to it.

  trigger_eval.py run <cases.json> --cwd <fixture project> --out <folder> [--model sonnet] [--jobs 4] [--max-turns 3]
  trigger_eval.py score <cases.json> --out <folder>

run starts one headless `claude -p` per case from the fixture project, with read-only tools and the Skill
tool allowed, and saves each stream-json transcript. score reads the transcripts and records the first
skill each run invoked: a "trigger" case passes when that is the skill under test, a "skip" case passes
when it is not, and an "either" case (both routes are right) passes on either route. A case passes only
when its transcript is valid: a session that started, took a turn and ended with a result. An empty or
truncated transcript, or any session error, fails the case and is counted under "invalid". Hitting the
turn cap after the first move is accepted, and the row says why. Prints one JSON object; exits 0 when
every case passes, 1 when any fails, 2 on bad usage.

A run costs agent usage: check the usage gate first. The score is one sample per case on one model,
so treat a single miss as a lead, not a verdict.
"""
import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

TOOLS = "Skill,Read,Glob,Grep"


def first_skill(lines):
    """The first skill a stream-json transcript invoked, the tools it used before that, and the cost."""
    used, skill, cost, error = [], None, None, None
    started, turns, ended, subtype = False, 0, False, None
    for line in lines:
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get("type") == "system" and event.get("subtype") == "init":
            started = True
        if event.get("type") == "assistant":
            turns += 1
            for block in event.get("message", {}).get("content", []):
                if block.get("type") != "tool_use":
                    continue
                if block.get("name") == "Skill" and skill is None:
                    skill = str(block.get("input", {}).get("skill") or block.get("input", {}).get("command") or "")
                elif skill is None:
                    used.append(block.get("name"))
        elif event.get("type") == "result":
            ended, subtype = True, event.get("subtype")
            cost = event.get("total_cost_usd")
            if event.get("is_error") and subtype != "error_max_turns":
                error = subtype or "error"
    # A routing result needs a session that started, made at least one move and ended cleanly. The turn
    # limit is the one accepted error: the harness caps turns on purpose, and by then the model has made
    # its first move, which is the routing decision being scored.
    invalid = ("empty transcript" if not started else "no turn taken" if not turns
               else "truncated: no result event" if not ended else f"session error: {error}" if error else None)
    return {"skill": skill, "tools_before": used, "cost_usd": cost, "error": error,
            "end": subtype, "invalid": invalid}


def run_case(case, args):
    out = Path(args.out) / f"{case['id']}.jsonl"
    cmd = ["claude", "-p", case["prompt"], "--output-format", "stream-json", "--verbose",
           "--max-turns", str(args.max_turns), "--allowedTools", TOOLS, "--model", args.model]
    with open(out, "w", encoding="utf-8") as handle:
        done = subprocess.run(cmd, cwd=args.cwd, stdout=handle, stderr=subprocess.PIPE, text=True,
                              encoding="utf-8", timeout=args.timeout)
    (Path(args.out) / f"{case['id']}.exit").write_text(str(done.returncode), encoding="utf-8")
    return case["id"], done.returncode


def score(cases, folder, skill):
    rows, total = [], 0.0
    for case in cases["cases"]:
        path = Path(folder) / f"{case['id']}.jsonl"
        if not path.is_file():
            rows.append({"id": case["id"], "expect": case["expect"], "pass": False, "note": "no transcript"})
            continue
        seen = first_skill(path.read_text(encoding="utf-8").splitlines())
        total += seen["cost_usd"] or 0
        hit = bool(seen["skill"]) and (seen["skill"] == skill or seen["skill"].endswith(":" + skill))
        ok = True if case["expect"] == "either" else hit if case["expect"] == "trigger" else not hit
        row = {"id": case["id"], "expect": case["expect"], "chose": seen["skill"], "pass": ok and not seen["invalid"],
               "tools_before": seen["tools_before"], "cost_usd": seen["cost_usd"], "end": seen["end"],
               "prompt": case["prompt"]}
        if seen["invalid"]:
            row["invalid"] = seen["invalid"]
        elif seen["end"] == "error_max_turns":
            row["accepted_because"] = ("hit the --max-turns cap after its first move; the first move is "
                                       "the routing choice this test scores")
        exit_file = Path(folder) / f"{case['id']}.exit"
        if exit_file.is_file():
            row["exit_code"] = int(exit_file.read_text(encoding="utf-8").strip() or -1)
        if case["expect"] == "skip":
            row["as_intended"] = seen["skill"] in case.get("others", []) if seen["skill"] else not case.get("others")
        if seen["error"]:
            row["error"] = seen["error"]
        rows.append(row)
    trig = [r for r in rows if r["expect"] == "trigger"]
    skip = [r for r in rows if r["expect"] == "skip"]
    either = [r for r in rows if r["expect"] == "either"]
    return {"ok": all(r["pass"] for r in rows), "skill": skill,
            "invalid": sum(1 for r in rows if r.get("invalid") or r.get("note") == "no transcript"),
            "trigger_recall": f"{sum(r['pass'] for r in trig)}/{len(trig)}",
            "skip_correct": f"{sum(r['pass'] for r in skip)}/{len(skip)}",
            "either_chose_skill": f"{sum(1 for r in either if r.get('chose'))}/{len(either)}",
            "cost_usd": round(total, 4), "cases": rows}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["run", "score"])
    parser.add_argument("cases")
    parser.add_argument("--out", required=True)
    parser.add_argument("--cwd")
    parser.add_argument("--model", default="sonnet")
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--max-turns", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=300)
    try:
        args = parser.parse_args(sys.argv[1:] if argv is None else argv)
        cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    except SystemExit as stop:
        return 2 if stop.code else 0
    except (OSError, ValueError) as error:
        print(json.dumps({"ok": False, "error": str(error)}))
        return 2
    if args.command == "run":
        if not args.cwd or not Path(args.cwd).is_dir():
            print(json.dumps({"ok": False, "error": "--cwd must be the fixture project folder"}))
            return 2
        Path(args.out).mkdir(parents=True, exist_ok=True)
        with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
            list(pool.map(lambda case: run_case(case, args), cases["cases"]))
    report = score(cases, args.out, cases["skill"])
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
