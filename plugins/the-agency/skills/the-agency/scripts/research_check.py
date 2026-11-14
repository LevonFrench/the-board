"""Check the evidence chain of wiki research: raw notes carry their provenance, articles point at notes that exist.

  research_check.py [--baseline <git-commit>] raw <folder or .md files>   staged or ingested raw notes
  research_check.py [--baseline <git-commit>] article <.md files>        compiled articles

Prints JSON with ok, counts and a problems list per file. Exit 0 when every file passes, 1 when any fails, 2 on bad
usage. Read-only. It proves the links exist and the provenance is recorded, not that a claim is true.

Raw notes follow the llm-wiki plugin's schema: title, source, type (one of the plugin's raw folder kinds, matching
the raw/<kind>/ folder the note sits in) and ingested, plus the division's own fields.

With --baseline each file is also checked as it was at that commit (a file absent then has no problems). Each file's
problems split into introduced and pre_existing, and the exit code is 1 only when something was introduced.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

RAW_REQUIRED = ("title", "source", "type", "ingested", "fetched", "evidence_type", "credibility")
RAW_TYPES = ("articles", "data", "notes", "papers", "repos")
SHARD = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)+\.md$")
URL = re.compile(r"https?://\S+")
COPY_HOSTS = re.compile(r"web\.archive\.org|r\.jina\.ai|archive\.ph|archive\.today", re.I)
CHALLENGE = re.compile(r"just a moment\.\.\.|verify you are human|security verification|checking your browser|"
                       r"enable javascript and cookies|i am not a robot|not a bot", re.I)
OWN_LINE_URL = re.compile(r"^\s*(?:[-*]\s+)?(?:\*\*)?[A-Za-z][A-Za-z ]{0,30}:?(?:\*\*)?\s*<?https?://\S+?>?\s*$|^\s*<?https?://\S+?>?\s*$")
SKIP = {"_index.md", "ledger.md", "log.md"}
MIN_BODY = 300


def front(text):
    """Return (fields, list fields, body) for simple YAML frontmatter, or (None, None, text) without one."""
    text = text.replace("\r\n", "\n")
    if not text.startswith("---\n"):
        return None, None, text
    end = text.find("\n---", 4)
    if end < 0:
        return None, None, text
    fields, lists, key = {}, {}, None
    for line in text[4:end].split("\n"):
        top = re.match(r"^([A-Za-z_][\w-]*):\s?(.*)$", line)
        if top:
            key, value = top.group(1), top.group(2).strip()
            fields[key] = value.strip("\"'")
            flow = re.match(r"^\[(.*)\]$", value)
            if flow:
                lists[key] = [part.strip().strip("\"'") for part in flow.group(1).split(",") if part.strip()]
            continue
        item = re.match(r"^\s+-\s+(.*)$", line)
        if item and key:
            lists.setdefault(key, []).append(item.group(1).strip().strip("\"'"))
        elif key and line.startswith((" ", "\t")) and fields.get(key) in ("|", ">", "|-", ">-"):
            fields[key + "__text"] = fields.get(key + "__text", "") + line.strip() + " "
    body = text[end + 4:].split("\n", 1)[1] if "\n" in text[end + 4:] else ""
    return fields, lists, body


def read(path):
    return path.read_text(encoding="utf-8", errors="replace")


def check_raw(path, text=None):
    problems = []
    fields, _, body = front(read(path) if text is None else text)
    if fields is None:
        return ["no frontmatter"]
    for key in RAW_REQUIRED:
        if not fields.get(key):
            problems.append(f"missing {key}")
    kind = fields.get("type", "")
    if kind and kind not in RAW_TYPES:
        problems.append(f"type {kind!r} is not a raw folder kind ({', '.join(RAW_TYPES)})")
    parent = path.resolve().parent
    if kind in RAW_TYPES and parent.parent.name == "raw" and parent.name in RAW_TYPES and parent.name != kind:
        problems.append(f"type {kind!r} does not match its folder raw/{parent.name}/")
    source = fields.get("source", "")
    if source and not URL.search(source):
        problems.append("source has no URL")
    if not SHARD.match(path.name):
        problems.append("name is not <YYYY-MM-DD>-<angle>-<source>.md")
    if COPY_HOSTS.search(source + " " + body[:2000]) and not fields.get("fetch-method"):
        problems.append("archive or reader copy without fetch-method")
    if CHALLENGE.search(body):
        problems.append("body carries bot-wall challenge text")
    if len(re.sub(r"\s+", "", body)) < MIN_BODY and fields.get("retention") != "quarantine-candidate":
        problems.append(f"body under {MIN_BODY} characters: too thin to be evidence")
    return problems


def wiki_root(path):
    for folder in path.resolve().parents:
        if (folder / "raw").is_dir():
            return folder
    return None


def check_article(path, text=None):
    problems = []
    fields, lists, body = front(read(path) if text is None else text)
    if fields is None:
        return ["no frontmatter"]
    sources = lists.get("sources", [])
    if not sources:
        problems.append("no sources list")
    root = wiki_root(path)
    for source in sources:
        if URL.match(source):
            continue
        if root is None or not (root / source).is_file():
            problems.append(f"source missing: {source}")
    if not any(OWN_LINE_URL.match(line) for line in body.split("\n")):
        problems.append("no source URL on its own line")
    if body.count("[UNSUPPORTED") > body.count("Failed verification"):
        problems.append("an [UNSUPPORTED] claim has no failed-verification note")
    return problems


def files(targets):
    out = []
    for target in targets:
        path = Path(target)
        if path.is_dir():
            out += sorted(p for p in path.rglob("*.md") if p.name not in SKIP and "quarantine" not in p.parts)
        elif path.is_file():
            if path.name not in SKIP:
                out.append(path)
        else:
            raise FileNotFoundError(target)
    return out


def baseline_text(path, commit):
    """The file's text at commit, or None when it did not exist there. Raises ValueError for a bad commit or repo."""
    folder = path.resolve().parent
    def git(*args):
        return subprocess.run(["git", "-C", str(folder), *args], capture_output=True)
    top = git("rev-parse", "--show-toplevel")
    if top.returncode:
        raise ValueError(f"not in a git repository: {path}")
    if git("rev-parse", "--verify", "--quiet", f"{commit}^{{commit}}").returncode:
        raise ValueError(f"unknown commit: {commit}")
    rel = path.resolve().relative_to(Path(top.stdout.decode().strip()).resolve()).as_posix()
    if git("cat-file", "-e", f"{commit}:{rel}").returncode:
        return None
    shown = git("show", f"{commit}:{rel}")
    if shown.returncode:
        raise ValueError(f"git show failed for {rel}")
    return shown.stdout.decode("utf-8", errors="replace")


