"""Score loop rounds with a judge panel and say what the loop does next.

A run folder holds panel.json (item, target, rubric, references, judges), verdict.schema.json and rounds.jsonl.
Judges are read-only and never see the target or any earlier score: `brief` prints what a judge gets, and nothing in it
comes from the target or from an earlier score. From round 2 (`brief --round N`) it also carries the diff since the last
round and the earlier rounds' blocking items as text. The first judge scores every round; the confirming judges that the
run's depth asks for (quick none, standard the second judge, deep all) score only a candidate the first judge passed.
A programmatic check outranks every judge: a failed check fails the round. Only blocking items the candidate introduced
fail a round; pre-existing ones are a backlog in `status`.

Subcommands: init, brief, check, record, codex, hash, snapshot, extend, status. `status` prints JSON and exits 0 only when the panel passed;
1 means repair, judge, confirm or stop (see "next"); 2 means bad usage or a missing file.
Stdlib only. The only subprocess is `codex exec` in a read-only sandbox, run with an argument list, never a shell.
"""
import argparse
import difflib
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PANEL = "panel.json"
ROUNDS = "rounds.jsonl"
SCHEMA_FILE = "verdict.schema.json"
DEFAULT_JUDGES = ["haiku", "sonnet", "codex"]
CODEX_TIMEOUT = 1800
SNAPSHOTS = "snapshots"
DEPTHS = ("quick", "standard", "deep")
DEFAULT_DEPTH = "standard"
DEFAULT_GROWTH_LIMIT = 2.0
DIFF_LIMIT = 24000
ORIGINS = ("introduced", "pre-existing")

VERDICT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["score", "criteria", "blocking", "summary"],
    "properties": {
        "score": {"type": "number", "minimum": 0, "maximum": 10},
        "criteria": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["name", "score", "evidence"],
                "properties": {
                    "name": {"type": "string"},
                    "score": {"type": "number", "minimum": 0, "maximum": 10},
                    "evidence": {"type": "string"},
                },
            },
        },
        "blocking": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["item", "origin", "class"],
                "properties": {
                    "item": {"type": "string"},
                    "origin": {"type": "string", "enum": list(ORIGINS)},
                    "class": {"type": "string"},
                },
            },
        },
        "summary": {"type": "string"},
    },
}


class PanelError(Exception):
    """Bad usage, a missing file or a record that breaks the round rules: exit 2."""


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_panel(run):
    path = Path(run) / PANEL
    if not path.is_file():
        raise PanelError(f"no {PANEL} in {run}; run init first")
    return json.loads(path.read_text(encoding="utf-8"))


