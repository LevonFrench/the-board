#!/usr/bin/env python3
"""Keep a project's media kit: <project>/.mediakit, the screenshots, logos, renders, video and audio
an Agency run already made that could show or promote the project.

  mediakit.py candidates <project> [--since <ISO date>] [--path <folder> ...] [--record <run record> ...]
  mediakit.py add <project> <file> --kind <kind> --caption <text> --shows <text> --run <run>
                  [--source-note <text>] [--supersedes <id>]
  mediakit.py check <project>

candidates lists media files the run made (under --path folders, else the whole project) that are not
already in the kit by hash. add copies one file in, never moves or edits the original, and records it in
.mediakit/manifest.json; a file whose bytes are already in the kit is skipped. check proves the manifest
and the folder agree. Every command prints one JSON object and exits 0 when it is OK, 1 when something
needs fixing and 2 on bad usage. Video stays out of git through .mediakit/.gitignore; the manifest still
lists it by hash.

The script cannot see what an image shows: the curator looks at every file before adding it and keeps
anything that shows a secret, an account page, personal data or a private path out of the kit.
"""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

KIT = ".mediakit"
MANIFEST = "manifest.json"
KINDS = {"screenshot": "screenshots", "logo": "logos", "render": "renders", "video": "video",
         "audio": "audio", "other": "other"}
MEDIA = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".bmp", ".tif", ".tiff",
         ".mp4", ".mov", ".webm", ".mkv", ".avi", ".wav", ".mp3", ".flac", ".ogg", ".m4a"}
SKIP_DIRS = {".git", ".mediakit", "node_modules", ".venv", "venv", "__pycache__", "Library", "Temp",
             ".godot", ".import", "Intermediate", "DerivedDataCache", "Binaries", ".wiki", "dist", "build"}
GITIGNORE = "# Video stays out of git; manifest.json still lists each file by hash.\nvideo/*\n!video/.gitkeep\n"


class KitError(Exception):
    pass


def sha256_of(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load(project):
    path = Path(project) / KIT / MANIFEST
    if not path.is_file():
        return {"version": 1, "items": []}
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict) or not isinstance(data.get("items"), list):
        raise KitError(f"{path} is not a media kit manifest")
    return data


def save(project, data):
    path = Path(project) / KIT / MANIFEST
    path.write_bytes((json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))


def ensure_kit(project):
    kit = Path(project) / KIT
    (kit / "video").mkdir(parents=True, exist_ok=True)
    (kit / "video" / ".gitkeep").touch()
    if not (kit / ".gitignore").is_file():
        (kit / ".gitignore").write_bytes(GITIGNORE.encode("utf-8"))
    return kit


