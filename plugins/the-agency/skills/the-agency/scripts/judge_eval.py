"""Calibrate a judge on known cases: past bugs, and known-clean work to count noise.

Cases live in evals/judge/<case-id>/ as candidate/ (the files to judge), rubric.md and case.json. This script never
calls a model. `brief` prints what a judge gets; the coordinator runs the judges and saves one verdict JSON per case,
named <case-id>.json; `score` compares those verdicts with each case's expectation.

Subcommands: list, brief, score. `score` prints JSON and exits 0 only when every case meets its expectation;
1 means at least one case missed; 2 means bad usage or a missing file.
Stdlib only. The brief reuses judge_panel.brief; nothing from case.json goes into it.
"""
import argparse
import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CASES = HERE.parent / "evals" / "judge"
PASS_SCORE = 6.0

_spec = importlib.util.spec_from_file_location("judge_panel", HERE / "judge_panel.py")
judge_panel = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(judge_panel)


class EvalError(Exception):
    """Bad usage or a missing file: exit 2."""


def load_case(case_dir):
    case_dir = Path(case_dir)
    path = case_dir / "case.json"
    if not path.is_file():
        raise EvalError(f"no case.json in {case_dir}")
    case = json.loads(path.read_text(encoding="utf-8"))
    for key in ("id", "kind", "origin", "expect"):
        if key not in case:
            raise EvalError(f"{path} lacks {key}")
    if case["kind"] not in ("bug", "clean"):
        raise EvalError(f"{path}: kind must be bug or clean")
    if not (case_dir / "rubric.md").is_file() or not (case_dir / "candidate").is_dir():
        raise EvalError(f"{case_dir} needs rubric.md and a candidate folder")
    case["dir"] = case_dir
    return case


def load_cases(root):
    root = Path(root)
    if not root.is_dir():
        raise EvalError(f"no case folder at {root}")
    cases = [load_case(p) for p in sorted(root.iterdir()) if (p / "case.json").is_file()]
    if not cases:
        raise EvalError(f"no cases under {root}")
    return cases


def find_case(root, case_id):
    for case in load_cases(root):
        if case["id"] == case_id:
            return case
    raise EvalError(f"unknown case: {case_id}")


def candidate_files(case):
    """The case's own candidate files. A link or junction that leads outside the case folder is refused:
    staging would otherwise copy an outside file into the folder a judge reads."""
    folder = (case["dir"] / "candidate").resolve()
    files = sorted(p for p in (case["dir"] / "candidate").rglob("*") if p.is_file())
    for path in files:
        if path.is_symlink() or not path.resolve().is_relative_to(folder):
            raise EvalError(f"{case['id']}: candidate file is a link or resolves outside the case folder: {path.name}")
    return files


def make_brief(case, stage=None):
    """Judge brief for one case. Files are staged under a neutral hash folder, so no path carries the case id or kind."""
    files = candidate_files(case)
    tag = hashlib.sha256(b"".join(f.read_bytes() for f in files)).hexdigest()[:12]
    stage_root = Path(stage) if stage else Path(tempfile.mkdtemp(prefix="judge-eval-"))
    work = stage_root / tag
    work.mkdir(parents=True, exist_ok=True)
    artifacts = []
    for f in files:
        target = work / f.relative_to(case["dir"] / "candidate")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(f, target)
        artifacts.append(target.resolve().as_posix())
    rubric = work / "rubric.md"
    shutil.copyfile(case["dir"] / "rubric.md", rubric)
    run = stage_root / f"run-{tag}"
    run.mkdir(exist_ok=True)
    panel = {"item": f"calibration {tag}", "target": PASS_SCORE, "rubric": str(rubric.resolve()), "judges": ["calibration"],
             "references": [], "artifacts": artifacts, "max_rounds": 1}
    (run / "panel.json").write_bytes(json.dumps(panel, indent=2).encode("utf-8") + b"\n")
    return judge_panel.brief(str(run), tag, "calibration")


def blocking_items(verdict):
    items = []
    for entry in verdict.get("blocking") or []:
        if isinstance(entry, str):
            items.append(entry)
        elif isinstance(entry, dict) and isinstance(entry.get("item"), str):
            items.append(entry["item"])
        else:
            raise EvalError("a blocking entry must be a string or an object with an item key")
    return items


def read_verdict(path):
    try:
        data = judge_panel.read_verdict(path)
    except Exception as error:
        raise EvalError(f"{path}: {error}") from error
    if not isinstance(data, dict):
        raise EvalError(f"{path}: verdict is not a JSON object")
    score = data.get("score")
    if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= score <= 10:
        raise EvalError(f"{path}: score must be a number from 0 to 10")
    return data