def split_problems(now, before):
    """Problems in now that the baseline lacks are introduced; matching ones are pre-existing (counted one for one)."""
    left = list(before)
    introduced, old = [], []
    for problem in now:
        if problem in left:
            left.remove(problem)
            old.append(problem)
        else:
            introduced.append(problem)
    return introduced, old


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--baseline", metavar="COMMIT", help="split problems into introduced and pre_existing against this commit")
    parser.add_argument("mode", choices=["raw", "article"])
    parser.add_argument("targets", nargs="+")
    args = parser.parse_args(argv)
    try:
        paths = files(args.targets)
    except FileNotFoundError as error:
        print(json.dumps({"ok": False, "error": f"not found: {error}"}), file=sys.stderr)
        return 2
    check = check_raw if args.mode == "raw" else check_article
    if args.baseline:
        results = []
        try:
            for p in paths:
                old = baseline_text(p, args.baseline)
                before = [] if old is None else check(p, old)
                introduced, pre = split_problems(check(p), before)
                results.append({"path": str(p), "introduced": introduced, "pre_existing": pre})
        except ValueError as error:
            print(json.dumps({"ok": False, "error": str(error)}), file=sys.stderr)
            return 2
        failed = [r for r in results if r["introduced"]]
        listed = [r for r in results if r["introduced"] or r["pre_existing"]]
        print(json.dumps({"ok": not failed, "mode": args.mode, "baseline": args.baseline, "checked": len(results),
                          "failed": len(failed), "introduced": sum(len(r["introduced"]) for r in results),
                          "pre_existing": sum(len(r["pre_existing"]) for r in results), "files": listed},
                         indent=2, ensure_ascii=False))
        return 1 if failed else 0
    results = [{"path": str(p), "problems": check(p)} for p in paths]
    failed = [r for r in results if r["problems"]]
    print(json.dumps({"ok": not failed, "mode": args.mode, "checked": len(results), "failed": len(failed),
                      "files": failed}, indent=2, ensure_ascii=False))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