def git_commit(project):
    try:
        done = subprocess.run(["git", "-C", str(project), "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return done.stdout.strip() or None if done.returncode == 0 else None


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:48] or "item"


def cmd_candidates(args):
    project = Path(args.project).resolve()
    if not project.is_dir():
        raise KitError(f"not a folder: {project}")
    known = {item.get("sha256") for item in load(project)["items"]}
    since = datetime.fromisoformat(args.since).timestamp() if args.since else None
    roots = [Path(p) if Path(p).is_absolute() else project / p for p in (args.path or [project])]
    found, seen = [], set()
    for root in roots:
        if not root.is_dir():
            raise KitError(f"not a folder: {root}")
        stack = [root]
        while stack:
            folder = stack.pop()
            try:
                entries = list(folder.iterdir())
            except OSError:
                continue
            for entry in entries:
                if entry.is_dir() and not entry.is_symlink():
                    if entry.name not in SKIP_DIRS:
                        stack.append(entry)
                elif entry.is_file() and entry.suffix.lower() in MEDIA:
                    stat = entry.stat()
                    if since and stat.st_mtime < since:
                        continue
                    digest = sha256_of(entry)
                    if digest in known or digest in seen:
                        continue
                    seen.add(digest)
                    found.append({"path": entry.as_posix(), "bytes": stat.st_size, "sha256": digest,
                                  "modified": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(timespec="seconds")})
    cited = set()
    for record in args.record or []:
        cited |= referenced(Path(record) if Path(record).is_absolute() else project / record, project)
    for row in found:
        row["referenced"] = Path(row["path"]).resolve() in cited
    found.sort(key=lambda row: row["modified"], reverse=True)
    found.sort(key=lambda row: not row["referenced"])
    folders = {}
    for row in found:
        name = Path(row["path"]).parent
        try:
            name = name.relative_to(project)
        except ValueError:
            pass
        entry = folders.setdefault(name.as_posix(), {"folder": name.as_posix(), "files": 0, "newest": row["modified"]})
        entry["files"] += 1
        entry["newest"] = max(entry["newest"], row["modified"])
    return 0, {"ok": True, "project": project.as_posix(), "count": len(found),
               "referenced": sum(row["referenced"] for row in found),
               "folders": sorted(folders.values(), key=lambda f: f["newest"], reverse=True),
               "candidates": found[: args.limit]}


LINKED = re.compile(r"[\w./\\:-]+\.(?:png|jpe?g|webp|gif|svg|bmp|tiff?|mp4|mov|webm|mkv|avi|wav|mp3|flac|ogg|m4a)\b", re.I)


def referenced(record, project):
    """Media files a run record names, by link or bare path, resolved against the record and the project."""
    if not record.is_file():
        raise KitError(f"not a file: {record}")
    found = set()
    for match in LINKED.findall(record.read_text(encoding="utf-8", errors="replace")):
        name = Path(match.replace("\\", "/"))
        for base in ((name,) if name.is_absolute() else (record.parent / name, project / name)):
            if base.is_file():
                found.add(base.resolve())
                break
    return found


def cmd_add(args):
    project, source = Path(args.project).resolve(), Path(args.file).resolve()
    if not project.is_dir():
        raise KitError(f"not a folder: {project}")
    if not source.is_file():
        raise KitError(f"not a file: {source}")
    kit_root = (project / KIT).resolve()
    if kit_root in source.parents:
        raise KitError("the file is already inside the media kit")
    for field in ("caption", "shows", "run"):
        if not (getattr(args, field) or "").strip():
            raise KitError(f"--{field} is empty")
    data = load(project)
    digest = sha256_of(source)
    same = next((item for item in data["items"] if item.get("sha256") == digest), None)
    if same:
        return 0, {"ok": True, "added": False, "duplicate_of": same["id"]}
    old = None
    if args.supersedes:
        old = next((item for item in data["items"] if item["id"] == args.supersedes), None)
        if old is None:
            raise KitError(f"--supersedes {args.supersedes!r} is not in the manifest")
        if old.get("superseded_by"):
            raise KitError(f"{args.supersedes} is already superseded by {old['superseded_by']}")
    kit = ensure_kit(project)
    folder = kit / KINDS[args.kind]
    folder.mkdir(exist_ok=True)
    day = datetime.now().strftime("%Y-%m-%d")
    # The id is unique across the whole manifest, not only within one kind's folder or extension,
    # and the file is named after it, so an id never points at two items.
    taken = {item.get("id") for item in data["items"]}
    stem, n = f"{day}-{slug(args.caption)}", 1
    item_id, target = stem, folder / f"{stem}{source.suffix.lower()}"
    while item_id in taken or target.exists():
        n += 1
        item_id, target = f"{stem}-{n}", folder / f"{stem}-{n}{source.suffix.lower()}"
    shutil.copy2(source, target)
    if sha256_of(target) != digest:
        target.unlink()
        raise KitError("the copy does not match the original; nothing was added")
    try:
        origin = source.relative_to(project).as_posix()
    except ValueError:
        origin = source.as_posix()
    item = {"id": item_id, "file": target.relative_to(kit).as_posix(), "kind": args.kind,
            "caption": args.caption.strip(), "shows": args.shows.strip(), "source": origin,
            "run": args.run.strip(), "commit": git_commit(project), "added": day,
            "bytes": target.stat().st_size, "sha256": digest, "in_git": args.kind != "video"}
    if args.source_note:
        item["source_note"] = args.source_note.strip()
    if old is not None:
        item["supersedes"] = old["id"]
        old["superseded_by"] = item["id"]
    data["items"].append(item)
    save(project, data)
    return 0, {"ok": True, "added": True, "item": item}


def cmd_check(args):
    project = Path(args.project).resolve()
    kit = project / KIT
    failures, warnings = [], []
    if not kit.is_dir():
        return 0, {"ok": True, "items": 0, "failures": [], "warnings": ["no media kit yet"]}
    data = load(project)
    ids, hashes, files = {}, {}, set()
    for item in data["items"]:
        missing = [f for f in ("id", "file", "kind", "caption", "shows", "source", "run", "added", "sha256") if not item.get(f)]
        if missing:
            failures.append(f"{item.get('id', '?')}: missing {', '.join(missing)}")
            continue
        if item["id"] in ids:
            failures.append(f"duplicate id {item['id']}")
        ids[item["id"]] = item
        if item["sha256"] in hashes:
            failures.append(f"{item['id']} has the same bytes as {hashes[item['sha256']]}")
        hashes[item["sha256"]] = item["id"]
        if item["kind"] not in KINDS:
            failures.append(f"{item['id']}: kind {item['kind']!r} is not one of {', '.join(KINDS)}")
        files.add(item["file"])
        path = kit / item["file"]
        # Every listed file must sit inside the kit: no absolute path, no "..", no link out.
        if Path(item["file"]).is_absolute() or (kit.resolve() not in path.resolve().parents):
            failures.append(f"{item['id']}: file is outside the kit: {item['file']}")
            continue
        if not path.is_file():
            failures.append(f"{item['id']}: file missing: {item['file']}")
        elif sha256_of(path) != item["sha256"]:
            failures.append(f"{item['id']}: file changed since it was added: {item['file']}")
    for item in data["items"]:
        for link in ("supersedes", "superseded_by"):
            if item.get(link) and item[link] not in ids:
                failures.append(f"{item.get('id')}: {link} {item[link]!r} is not in the manifest")
    for path in kit.rglob("*"):
        rel = path.relative_to(kit).as_posix()
        if path.is_file() and rel not in files and rel not in (MANIFEST, ".gitignore", "video/.gitkeep"):
            failures.append(f"unlisted file in the kit: {rel}")
    if not (kit / ".gitignore").is_file():
        warnings.append("no .mediakit/.gitignore: video would go into git")
    current = sum(1 for item in data["items"] if not item.get("superseded_by"))
    return (1 if failures else 0), {"ok": not failures, "items": len(data["items"]), "current": current,
                                    "failures": failures, "warnings": warnings}


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("candidates", help="media files the run made that are not in the kit yet")
    p.add_argument("project")
    p.add_argument("--since", help="only files modified at or after this ISO date or time")
    p.add_argument("--path", action="append", help="a run or output folder to look in; repeatable")
    p.add_argument("--record", action="append", help="a run record or summary; media it names are listed first")
    p.add_argument("--limit", type=int, default=60)
    p.set_defaults(func=cmd_candidates)
    p = sub.add_parser("add", help="copy one file into the kit and record it")
    p.add_argument("project")
    p.add_argument("file")
    p.add_argument("--kind", required=True, choices=sorted(KINDS))
    p.add_argument("--caption", required=True, help="one line a reader could use under the image")
    p.add_argument("--shows", required=True, help="what is on screen, plainly")
    p.add_argument("--run", required=True, help="the run that made it: its folder or record path")
    p.add_argument("--source-note", help="anything a reuser must know, such as third-party content in frame")
    p.add_argument("--supersedes", help="the id of an older item showing the same thing")
    p.set_defaults(func=cmd_add)
    p = sub.add_parser("check", help="the manifest and the folder agree")
    p.add_argument("project")
    p.set_defaults(func=cmd_check)
    return parser


def main(argv=None):
    parser = build_parser()
    try:
        args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    except SystemExit as stop:
        return 2 if stop.code else 0
    try:
        code, report = args.func(args)
    except (KitError, ValueError, OSError) as error:
        code, report = 2, {"ok": False, "error": str(error)}
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return code


if __name__ == "__main__":
    sys.exit(main())
