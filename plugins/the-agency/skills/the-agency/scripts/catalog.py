"""Read-only metadata discovery. No repository updates or discovered code execution.

Exit codes: 0 normally, even when a provider is missing or errored (the output
then carries "complete": false, "providers_degraded" and warnings). With
--strict the exit code is 2 when any provider is missing or errored, and 1 is
left to argparse/uncaught errors. Per-file warnings never change the exit code.
"""
import argparse
import hashlib
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

SKIP = {".git", "node_modules", "__pycache__", ".venv", "scripts", "assets"}
PERSONA_SKIP = {"node_modules", "__pycache__"}  # dot-directories are skipped as well
FIELDS = re.compile(r"^(name|description):[ \t]*(.*)$")
BLOCK_INDICATOR = re.compile(r"^[>|][+-]?[0-9]?[ \t]*(?:#.*)?$")
COMMENT = re.compile(r"[ \t]+#.*$")
MAX_READ_BYTES = 512 * 1024
KINDS = {"skills": "skill", "personas": "persona", "roles": "role",
         "workflows": "workflow", "methods": "method"}


def normalized(value):
    """Exclusion-matching key: NFKC, invisible format characters (U+200B, U+FEFF, ...) removed,
    casefolded and stripped, so look-alike and zero-width spellings of a name still match."""
    text = unicodedata.normalize("NFKC", str(value))
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Cf")
    return unicodedata.normalize("NFKC", text.casefold()).strip()


def _closing_quote(text, quote):
    """Index just past the closing quote of a quoted scalar, or None if unterminated."""
    i = 1
    while i < len(text):
        if quote == '"' and text[i] == "\\":
            i += 2
            continue
        if text[i] == quote:
            if quote == "'" and text[i + 1:i + 2] == "'":
                i += 2
                continue
            return i + 1
        i += 1
    return None


def _quoted(value, continuation):
    """Decode a (possibly wrapped) quoted scalar; trailing ' # comment' is allowed."""
    quote = value[0]
    text = value
    pending = list(continuation)
    end = _closing_quote(text, quote)
    while end is None and pending:
        text = text + " " + pending.pop(0)
        end = _closing_quote(text, quote)
    if end is None:
        raise ValueError("unterminated quoted metadata scalar")
    rest = text[end:]
    if rest.strip() and not rest.lstrip().startswith("#"):
        raise ValueError("unexpected text after quoted metadata scalar")
    body = text[:end]
    if quote == '"':
        return json.loads(body)  # Unsupported YAML escapes are reported, not guessed.
    return body[1:-1].replace("''", "'")


def metadata(text):
    """Read common scalar/block skill frontmatter, rejecting unsupported values.

    Values are stripped; unquoted scalars lose a trailing ' # comment' and gain
    the continuation lines of a wrapped plain scalar.
    """
    lines = text.lstrip("﻿").splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("missing frontmatter")
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        raise ValueError("unclosed frontmatter")
    fields = {}
    i = 1
    while i < end:
        match = FIELDS.match(lines[i])
        if not match:
            i += 1
            continue
        key, value = match.group(1), match.group(2).strip()
        if key in fields:  # ambiguous identity: which duplicate would a reader trust? Skip the file.
            raise ValueError("duplicate top-level '" + key + ":' key in frontmatter; file skipped")
        i += 1
        # Continuation: blank or indented lines up to the next top-level line.
        raw_block = []
        while i < end and (not lines[i].strip() or lines[i][0].isspace()):
            raw_block.append(lines[i].strip())
            i += 1
        if BLOCK_INDICATOR.match(value) or not value:
            value = " ".join(part for part in raw_block if part).strip()
        elif value[0] in "\"'":
            value = _quoted(value, [part for part in raw_block if part])
        elif value[0] in "[{*&!":
            raise ValueError("unsupported metadata scalar")
        else:
            parts = [COMMENT.sub("", value).strip()]
            for part in raw_block:
                if part.startswith("#"):
                    continue  # whole-line comment inside the scalar
                parts.append(COMMENT.sub("", part).strip())
            value = " ".join(part for part in parts if part)
        if not isinstance(value, str):
            raise ValueError("metadata must be text")
        fields[key] = value.strip()
    if not fields.get("name") or not fields.get("description"):
        raise ValueError("missing name or description")
    return fields


def skill_files(root):
    seen = set()
    for current, dirs, files in os.walk(root, followlinks=True):
        resolved = Path(current).resolve()
        if resolved in seen:
            dirs[:] = []
            continue
        seen.add(resolved)
        dirs[:] = sorted(d for d in dirs if d not in SKIP)
        if "SKILL.md" in files:
            yield Path(current) / "SKILL.md"


def persona_files(root):
    data = json.loads((root / "divisions.json").read_text(encoding="utf-8-sig"))
    real_root = root.resolve()
    for division in sorted(data["divisions"]):
        directory = (root / division).resolve()
        if not directory.is_relative_to(real_root):
            raise ValueError("division escapes provider root")
        for current, dirs, files in os.walk(directory, followlinks=False):
            dirs[:] = sorted(d for d in dirs if not d.startswith(".") and d not in PERSONA_SKIP)
            for name in sorted(files):
                path = Path(current) / name
                if name.endswith(".md") and path.resolve().is_relative_to(real_root):
                    yield path