def load_rounds(run):
    path = Path(run) / ROUNDS
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def is_score(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and 0 <= value <= 10


def validate_verdict(verdict):
    """Return a list of problems; empty means the verdict matches VERDICT_SCHEMA."""
    if not isinstance(verdict, dict):
        return ["verdict is not a JSON object"]
    problems = []
    extra = set(verdict) - set(VERDICT_SCHEMA["properties"])
    if extra:
        problems.append("unknown keys: " + ", ".join(sorted(extra)))
    for key in VERDICT_SCHEMA["required"]:
        if key not in verdict:
            problems.append(f"missing {key}")
    if "score" in verdict and not is_score(verdict["score"]):
        problems.append("score must be a number from 0 to 10")
    criteria = verdict.get("criteria")
    if "criteria" in verdict:
        if not isinstance(criteria, list) or not criteria:
            problems.append("criteria must be a non-empty list")
        else:
            for index, item in enumerate(criteria):
                if not isinstance(item, dict) or set(item) != {"name", "score", "evidence"}:
                    problems.append(f"criteria[{index}] needs exactly name, score and evidence")
                    continue
                if not isinstance(item["name"], str) or not item["name"].strip():
                    problems.append(f"criteria[{index}].name is empty")
                if not is_score(item["score"]):
                    problems.append(f"criteria[{index}].score must be a number from 0 to 10")
                if not isinstance(item["evidence"], str) or not item["evidence"].strip():
                    problems.append(f"criteria[{index}].evidence is empty: every score needs evidence")
    if "blocking" in verdict:
        blocking = verdict["blocking"]
        if not isinstance(blocking, list):
            problems.append("blocking must be a list")
        else:
            for index, entry in enumerate(blocking):
                if isinstance(entry, str):
                    continue  # older verdicts: a plain string counts as an introduced item
                if not isinstance(entry, dict) or set(entry) != {"item", "origin", "class"}:
                    problems.append(f"blocking[{index}] needs exactly item, origin and class (or be a plain string)")
                    continue
                if not isinstance(entry["item"], str) or not entry["item"].strip():
                    problems.append(f"blocking[{index}].item is empty")
                if entry["origin"] not in ORIGINS:
                    problems.append(f"blocking[{index}].origin must be introduced or pre-existing")
                if not isinstance(entry["class"], str):
                    problems.append(f"blocking[{index}].class must be a string")
    if "summary" in verdict and not isinstance(verdict["summary"], str):
        problems.append("summary must be a string")
    return problems


def blocking_items(verdict):
    """Blocking entries as {item, origin, class}. A plain string from an older verdict is an introduced item."""
    items = []
    for entry in verdict.get("blocking", []):
        if isinstance(entry, str):
            items.append({"item": entry, "origin": "introduced", "class": ""})
        else:
            items.append({"item": entry["item"], "origin": entry.get("origin", "introduced"), "class": entry.get("class", "")})
    return items


def introduced(verdict):
    return [b for b in blocking_items(verdict) if b["origin"] == "introduced"]


def needed_judges(panel):
    """Judges a pass needs at the run's depth. A panel written before depth existed asked for every judge."""
    judges = panel["judges"]
    depth = panel.get("depth", "deep")
    if depth == "quick":
        return judges[:1]
    if depth == "standard":
        return judges[:2]
    return list(judges)


# A name is one to four words before the colon, so a prose bullet such as "- Use when the file is X: ..." is not
# read as a criterion (calibration run 2026-11-06). Two-word names such as "house fit" still parse.
CRITERION = re.compile(r"^[ \t]*[-*][ \t]+`?([A-Za-z0-9][\w.-]*(?:[ \t][\w.-]+){0,3})`?[ \t]*:", re.M)


def rubric_criteria(path):
    """Criterion names from rubric lines shaped `- name: what to check`. Empty when the rubric uses another shape."""
    return {m.group(1).strip().lower() for m in CRITERION.finditer(Path(path).read_text(encoding="utf-8"))}


def candidate_hash(paths):
    """First 12 hex digits of SHA-256 over the files' bytes, in the order given."""
    digest = hashlib.sha256()
    for name in paths:
        path = Path(name)
        if not path.is_file():
            raise PanelError(f"not a file: {path}")
        digest.update(path.read_bytes())
    return digest.hexdigest()[:12]


def append(run, record):
    with (Path(run) / ROUNDS).open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def check_round(panel, rounds, number, candidate, kind, name):
    """Enforce the round rules before a record is written."""
    if not isinstance(number, int) or number < 1:
        raise PanelError("round must be 1 or more")
    latest = max((r["round"] for r in rounds), default=0)
    if number not in (latest, latest + 1) or (latest == 0 and number != 1):
        raise PanelError(f"round {number} is out of order: the latest round is {latest}")
    if not candidate.strip():
        raise PanelError("candidate is empty: name the revision or artifact hash being judged")
    same = [r for r in rounds if r["round"] == number]
    if same and same[0]["candidate"] != candidate:
        raise PanelError(f"round {number} judges {same[0]['candidate']}, not {candidate}: one candidate per round")
    if number == latest + 1 and latest:
        previous = next(r["candidate"] for r in rounds if r["round"] == latest)
        if previous == candidate:
            raise PanelError("a new round needs a changed candidate; re-judging the same one is not a fresh review")
        settled = round_state(panel, [r for r in rounds if r["round"] == latest])
        if settled["passed"] is not False:
            raise PanelError(f"round {latest} is not settled ({settled['next']}); finish it before opening round {number}")
    if number > panel["max_rounds"]:
        raise PanelError(f"round {number} is past the budget of {panel['max_rounds']} rounds")
    if any(r["kind"] == kind and r["name"] == name for r in same):
        raise PanelError(f"{kind} {name} is already recorded for round {number}")
    if kind == "judge":
        if name not in panel["judges"]:
            raise PanelError(f"{name} is not on this panel: {', '.join(panel['judges'])}")
        if name not in needed_judges(panel):
            raise PanelError(f"{name} is not needed at depth {panel.get('depth', 'deep')}: "
                             f"{', '.join(needed_judges(panel))} judge this run")
        first = panel["judges"][0]
        if name != first:
            gate = next((r for r in same if r["kind"] == "judge" and r["name"] == first), None)
            if gate is None or gate["score"] < panel["target"] or introduced(gate["verdict"]):
                raise PanelError(f"{name} confirms only a candidate {first} passed; {first} has not passed round {number}")


def round_state(panel, records):
    target, judges = panel["target"], needed_judges(panel)
    checks = [r for r in records if r["kind"] == "check"]
    scores = {r["name"]: r["score"] for r in records if r["kind"] == "judge"}
    failed = [c["name"] for c in checks if not c["passed"]]
    # An introduced blocking item is a defect the judge says this candidate made, so it fails the round at any score.
    # A pre-existing one is a backlog item: status lists it and the round ignores it.
    blocked = [r["name"] for r in records if r["kind"] == "judge" and introduced(r["verdict"])]
    state = {"round": records[0]["round"], "candidate": records[0]["candidate"], "scores": scores,
             "checks": {c["name"]: c["passed"] for c in checks}, "failed_checks": failed}
    first = judges[0]
    if failed:
        state.update(passed=False, next="repair", reason="check failed: " + ", ".join(failed))
    elif first not in scores:
        state.update(passed=None, next="judge:" + first, reason=f"{first} has not judged this candidate")
    elif scores[first] < target:
        state.update(passed=False, next="repair", reason=f"{first} scored below target")
    elif blocked:
        state.update(passed=False, next="repair", reason="blocking items from: " + ", ".join(blocked))
    else:
        missing = [j for j in judges[1:] if j not in scores]
        if missing:
            state.update(passed=None, next="confirm:" + missing[0], reason=f"{first} passed; {missing[0]} confirms next")
        else:
            panel_score = min(scores[j] for j in judges)
            state["panel_score"] = panel_score
            if panel_score >= target:
                state.update(passed=True, next="pass", reason="every judge reached the target")
            else:
                low = [j for j in judges if scores[j] < target]
                state.update(passed=False, next="repair", reason="below target: " + ", ".join(low))
    if "panel_score" not in state and scores:
        state["panel_score"] = min(scores.values())
    return state


def take_snapshot(run, number, candidate, paths):
    """Copy the candidate's files under the run folder and record their sizes, so a later round can diff against them.

    A round's snapshot is evidence for the verdict already given on it, so it is never replaced: repeating it
    with the same files and bytes returns the saved manifest, and anything else fails before a byte is written.
    """
    if not isinstance(number, int) or number < 1:
        raise PanelError("round must be 1 or more")
    if not candidate.strip():
        raise PanelError("candidate is empty")
    folder = Path(run) / SNAPSHOTS / f"round-{number}"
    manifest_path = folder / "manifest.json"
    read = []
    for name in paths:
        path = Path(name)
        if not path.is_file():
            raise PanelError(f"not a file: {path}")
        read.append((str(name), path.read_bytes()))
    if manifest_path.is_file():
        saved = json.loads(manifest_path.read_text(encoding="utf-8"))
        if saved["candidate"] != candidate:
            raise PanelError(f"round {number} already has a snapshot of another candidate")
        if not same_snapshot(folder, saved, read):
            raise PanelError(f"round {number} already has a snapshot of different files or bytes; "
                             "a judged round's evidence is never replaced, so snapshot the change as the next round")
        return saved
    files = []
    (folder / "files").mkdir(parents=True, exist_ok=True)
    for index, (name, data) in enumerate(read):
        try:
            data.decode("utf-8")
            text = True
        except UnicodeDecodeError:
            text = False
        copy = f"{index}.txt" if text else None
        if copy:
            (folder / "files" / copy).write_bytes(data)
        files.append({"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                      "text": text, "copy": copy})
    manifest = {"round": number, "candidate": candidate, "total_bytes": sum(f["bytes"] for f in files), "files": files}
    manifest_path.write_bytes((json.dumps(manifest, indent=2) + "\n").encode("utf-8"))
    return manifest


def same_snapshot(folder, saved, read):
    """True when the files just read are exactly the ones the saved snapshot holds."""
    if [f["path"] for f in saved["files"]] != [name for name, _ in read]:
        return False
    for entry, (_, data) in zip(saved["files"], read):
        if entry["bytes"] != len(data):
            return False
        if entry.get("sha256"):
            if entry["sha256"] != hashlib.sha256(data).hexdigest():
                return False
        elif not entry.get("copy") or (folder / "files" / entry["copy"]).read_bytes() != data:
            return False  # an older manifest without a hash: compare the saved copy, and refuse a binary file
    return True


def load_snapshot(run, number):
    path = Path(run) / SNAPSHOTS / f"round-{number}" / "manifest.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def snapshot_text(run, manifest, entry):
    return (Path(run) / SNAPSHOTS / f"round-{manifest['round']}" / "files" / entry["copy"]).read_bytes().decode("utf-8")


def snapshot_diff(run, old, new, limit=DIFF_LIMIT):
    """Unified diff between two rounds' snapshots, capped. None when either round has no snapshot."""
    before, after = load_snapshot(run, old), load_snapshot(run, new)
    if before is None or after is None:
        return None
    old_files = {f["path"]: f for f in before["files"]}
    new_files = {f["path"]: f for f in after["files"]}
    chunks, notes = [], []
    for path in list(new_files) + [p for p in old_files if p not in new_files]:
        a, b = old_files.get(path), new_files.get(path)
        if (a and not a["text"]) or (b and not b["text"]):
            notes.append(f"binary file changed or not diffable: {path}")
            continue
        a_lines = snapshot_text(run, before, a).splitlines(keepends=True) if a else []
        b_lines = snapshot_text(run, after, b).splitlines(keepends=True) if b else []
        diff = "".join(difflib.unified_diff(a_lines, b_lines, f"{path} (round {old})" if a else "/dev/null",
                                            f"{path} (round {new})" if b else "/dev/null"))
        if diff:
            chunks.append(diff if diff.endswith("\n") else diff + "\n")
    text = "".join(chunks)
    truncated = len(text) > limit
    if truncated:
        text = text[:limit].rsplit("\n", 1)[0] + "\n"
    return {"text": text, "truncated": truncated, "notes": notes}


def previous_blocking(rounds, before):
    """Blocking items earlier rounds posted, as text only (no scores), without repeats."""
    seen, items = set(), []
    for record in rounds:
        if record["kind"] == "judge" and record["round"] < before:
            for entry in blocking_items(record["verdict"]):
                if entry["item"] not in seen:
                    seen.add(entry["item"])
                    items.append({**entry, "round": record["round"]})
    return items


def size_report(run, panel):
    """Candidate bytes per round, growth against round 1 and a warning past the panel's limit."""
    root = Path(run) / SNAPSHOTS
    sizes = {}
    for folder in sorted(root.glob("round-*")) if root.is_dir() else []:
        manifest = load_snapshot(run, int(folder.name.split("-")[1]))
        if manifest:
            sizes[manifest["round"]] = manifest["total_bytes"]
    if not sizes:
        return None
    report = {"bytes": {str(n): sizes[n] for n in sorted(sizes)}}
    first, last = sizes.get(1), sizes[max(sizes)]
    limit = panel.get("growth_limit", DEFAULT_GROWTH_LIMIT)
    if first and max(sizes) > 1:
        report["growth"] = round(last / first, 2)
        if last / first > limit:
            report["warning"] = (f"the candidate is {report['growth']}x its round 1 size (limit {limit}x): "
                                 "the fixer may be addressing nits and bloating the change; fix only introduced "
                                 "blocking items and criteria below the target")
    return report


def status(run):
    panel = load_panel(run)
    rounds = load_rounds(run)
    if not rounds:
        return {"item": panel["item"], "round": 0, "next": "judge:" + panel["judges"][0], "passed": None,
                "reason": "no round recorded yet", "depth": panel.get("depth", "deep"), "history": []}
    history = [round_state(panel, [r for r in rounds if r["round"] == n]) for n in sorted({r["round"] for r in rounds})]
    latest = dict(history[-1])
    if latest["next"] == "repair":
        failed = [h for h in history if h["passed"] is False]
        previous = failed[-2] if len(failed) >= 2 and failed[-2]["round"] == latest["round"] - 1 else None
        same_check = previous is not None and set(latest["failed_checks"]) & set(previous["failed_checks"])
        no_gain = previous is not None and "panel_score" in latest and "panel_score" in previous \
            and latest["panel_score"] <= previous["panel_score"]
        # The budget stop is checked first, so a round that is both over budget and stuck reports stop:budget.
        if latest["round"] >= panel["max_rounds"]:
            latest.update(next="stop:budget", reason=latest["reason"] + f"; the {panel['max_rounds']}-round budget is spent. "
                          "Step back and reconsider the approach before asking for more rounds")
        elif same_check or no_gain:
            why = "the same check failed twice in a row" if same_check else "two failed rounds with no score gain"
            latest.update(next="stop:no-progress",
                          reason=latest["reason"] + f"; {why}. Go on only with a new hypothesis the owner accepts")
    latest["item"] = panel["item"]
    latest["depth"] = panel.get("depth", "deep")
    seen = {}
    for record in rounds:
        if record["kind"] == "judge":
            for entry in blocking_items(record["verdict"]):
                if entry["origin"] == "pre-existing" and entry["item"] not in seen:
                    seen[entry["item"]] = {**entry, "round": record["round"], "judge": record["name"]}
    if seen:
        latest["backlog"] = list(seen.values())
    size = size_report(run, panel)
    if size:
        latest["size"] = size
    latest["history"] = [{k: h[k] for k in ("round", "candidate", "scores", "checks", "passed") if k in h} for h in history]
    return latest


def brief(run, candidate, judge, round_=None):
    """What a judge gets. Built from panel.json without the target. From round 2 it adds the diff since the last round
    and the earlier rounds' blocking items as text; it never carries a score."""
    panel = load_panel(run)
    rubric = Path(panel["rubric"])
    if not rubric.is_file():
        raise PanelError(f"rubric not found: {rubric}")
    lines = [
        f"# Judge brief: {panel['item']}",
        "",
        f"You are the {judge} judge on a read-only panel. Do not edit, create or delete any file, and run nothing that",
        "changes state. Score the candidate below on its own merits; you are not told any target or any earlier score,",
        "and you must not guess or ask for them.",
        "",
        f"Do not open anything under {Path(run).resolve().as_posix()}: it holds the loop's own records, not the work.",
        "",
        f"Candidate: {candidate}",
        "",
        "## What to judge",
    ]
    lines += [f"- {a}" for a in panel["artifacts"]] or ["- (the candidate named above)"]
    if round_ and round_ > 1:
        lines += ["", "## Earlier rounds", "",
                  "Review the changed parts of the candidate first, then the rest. Do not repeat a finding that an earlier",
                  "round already posted: they are listed below as text. If one is still present in the candidate, list it",
                  "under blocking once more, starting the item with `still open:`; otherwise leave it out."]
        earlier = previous_blocking(load_rounds(run), round_)
        if earlier:
            lines += ["", "Findings posted before:"]
            lines += [f"- round {e['round']}: {e['item']}" + (f" [class: {e['class']}]" if e["class"] else "") for e in earlier]
        else:
            lines += ["", "No blocking item was posted before."]
        diff = snapshot_diff(run, round_ - 1, round_)
        if diff is None:
            lines += ["", "No diff is available for this round: review the whole candidate."]
        else:
            cut = " (cut at the size cap)" if diff["truncated"] else ""
            lines += ["", f"Diff since the previous round's candidate{cut}:", ""]
            lines += ["```diff", diff["text"].rstrip("\n") or "(no text changes)", "```"]
            lines += [f"- {n}" for n in diff["notes"]]
    lines += ["", "## Reference work", ""]
    if panel["references"]:
        lines.append("Score relative to these. A 10 means the candidate matches or beats the best of them on that criterion.")
        lines += [f"- {r}" for r in panel["references"]]
    else:
        lines.append("None given. Score against the rubric alone and say so in the summary.")
    lines += ["", "## Rubric", "", rubric.read_text(encoding="utf-8").strip(), "", "## How to score", "",
              "- Score each rubric criterion from 0 to 10 with the evidence for it: a file and line, a command and its",
              "  output, or a quoted passage. A score without evidence is not accepted.",
              "- The overall score is your own judgment from 0 to 10, not an average you were told to compute.",
              "- List under blocking only defects that must be fixed for this to be acceptable; preferences go in the summary.",
              "- Each blocking item is an object: `item` says what is wrong and where; `origin` is `introduced` when this",
              "  candidate's change created or worsened the defect, `pre-existing` when it was already there before the",
              "  change (when you cannot tell, use `introduced`); `class` names the kind of defect in a few words, so the",
              "  fixer can fix every instance of it, not one line.",
              "- Reply with one JSON object and nothing else, matching this schema:", "",
              json.dumps(VERDICT_SCHEMA, indent=2)]
    return "\n".join(lines) + "\n"


def cmd_init(args):
    run = Path(args.run)
    if (run / PANEL).exists() and not args.force:
        raise PanelError(f"{run / PANEL} exists; pass --force to replace it")
    rubric = Path(args.rubric).resolve()
    if not rubric.is_file():
        raise PanelError(f"rubric not found: {rubric}")
    if not 0 < args.target <= 10:
        raise PanelError("target must be above 0 and at most 10")
    judges = [j.strip() for j in args.judges.split(",") if j.strip()]
    if len(judges) != len(set(judges)) or not judges:
        raise PanelError("judges must be a non-empty list without repeats")
    if (run / ROUNDS).exists():
        raise PanelError(f"{run / ROUNDS} already holds rounds; start a new run folder instead")
    run.mkdir(parents=True, exist_ok=True)
    if args.growth_limit <= 1:
        raise PanelError("growth limit must be above 1 (a multiple of the round 1 size)")
    panel = {"item": args.item, "target": args.target, "rubric": str(rubric), "judges": judges,
             "references": args.reference or [], "artifacts": args.artifact or [], "max_rounds": args.max_rounds,
             "depth": args.depth, "growth_limit": args.growth_limit, "created": now()}
    (run / PANEL).write_text(json.dumps(panel, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (run / SCHEMA_FILE).write_text(json.dumps(VERDICT_SCHEMA, indent=2) + "\n", encoding="utf-8")
    (run / "verdicts").mkdir(exist_ok=True)
    criteria = sorted(rubric_criteria(rubric))
    print(json.dumps({"ok": True, "run": str(run.resolve()), "judges": judges, "depth": args.depth, "criteria": criteria,
                      **({} if criteria else {"warning": "no `- name: what to check` lines found; record will not check coverage"})}))
    return 0


def cmd_brief(args):
    sys.stdout.write(brief(args.run, args.candidate, args.judge, args.round))
    return 0


def cmd_check(args):
    panel, rounds = load_panel(args.run), load_rounds(args.run)
    check_round(panel, rounds, args.round, args.candidate, "check", args.name)
    append(args.run, {"round": args.round, "candidate": args.candidate, "kind": "check", "name": args.name,
                      "passed": args.passed == "true", "detail": args.detail or "", "at": now()})
    print(json.dumps({"ok": True}))
    return 0


def record_verdict(run, number, candidate, judge, verdict):
    panel, rounds = load_panel(run), load_rounds(run)
    problems = validate_verdict(verdict)
    if not problems:
        scored = {c["name"].strip().lower() for c in verdict["criteria"]}
        skipped = sorted(rubric_criteria(panel["rubric"]) - scored)
        if skipped:
            problems.append("no score for rubric criteria: " + ", ".join(skipped))
    if problems:
        raise PanelError("verdict rejected: " + "; ".join(problems))
    check_round(panel, rounds, number, candidate, "judge", judge)
    append(run, {"round": number, "candidate": candidate, "kind": "judge", "name": judge, "score": verdict["score"],
                 "verdict": verdict, "at": now()})


def read_verdict(path):
    text = Path(path).read_text(encoding="utf-8-sig").strip()
    if text.startswith("```"):
        text = text.strip("`").split("\n", 1)[-1].rsplit("```", 1)[0]
    try:
        return json.loads(text)
    except ValueError as error:
        raise PanelError(f"verdict in {path} is not JSON: {error}") from error


def cmd_record(args):
    record_verdict(args.run, args.round, args.candidate, args.judge, read_verdict(args.verdict))
    print(json.dumps({"ok": True}))
    return 0


def cmd_codex(args):
    panel, rounds = load_panel(args.run), load_rounds(args.run)
    check_round(panel, rounds, args.round, args.candidate, "judge", args.judge)
    run = Path(args.run)
    project = Path(args.project).resolve()
    if run.resolve() == project or run.resolve().is_relative_to(project):
        raise PanelError(f"the run folder is inside {project}, which Codex can read: pass a --project that holds the "
                         "artifacts and references but not the run folder")
    out_dir = run / "verdicts"
    out_dir.mkdir(exist_ok=True)
    out = out_dir / f"round-{args.round}-{args.judge}.json"
    text = brief(args.run, args.candidate, args.judge, args.round)
    (out_dir / f"round-{args.round}-{args.judge}.brief.md").write_text(text, encoding="utf-8")
    cmd = [args.codex_bin, "exec", "--sandbox", "read-only", "--ephemeral", "--skip-git-repo-check",
           "-C", str(project), "--output-schema", str((run / SCHEMA_FILE).resolve()),
           "-o", str(out.resolve()), "-c", f'model_reasoning_effort="{args.effort}"']
    if args.model:
        cmd += ["-m", args.model]
    cmd.append("-")
    try:
        result = subprocess.run(cmd, input=text, capture_output=True, text=True, encoding="utf-8", errors="replace",
                                timeout=args.timeout, check=False)
    except FileNotFoundError as error:
        raise PanelError(f"{args.codex_bin} not found on PATH") from error
    except subprocess.TimeoutExpired as error:
        raise PanelError(f"codex timed out after {args.timeout} s; nothing recorded") from error
    if result.returncode != 0 or not out.is_file():
        raise PanelError(f"codex exited {result.returncode}; nothing recorded. {result.stderr.strip()[-600:]}")
    try:
        record_verdict(args.run, args.round, args.candidate, args.judge, read_verdict(out))
    except PanelError as error:
        raise PanelError(f"{error}. The reply is kept at {out.resolve()}; run codex once more for a fresh judge, "
                         "and count a second rejection as no verdict") from error
    print(json.dumps({"ok": True, "verdict": str(out.resolve())}))
    return 0


def cmd_snapshot(args):
    load_panel(args.run)
    manifest = take_snapshot(args.run, args.round, args.candidate, args.paths)
    print(json.dumps({"ok": True, "round": args.round, "total_bytes": manifest["total_bytes"]}))
    return 0


def cmd_hash(args):
    print(candidate_hash(args.paths))
    return 0


def cmd_extend(args):
    panel = load_panel(args.run)
    if args.rounds <= panel["max_rounds"]:
        raise PanelError(f"the budget is already {panel['max_rounds']} rounds; extend only raises it")
    if not args.reason.strip():
        raise PanelError("say who allowed the extra rounds and why")
    panel.setdefault("budget_changes", []).append(
        {"from": panel["max_rounds"], "to": args.rounds, "reason": args.reason, "at": now()})
    panel["max_rounds"] = args.rounds
    (Path(args.run) / PANEL).write_text(json.dumps(panel, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "max_rounds": args.rounds}))
    return 0


def cmd_status(args):
    state = status(args.run)
    print(json.dumps(state, indent=2, ensure_ascii=False))
    return 0 if state.get("passed") is True else 1


def parser():
    top = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = top.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="start a run folder")
    p.add_argument("run")
    p.add_argument("--item", required=True)
    p.add_argument("--target", type=float, required=True, help="score out of 10 every judge must reach; judges never see it")
    p.add_argument("--rubric", required=True, help="markdown file listing the criteria")
    p.add_argument("--reference", action="append", help="reference work to score against (repeatable)")
    p.add_argument("--artifact", action="append", help="what the judges read (repeatable)")
    p.add_argument("--judges", default=",".join(DEFAULT_JUDGES), help="first judge, then confirmers, comma separated")
    p.add_argument("--max-rounds", type=int, default=3, help="first attempt plus two repairs, as the improvement loop's default")
    p.add_argument("--depth", choices=DEPTHS, default=DEFAULT_DEPTH,
                   help="quick: first judge only; standard: plus the second judge; deep: every judge. Set it from the change's blast radius")
    p.add_argument("--growth-limit", type=float, default=DEFAULT_GROWTH_LIMIT,
                   help="warn when the candidate grows past this multiple of its round 1 size")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("brief", help="print the brief one judge gets")
    p.add_argument("run")
    p.add_argument("--candidate", required=True)
    p.add_argument("--judge", required=True)
    p.add_argument("--round", type=int, help="round number; from 2 the brief adds the diff and earlier blocking items")
    p.set_defaults(func=cmd_brief)

    p = sub.add_parser("check", help="record a programmatic check for a round")
    p.add_argument("run")
    p.add_argument("--round", type=int, required=True)
    p.add_argument("--candidate", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--passed", choices=["true", "false"], required=True)
    p.add_argument("--detail")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("record", help="record one judge's JSON verdict for a round")
    p.add_argument("run")
    p.add_argument("--round", type=int, required=True)
    p.add_argument("--candidate", required=True)
    p.add_argument("--judge", required=True)
    p.add_argument("--verdict", required=True, help="file holding the judge's JSON reply")
    p.set_defaults(func=cmd_record)

    p = sub.add_parser("codex", help="run the Codex judge read-only and record its verdict")
    p.add_argument("run")
    p.add_argument("--round", type=int, required=True)
    p.add_argument("--candidate", required=True)
    p.add_argument("--project", required=True, help="folder Codex reads, read-only; must not contain the run folder")
    p.add_argument("--judge", default="codex")
    p.add_argument("--model")
    p.add_argument("--effort", default="medium")
    p.add_argument("--codex-bin", default="codex")
    p.add_argument("--timeout", type=int, default=CODEX_TIMEOUT)
    p.set_defaults(func=cmd_codex)

    p = sub.add_parser("hash", help="print a candidate name: SHA-256 of the files' bytes, first 12 digits")
    p.add_argument("paths", nargs="+")
    p.set_defaults(func=cmd_hash)

    p = sub.add_parser("snapshot", help="record the candidate's files for a round: sizes now, a diff in the next brief")
    p.add_argument("run")
    p.add_argument("--round", type=int, required=True)
    p.add_argument("--candidate", required=True)
    p.add_argument("paths", nargs="+", help="the same files, in the same order, as `hash`")
    p.set_defaults(func=cmd_snapshot)

    p = sub.add_parser("extend", help="raise the round budget, recording who allowed it")
    p.add_argument("run")
    p.add_argument("--rounds", type=int, required=True)
    p.add_argument("--reason", required=True)
    p.set_defaults(func=cmd_extend)

    p = sub.add_parser("status", help="print the latest round's verdict and the next step")
    p.add_argument("run")
    p.set_defaults(func=cmd_status)
    return top


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        return args.func(args)
    except (PanelError, OSError, ValueError, KeyError) as error:
        print(json.dumps({"ok": False, "error": str(error)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