def judge_case(case, verdict, target=PASS_SCORE):
    score = verdict["score"]
    blocking = blocking_items(verdict)
    passed = score >= target and not blocking
    expect, reasons = case["expect"], []
    if "pass" in expect and passed != expect["pass"]:
        reasons.append(f"verdict {'passed' if passed else 'failed'}, expected {'a pass' if expect['pass'] else 'a fail'}")
    if "max_score" in expect and score > expect["max_score"]:
        reasons.append(f"score {score} is above the maximum {expect['max_score']}")
    if "min_score" in expect and score < expect["min_score"]:
        reasons.append(f"score {score} is below the minimum {expect['min_score']}")
    if "must_block" in expect and bool(blocking) != expect["must_block"]:
        reasons.append("no blocking item raised" if expect["must_block"] else f"blocked a clean case: {blocking[0]}")
    return {"case": case["id"], "kind": case["kind"], "ok": not reasons, "score": score, "blocking": len(blocking),
            "reasons": reasons}


def score_all(root, verdicts, target=PASS_SCORE):
    verdicts = Path(verdicts)
    if not verdicts.is_dir():
        raise EvalError(f"no verdicts folder at {verdicts}")
    results = []
    for case in load_cases(root):
        path = verdicts / f"{case['id']}.json"
        if not path.is_file():
            results.append({"case": case["id"], "kind": case["kind"], "ok": False, "score": None, "blocking": 0,
                            "reasons": [f"no verdict file {path.name}"], "missing": True})
            continue
        results.append(judge_case(case, read_verdict(path), target))
    bugs = [r for r in results if r["kind"] == "bug"]
    clean = [r for r in results if r["kind"] == "clean"]

    def mean(rows):
        scored = [r["score"] for r in rows if r["score"] is not None]
        return round(sum(scored) / len(scored), 2) if scored else None

    gap = None if mean(bugs) is None or mean(clean) is None else round(mean(clean) - mean(bugs), 2)
    totals = {"cases": len(results), "met": sum(r["ok"] for r in results),
              "missed_bugs": sum(not r["ok"] for r in bugs), "false_blocks": sum(r["blocking"] > 0 for r in clean),
              "clean_misses": sum(not r["ok"] for r in clean),
              "missing_verdicts": sum(bool(r.get("missing")) for r in results),
              # The panel's own rule: an introduced blocking item fails a round at any score. These two count
              # what a real round would have done, apart from the stricter score bounds in each case's expect.
              "bugs_blocked": sum(r["blocking"] > 0 for r in bugs if not r.get("missing")),
              "bugs_unblocked": sum(r["blocking"] == 0 for r in bugs),
              "mean_bug_score": mean(bugs), "mean_clean_score": mean(clean), "score_gap": gap}
    return {"ok": all(r["ok"] for r in results), "pass_score": target, "results": results, "totals": totals}


def cmd_list(args):
    rows = [{"id": c["id"], "kind": c["kind"], "origin": c["origin"], "files": [f.name for f in candidate_files(c)]}
            for c in load_cases(args.cases)]
    print(json.dumps(rows, indent=2, ensure_ascii=False))
    return 0


def cmd_brief(args):
    sys.stdout.write(make_brief(find_case(args.cases, args.case), args.stage))
    return 0


def cmd_score(args):
    report = score_all(args.cases, args.verdicts, args.target)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["ok"] else 1


def parser():
    top = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    top.add_argument("--cases", default=str(CASES), help="case folder (default: evals/judge)")
    sub = top.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="list the cases").set_defaults(func=cmd_list)
    p = sub.add_parser("brief", help="print the judge brief for one case")
    p.add_argument("case")
    p.add_argument("--stage", help="folder to stage the candidate files in (default: a new temp folder)")
    p.set_defaults(func=cmd_brief)
    p = sub.add_parser("score", help="score a folder of <case-id>.json verdicts")
    p.add_argument("verdicts")
    p.add_argument("--target", type=float, default=PASS_SCORE,
                   help="score at or above which a verdict with no blocking items passes")
    p.set_defaults(func=cmd_score)
    return top


def main(argv=None):
    try:
        args = parser().parse_args(argv)
    except SystemExit as error:
        return 2 if error.code else 0
    try:
        return args.func(args)
    except (EvalError, OSError, ValueError, KeyError) as error:
        print(json.dumps({"ok": False, "error": str(error)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