def brief_files(root):
    """Discover authored role/workflow briefs without traversing external links."""
    for current, dirs, files in os.walk(root, followlinks=False):
        directory = Path(current)
        dirs[:] = sorted(d for d in dirs if d not in SKIP and not d.startswith('.')
                         and (directory / d).resolve().is_relative_to(root.resolve()))
        for name in sorted(files):
            path = directory / name
            if name.endswith('.md') and path.resolve().is_relative_to(root.resolve()):
                yield path


def provider_root(provider):
    env = provider.get("root_env")
    override = os.environ.get(env, "").strip() if env else ""  # empty variable = unset
    raw = override or provider["root"]
    # "skill:roles" names a folder inside this skill, so the public copy needs no machine path.
    root = Path(__file__).resolve().parents[1] / raw[6:] if raw.startswith("skill:") else Path(raw).expanduser()
    if not root.is_absolute():
        raise ValueError("provider roots must be absolute: " + str(root))
    return root.resolve()


def folder_name(path):
    return path.parent.name if path.name == "SKILL.md" else path.stem


def read_capped(path):
    with path.open("rb") as handle:
        raw = handle.read(MAX_READ_BYTES + 1)
    if len(raw) > MAX_READ_BYTES:
        raise ValueError("exceeds the " + str(MAX_READ_BYTES) + "-byte read cap; skipped")
    return raw


def discover(config):
    records, warnings, health = [], [], []
    blocked = {normalized(name) for name in config.get("excluded_names", []) if normalized(name)}
    for provider in config["providers"]:
        state = {"id": str(provider.get("id", "?")), "root": str(provider.get("root", "")),
                 "status": "available", "entries": 0}
        if provider.get("revision"):
            state["revision"] = provider["revision"]
        health.append(state)
        try:
            root = provider_root(provider)
            state["root"] = str(root)
            if not root.is_dir():
                state["status"] = "missing"
                warnings.append("Missing provider: " + state["id"] + " at " + str(root))
                continue
            kind = KINDS.get(provider.get("kind"))
            if kind is None:
                raise ValueError("unsupported provider kind")
            if kind in {"skill", "method"}:
                paths = skill_files(root)
            elif kind == "persona":
                paths = persona_files(root)
            else:
                paths = brief_files(root)
            for path in paths:
                try:
                    raw = read_capped(path)
                    fm = metadata(raw.decode("utf-8-sig"))
                    folder = folder_name(path)
                    if blocked & {normalized(fm["name"]), normalized(folder)}:
                        continue
                    records.append({**fm, "kind": kind, "provider": state["id"], "folder": folder,
                                    "path": str(path.absolute()), "sha256": hashlib.sha256(raw).hexdigest()})
                    state["entries"] += 1
                except (OSError, UnicodeError, ValueError) as exc:
                    warnings.append(str(path.absolute()) + ": " + str(exc))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            state["status"] = "error"
            warnings.append(state["id"] + ": " + str(exc))
    return records, warnings, health


def select(records, query="", kind=None, provider=None):
    """Match query terms (any) against name, description and folder name; never the path."""
    terms = query.casefold().split()
    chosen = []
    for item in records:
        if kind and item["kind"] != kind:
            continue
        if provider and item["provider"] not in provider:
            continue
        haystack = " ".join(item.get(k, "") for k in ("name", "description", "folder")).casefold()
        if terms and not any(term in haystack for term in terms):
            continue
        chosen.append(item)
    merged = {}
    for item in chosen:
        key = (item["kind"], item["name"], item["sha256"])
        if key not in merged:
            merged[key] = {**item, "locations": []}
        location = {"provider": item["provider"], "path": item["path"]}
        if location not in merged[key]["locations"]:
            merged[key]["locations"].append(location)
    return sorted(merged.values(), key=lambda row: (row["kind"], row["name"], row["path"]))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", type=Path, default=Path(__file__).resolve().parents[1] / "references/providers.json")
    parser.add_argument("--skills-root", action="append", default=[])
    parser.add_argument("--query", default="", help="terms matched (any) against name, description and folder name; not the path")
    parser.add_argument("--kind", choices=sorted(KINDS.values()))
    parser.add_argument("--provider", action="append")
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true",
                        help="exit 2 when any provider is missing or errored (default exit is 0; see output 'complete')")
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8-sig"))
    if config.get("schema_version") != 1:
        parser.error("unsupported registry schema")
    for i, root in enumerate(args.skills_root):
        config["providers"].append({"id": "extra-" + str(i + 1), "kind": "skills", "root": root})
    records, warnings, health = discover(config)
    rows = select(records, args.query, args.kind, args.provider)
    degraded = [h["id"] for h in health if h["status"] != "available"]
    output = {"providers": health, "complete": not degraded, "providers_degraded": degraded,
              "warnings": warnings, "matches": len(rows),
              "notice": "Metadata candidates only; read full sources and verify execution separately."}
    if not args.summary:
        output["entries"] = rows
    if args.json or args.summary:
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        for row in rows:
            print(row["kind"] + " | " + row["name"] + " | " + row["description"][:200] + " | " + row["path"])
        print(str(len(rows)) + " candidates. " + output["notice"], file=sys.stderr)
        for warning in warnings:
            print("Warning: " + warning, file=sys.stderr)
    if degraded:
        print("INCOMPLETE: provider(s) missing or errored: " + ", ".join(degraded)
              + (" (--strict: exit 2)" if args.strict else ""), file=sys.stderr)
        if args.strict:
            return 2
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
