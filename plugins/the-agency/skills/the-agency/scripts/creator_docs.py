"""Read-only, local Creator Docs lookup. Python stdlib; Git is optional.

No persistent index, network, checkout changes, YAML evaluation or API calls.
Raw source is evidence, not executable instructions or production acceptance.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess


DEFAULT_ROOT = os.environ.get("CREATOR_DOCS_DIR", "creator-docs")
DOC_PREFIX = "content/en-us"
EXTENSIONS = {".md", ".yaml", ".yml", ".json"}
MAX_BYTES = 2 * 1024 * 1024
MAX_TREE_BYTES = 4 * 1024 * 1024
MAX_WALK_FILES = 20000  # enumeration cap only; title reads are bounded separately by scan_limit


def absolute(path: Path) -> str:
    return path.resolve().as_posix()


class Corpus:
    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()
        self.repo_head = None
        self.git_error = None
        top, error = self.git("rev-parse", "--show-toplevel")
        if error or Path(top.decode().strip()).resolve() != self.root:
            self.git_error = error or "Source root is not the Git repository root."
        else:
            head, error = self.git("rev-parse", "--verify", "HEAD")
            self.repo_head = head.decode().strip() if not error else None
            self.git_error = error

    def git(self, *args: str) -> tuple[bytes, str | None]:
        # In partial clones, a read may otherwise fetch missing objects. Disable
        # lazy fetch AND all transports. Never invoke a shell, helper or filter.
        env = os.environ.copy()
        for key in list(env):
            if key.startswith("GIT_"):
                del env[key]
        env.update(GIT_NO_LAZY_FETCH="1", GIT_TERMINAL_PROMPT="0",
                   GIT_OPTIONAL_LOCKS="0", GIT_NO_REPLACE_OBJECTS="1",
                   GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
        command = ["git", "--no-optional-locks", "-C", str(self.root),
                   "-c", "safe.directory=" + self.root.as_posix(),
                   "-c", "protocol.allow=never", "-c", "credential.helper=",
                   "-c", "core.fsmonitor=false", *args]
        try:
            result = subprocess.run(command, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, env=env, timeout=10)
        except (OSError, subprocess.TimeoutExpired) as exc:
            return b"", f"Local Git unavailable ({type(exc).__name__})."
        if result.returncode:
            # Avoid echoing arbitrary repository/helper diagnostics.
            return b"", f"Local Git {args[0]} failed (exit {result.returncode}); no fetch allowed."
        if len(result.stdout) > MAX_TREE_BYTES:
            return b"", "Git result exceeds the local lookup size limit; narrow the scope."
        return result.stdout, None

    @staticmethod
    def lexical(relative: str, *, scope: bool = False) -> tuple[str, tuple[str, ...]]:
        """Pure string validation: no filesystem access. Cheap enough for every enumerated path."""
        if "\\" in relative or any(c in relative for c in "\x00\n\r:"):
            raise ValueError("Use a repository-relative forward-slash documentation path.")
        parts = PurePosixPath(relative).parts
        if (not parts or PurePosixPath(relative).is_absolute() or ".." in parts
                or parts[:2] != ("content", "en-us")):
            raise ValueError("Path must stay under content/en-us in the selected source root.")
        if not scope and PurePosixPath(*parts).suffix.lower() not in EXTENSIONS:
            raise ValueError("Only Markdown, YAML and JSON documentation is supported.")
        return PurePosixPath(*parts).as_posix(), parts

    def path(self, relative: str, *, scope: bool = False) -> tuple[str, Path]:
        relative, parts = self.lexical(relative, scope=scope)
        target = self.root.joinpath(*parts)
        # Reject every symlink, including a broken one; never inspect its target.
        current = self.root
        for part in parts:
            current = current / part
            if current.is_symlink() or getattr(current, "is_junction", lambda: False)():
                raise ValueError("Documentation symlinks are not followed.")
        if not target.resolve().is_relative_to(self.root):
            raise ValueError("Resolved documentation path escapes the source root.")
        return relative, target

    def base(self) -> dict:
        return {"source_root": absolute(self.root), "repo_head": self.repo_head,
                "verified_at": datetime.now(timezone.utc).isoformat(),
                "git_note": self.git_error,
                "authority": "Local documentation snapshot; not installed Studio or runtime evidence."}

    def lookup(self, relative: str, member: str | None = None) -> dict:
        relative, target = self.path(relative)
        record = {**self.base(), "source_path": absolute(target),
                  "relative_path": relative, "kind": kind(relative),
                  "availability": "unknown", "content_hash": None,
                  "tracked_at_head": None, "head_blob": None}
        entry_error = None
        if self.repo_head:
            # -z keeps non-ASCII names unquoted; compare the exact decoded path.
            tree, entry_error = self.git("ls-tree", "-z", self.repo_head, "--", relative)
            if not entry_error:
                record["tracked_at_head"] = bool(tree)
                if tree:
                    entry = tree.split(b"\0", 1)[0]
                    header, _, raw_name = entry.partition(b"\t")
                    name = raw_name.decode("utf-8", errors="replace")
                    mode, objtype, oid = header.decode("ascii", errors="replace").split()
                    if name != relative or objtype != "blob" or mode == "120000":
                        record["reason"] = "Not a regular documentation blob at HEAD."
                        return record
                    record["head_blob"] = oid
        data = None
        try:
            if target.is_file():
                record["availability"] = "materialized"
                with target.open("rb") as handle:
                    data = handle.read(MAX_BYTES + 1)
            elif record["head_blob"]:
                size, error = self.git("cat-file", "-s", record["head_blob"])
                if error:
                    record.update(availability="unavailable-locally", reason=error)
                    return record
                if int(size) > MAX_BYTES:
                    record.update(availability="git-object", reason="Source exceeds 2 MiB read limit.")
                    return record
                data, error = self.git("cat-file", "blob", record["head_blob"])
                if error:
                    record.update(availability="unavailable-locally", reason=error)
                    return record
                record["availability"] = "git-object"
            else:
                record.update(availability="unavailable-locally" if record["tracked_at_head"] is False else "unknown",
                              reason=entry_error or self.git_error or "No materialized file or entry at this HEAD; API existence is unknown.")
                return record
        except (OSError, ValueError) as exc:
            record.update(availability="unknown", reason=f"Local read failed ({type(exc).__name__}).")
            return record
        if len(data) > MAX_BYTES:
            record["reason"] = "Source exceeds 2 MiB read limit; not returned or hashed."
            return record
        record["content_hash"] = "sha256:" + hashlib.sha256(data).hexdigest()
        # The blob hash distinguishes a modified working copy from the recorded HEAD.
        if record["head_blob"] and len(record["head_blob"]) == 40:
            blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
            record["matches_head_blob"] = blob == record["head_blob"]
        try:
            source = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            record["reason"] = "Source is not UTF-8; bytes are hashed but content is not decoded."
            return record
        record.update(title_hint=title_hint(source, target.suffix),
                      metadata_policy="Raw source retained; no YAML/JSON metadata interpretation or field filtering.")
        if member:
            if target.suffix.lower() not in {".yaml", ".yml"}:
                record.update(member_status="unsupported-format", requested_member=member,
                              reason="Exact member selection supports generated Engine YAML only; omit --member for raw source.")
            else:
                record.update(select_member(source, member))
        else:
            record["content"] = source
        return record

    def search(self, query: str, scope: str, limit: int = 5, scan_limit: int = 300) -> dict:
        relative, directory = self.path(scope, scope=True)
        if not query.strip() or len(query) > 200:
            raise ValueError("Search needs 1-200 characters.")
        if not 1 <= limit <= 20 or not 1 <= scan_limit <= 2000:
            raise ValueError("limit must be 1-20 and scan-limit must be 1-2000.")
        paths, warnings = set(), []
        if self.repo_head:
            tree, error = self.git("ls-tree", "-r", "--name-only", "-z", self.repo_head, "--", relative)
            if error:
                warnings.append(error)
            else:
                for raw in tree.split(b"\0"):
                    if not raw:
                        continue
                    name = raw.decode("utf-8", errors="replace")
                    if PurePosixPath(name).suffix.lower() in EXTENSIONS:
                        paths.add(name)
        walked = 0
        local_cap = False
        if directory.is_dir():
            for folder, dirs, files in os.walk(directory, followlinks=False):
                dirs[:] = sorted(d for d in dirs if not (Path(folder) / d).is_symlink()
                                 and not getattr(Path(folder) / d, "is_junction", lambda: False)()
                                 and (Path(folder) / d).resolve().is_relative_to(self.root))
                for name in sorted(files):
                    candidate = Path(folder) / name
                    if candidate.suffix.lower() in EXTENSIONS:
                        paths.add(candidate.relative_to(self.root).as_posix())
                        walked += 1
                        if walked >= MAX_WALK_FILES:
                            local_cap = True
                            break
                if local_cap:
                    break
        # Cheap string-only validation for every enumerated path. Filesystem
        # (symlink/resolve) checks run only for paths that are returned or read.
        terms = query.casefold().split()
        ordered, unsafe = [], 0
        for p in sorted(paths):
            try:
                self.lexical(p)
                ordered.append(p)
            except ValueError:
                unsafe += 1
        if unsafe:
            warnings.append(f"Skipped {unsafe} enumerated path(s) that failed lexical validation.")
        folded = {p: p.casefold() for p in ordered}
        path_hits = [p for p in ordered if all(term in folded[p] for term in terms)]
        found = {}
        # Title budget rule (deterministic): spend it first on paths containing at
        # least one query term (alphabetical), then on an even stride across the
        # remaining sorted paths, so a late directory is not starved by the budget.
        hit_set = set(path_hits)
        partial = [p for p in ordered if p not in hit_set and any(term in folded[p] for term in terms)]
        partial_set = set(partial)
        rest = [p for p in ordered if p not in hit_set and p not in partial_set]
        stride = max(1, -(-len(rest) // max(1, scan_limit - len(partial))))
        title_order = partial + [rest[i] for offset in range(stride) for i in range(offset, len(rest), stride)]
        titles, scanned = {}, 0
        # Path hits get titles (for display) only when they are returned; they
        # cost at most `limit` extra reads and are counted in title_headers_read.
        for p in title_order:
            if scanned >= scan_limit:
                break
            try:
                _, target = self.path(p)
                if not target.is_file():
                    continue
                scanned += 1
                with target.open("rb") as handle:
                    title = title_hint(handle.read(16384).decode("utf-8-sig", errors="replace"), target.suffix)
                titles[p] = (title, target)
            except (OSError, ValueError):
                warnings.append(f"Skipped unreadable or unsafe source: {absolute(self.root / p)}")
        title_hits = sorted(p for p, (title, _) in titles.items()
                            if title and all(term in title.casefold() for term in terms))
        candidates = path_hits + [p for p in title_hits if p not in hit_set]
        selected = []
        for p in candidates:
            if len(selected) >= limit:
                break
            try:
                _, target = self.path(p)
            except ValueError:
                warnings.append(f"Skipped unsafe source: {(self.root / p).as_posix()}")
                continue
            title = titles.get(p, (None, None))[0]
            if p in hit_set and p not in titles and target.is_file():
                try:
                    with target.open("rb") as handle:
                        title = title_hint(handle.read(16384).decode("utf-8-sig", errors="replace"), target.suffix)
                    scanned += 1
                except OSError:
                    title = None
            matched_title = bool(title and all(term in title.casefold() for term in terms))
            row = {"source_path": absolute(target), "relative_path": p,
                   "match": ("path+title" if matched_title else "path") if p in hit_set else "title"}
            if p not in hit_set or matched_title:
                row["title_hint"] = title
            selected.append(row)
        matched = len(candidates)
        return {**self.base(), "query": query, "scope_path": absolute(directory),
                "results": selected, "matched_paths": matched, "result_limit": limit,
                "results_truncated": matched > limit, "enumerated_paths": len(paths),
                "title_headers_read": scanned, "title_scan_limit": scan_limit,
                "title_selection_rule": "Titles are read for paths containing a query term first (alphabetical), then remaining sorted paths in even-stride passes (every Nth path, then the next offset), until the scan limit of materialized files is read; path matches also read their own title when returned.",
                "search_complete": False, "warnings": warnings,
                "coverage": "Paths from local HEAD plus bounded working-tree walk; only materialized title headers are read within the scan limit. Body/API member text and unavailable objects are not searched. Filesystem safety is checked only for returned/read paths, so matched_paths counts lexically valid candidates. Use explicit lookup for revision, availability and raw metadata; no matches do not establish absence.",
                "working_tree_walk_capped": local_cap}


def kind(path: str) -> str:
    if "/reference/engine/" in path:
        return "engine-api"
    if "/reference/cloud/" in path or "/cloud/" in path and path.endswith((".json", ".yaml", ".yml")):
        return "cloud-schema"
    if "/includes/" in path:
        return "include"
    return "tutorial" if "/tutorials/" in path else "guide"


def title_hint(source: str, suffix: str) -> str | None:
    # Hints only: keep the authoritative metadata unchanged in lookup content.
    key = "title" if suffix.lower() == ".md" else "name"
    match = re.search(r"^" + key + r":\s*([^\r\n]+)", source[:16384], re.MULTILINE)
    return match.group(1).strip().strip("\"'") if match else None


LINE_SPLIT = re.compile(r"[^\r\n]*(?:\r\n|\n|\r)|[^\r\n]+")


def physical_lines(source: str) -> list[str]:
    """Split on CRLF, LF or CR only (not U+2028, VT, FF, NEL...), keeping line ends."""
    return LINE_SPLIT.findall(source)


def select_member(source: str, member: str) -> dict:
    lines = physical_lines(source)
    section, header_end = None, len(lines)
    for index, line in enumerate(lines):
        if re.match(r"^(properties|methods|events|callbacks):", line):
            section = line.split(":", 1)[0]
            header_end = min(header_end, index)
        elif re.match(r"^\S", line) and not line.startswith("#"):
            section = None
        match = re.match(r"^  - name: (.+?)\s*$", line)
        if section and match and match.group(1).strip("\"'") == member:
            end = index + 1
            while end < len(lines) and not re.match(r"^(?:  - name:|\S)", lines[end]):
                end += 1
            return {"requested_member": member, "member_status": "found", "section": section,
                    "line_start": index + 1, "line_end": end,
                    "entity_metadata_raw": "".join(lines[:header_end]),
                    "content": "".join(lines[index:end]),
                    "selection_note": "Exact generated-YAML block including tags, security, capabilities, parameters and deprecation text as present. Omit --member for full source."}
    return {"requested_member": member, "member_status": "not-found",
            "reason": "No exact generated-YAML member block matched; omit --member to inspect raw source. No API absence inferred."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=DEFAULT_ROOT, help="Absolute local Creator Docs repository root")
    commands = parser.add_subparsers(dest="command", required=True)
    lookup = commands.add_parser("lookup", help="Read one exact documentation path without fetching")
    lookup.add_argument("path")
    lookup.add_argument("--member", help="Exact Engine YAML member name, e.g. RemoteEvent:FireServer")
    search = commands.add_parser("search", help="Bounded path/title candidates; no body search")
    search.add_argument("query")
    search.add_argument("--scope", required=True, help="Repository-relative documentation directory")
    search.add_argument("--limit", type=int, default=5)
    search.add_argument("--scan-limit", type=int, default=300)
    args = parser.parse_args()
    try:
        corpus = Corpus(args.root)
        result = corpus.lookup(args.path, args.member) if args.command == "lookup" else corpus.search(args.query, args.scope, args.limit, args.scan_limit)
    except ValueError as exc:
        parser.error(str(exc))
    # JSON escapes preserve Unicode after decoding and work in Windows pipes
    # whose console encoding cannot directly emit every documentation character.
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
