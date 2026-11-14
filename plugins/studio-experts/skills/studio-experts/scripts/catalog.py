"""Read-only role retrieval. Rankings help discovery; the coordinator selects the panel.

Uses only the bundled catalog and source lock. No vendor imports, project scans or network.
"""
import argparse
import collections
import hashlib
import json
import math
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = ("unity", "unreal", "blender", "maya", "zbrush", "godot")
STOP = set("a an the is it in on for to of and or with from this that when use using my our do not"
           " looks look needs need issue problem fix broken scenario expert unity unreal blender maya"
           " zbrush godot engine project app game".split())
NORMALIZE = {
    "elbows": "elbow", "shoulders": "shoulder", "collapsing": "collapse", "collapsed": "collapse",
    "feet": "foot", "sliding": "slide", "slides": "slide", "skating": "skate",
    "stutters": "stutter", "stuttering": "stutter", "hitches": "hitch", "hitching": "hitch",
    "meshes": "mesh", "textures": "texture", "materials": "material", "shaders": "shader",
    "baking": "bake", "baked": "bake", "retargeting": "retarget", "retargeted": "retarget",
}


def tokens(text):
    return [NORMALIZE.get(t, t) for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in STOP]


def contained(relative):
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError(f"Pack path escapes the skill: {relative}")
    return path


def load_roles():
    data = json.loads((ROOT / "references/catalog.json").read_text(encoding="utf-8"))
    roles = data["roles"]
    names = set()
    available = []
    upstream_absent = not (ROOT / "vendor").is_dir()
    for role in roles:
        if role["family"] not in FAMILIES or role["name"] in names:
            raise ValueError("Invalid family or duplicate role in catalog")
        names.add(role["name"])
        if upstream_absent and role["path"].startswith("vendor/"):
            continue  # a public copy before the pinned upstream clone: local families still work
        if not contained(role["path"]).is_file():
            raise ValueError(f"Missing role: {role['name']}")
        available.append(role)
    data["roles"] = available
    return data


def retrieve(data, families=(), query="", limit=None):
    selected = set(families or FAMILIES)
    rows = [dict(r) for r in data["roles"] if r["family"] in selected]
    specialists = [r for r in rows if not r["lead"]]
    documents = [tokens(r["name"] + " " + r["description"] + " " + r.get("aliases", ""))
                 for r in specialists]
    average = sum(map(len, documents)) / max(1, len(documents))
    df = collections.Counter(t for d in documents for t in set(d))
    query_tokens = set(tokens(query))
    for row, document in zip(specialists, documents):
        tf = collections.Counter(document)
        score = 0.0
        matches = sorted(query_tokens & tf.keys())
        for term in matches:
            idf = math.log(1 + (len(documents) - df[term] + 0.5) / (df[term] + 0.5))
            score += idf * tf[term] * 2.2 / (tf[term] + 1.2 * (0.25 + 0.75 * len(document) / average))
        row.update(retrieval_score=round(score, 4), matched_terms=matches)
    specialists.sort(key=lambda r: (-r["retrieval_score"], r["name"]))
    leaders = sorted([r for r in rows if r["lead"]], key=lambda r: r["name"])
    for row in leaders + specialists:
        row["path"] = contained(row["path"]).as_posix()
    notices = ["Read picker.md: text relevance is not a selected panel, expertise confidence or execution readiness."]
    if not families:
        notices.append("No family specified. Resolve application ownership before selecting; all five are shown.")
    if query and not any(r["retrieval_score"] > 0 for r in specialists):
        notices.append("No matching specialist terms. Do not infer a winner; inspect the family catalog or clarify the task.")
    if limit is not None:
        notices.append("Candidate list truncated by --limit; inspect the full family for coverage before selection.")
    return {
        "query": query, "families": sorted(selected), "notices": notices,
        "validation": {f: data["families"][f] for f in sorted(selected)},
        "leads": leaders, "candidate_count": len(specialists),
        "candidates": specialists if limit is None else specialists[:limit],
    }


def verify():
    lock = json.loads((ROOT / "references/source-lock.json").read_text(encoding="utf-8"))
    errors = []
    # A public copy pins upstream bytes in files and its own in local_files, and may not have fetched upstream yet.
    public = "local_files" in lock
    upstream_absent = public and not (ROOT / "vendor").is_dir()
    tracked = {**({} if upstream_absent else lock["files"]), **lock.get("local_files", {})}
    for relative, digest in tracked.items():
        path = contained(relative)
        if not path.is_file():
            errors.append(f"Missing: {relative}")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            errors.append(f"Changed: {relative}")
    listed = set(tracked)
    actual = {p.relative_to(ROOT).as_posix() for p in (ROOT / "vendor").rglob("*")
              if p.is_file() and not (public and ".git" in p.relative_to(ROOT).parts)}
    errors.extend(f"Untracked vendor file: {p}" for p in sorted(actual - listed))
    data = load_roles()
    expected = {"godot": 6} if upstream_absent else {"unity": 14, "unreal": 10, "blender": 14, "maya": 11, "zbrush": 9, "godot": 6}
    actual_counts = dict(collections.Counter(r["family"] for r in data["roles"]))
    if actual_counts != expected:
        errors.append(f"Family count mismatch: {actual_counts}")
    for family in expected:
        if sum(r["lead"] for r in data["roles"] if r["family"] == family) != 1:
            errors.append(f"Expected one lead for {family}")
    result = {"ok": not errors, "upstream_commit": lock["commit"], "roles": len(data["roles"]),
              "verified_files": len(tracked), "errors": errors}
    if upstream_absent:
        result["upstream"] = "not fetched: only this copy's own files were verified"
    return result


def positive(value):
    result = int(value)
    if result < 1:
        raise argparse.ArgumentTypeError("must be positive")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--family", action="append", choices=FAMILIES, default=[])
    parser.add_argument("--query", default="")
    parser.add_argument("--limit", type=positive)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    try:
        result = verify() if args.verify else retrieve(load_roles(), args.family, args.query, args.limit)
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(2, f"Catalog error: {exc}\n")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if args.format == "json" or args.verify:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for notice in result["notices"]:
            print("NOTE: " + notice)
        for family, evidence in result["validation"].items():
            print(f"{family}: {evidence}")
        for label, rows in (("LEAD", result["leads"]), ("CANDIDATE", result["candidates"])):
            for role in rows:
                print(f"\n{label} {role['name']} | matches: {', '.join(role.get('matched_terms', []))}")
                print(role["description"])
                print(role["path"])
    return 1 if args.verify and not result["ok"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
