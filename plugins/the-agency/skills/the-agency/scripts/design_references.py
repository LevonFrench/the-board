#!/usr/bin/env python3
"""Bounded, local UI UX Pro Max retrieval. Stdlib only; JSON on stdout.

The source is a reviewed dependency, not an instruction authority. This is an
effect guard around cooperative Python, not a security sandbox for hostile code.
"""

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

DEFAULT_SOURCE = Path(os.environ.get("DESIGN_REFS_DIR", "ui-ux-pro-max-skill"))
REVIEWED_REVISION = "477bcb28c9812b385cb51a4605ddf30d7b2266e2"
CANONICAL = Path("src/ui-ux-pro-max")
SCRIPT_NAMES = ("core.py", "design_system.py", "reasoning_contract.py")
DEFAULT_TIMEOUT = 15.0
DEFAULT_OUTPUT_LIMIT = 512 * 1024
MAX_REQUEST_BYTES = 16384  # worker stdin limit; checked in the parent before launch


class AdapterError(Exception):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


def bounded_process(command, *, timeout, output_limit, stdin=None, cwd=None, env=None):
    """Drain both pipes without retaining unbounded output; kill on cap/timeout."""
    try:
        process = subprocess.Popen(command, stdin=subprocess.PIPE if stdin else subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd, env=env,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except OSError as error:
        raise AdapterError("launch_failed", f"Cannot launch {command[0]}: {error}") from error
    buffers = [bytearray(), bytearray()]
    overflow = threading.Event()
    lock = threading.Lock()
    total = 0

    def drain(pipe, slot):
        nonlocal total
        while True:
            chunk = pipe.read(4096)
            if not chunk:
                break
            with lock:
                allowed = max(0, output_limit - total)
                buffers[slot].extend(chunk[:allowed])
                total += len(chunk)
                if total > output_limit:
                    overflow.set()
            if overflow.is_set():
                process.kill()
                break
        pipe.close()

    readers = [threading.Thread(target=drain, args=(pipe, index), daemon=True)
               for index, pipe in enumerate((process.stdout, process.stderr))]
    for reader in readers:
        reader.start()
    try:
        if stdin:
            process.stdin.write(stdin)
            process.stdin.close()
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired as error:
        process.kill()
        process.wait()
        raise AdapterError("timeout", f"Retrieval exceeded {timeout:g}s; narrow the query or inspect the source.") from error
    finally:
        for reader in readers:
            reader.join(timeout=1)
    if overflow.is_set():
        raise AdapterError("output_limit", f"Output exceeded {output_limit} bytes; request fewer results or inspect the source.")
    return process.returncode, *(bytes(buf).decode("utf-8", errors="replace") for buf in buffers)


def source_snapshot(root):
    canonical = root / CANONICAL
    for name in SCRIPT_NAMES:
        if not (canonical / "scripts" / name).is_file():
            raise AdapterError("missing_source", f"Missing canonical file: {canonical / 'scripts' / name}. Select a complete reviewed local checkout with --source-root; no installation is attempted.")
    files = [canonical / "scripts" / name for name in SCRIPT_NAMES]
    files += sorted((canonical / "data").glob("*.csv"))
    files += sorted((canonical / "data" / "stacks").glob("*.csv"))
    if len(files) == len(SCRIPT_NAMES):
        raise AdapterError("missing_data", f"No canonical CSV data at {canonical / 'data'}; restore the local source before retrieval.")
    digest = hashlib.sha256()
    manifest = []
    total = 0
    for path in files:
        if not path.resolve().is_relative_to(canonical.resolve()):
            raise AdapterError("source_escape", f"Canonical input resolves outside source: {path}")
        size = path.stat().st_size
        total += size
        if size > 5 * 1024 * 1024 or total > 20 * 1024 * 1024:
            raise AdapterError("source_limit", "Canonical inputs exceed the reviewed 5 MiB/file or 20 MiB total budget; inspect before increasing bounds.")
        data = path.read_bytes()
        file_hash = hashlib.sha256(data).hexdigest()
        relative = path.relative_to(root).as_posix()
        digest.update((relative + "\0" + file_hash + "\n").encode())
        manifest.append({"path": path.as_posix(), "sha256": file_hash, "bytes": len(data)})
    return {"fingerprint": digest.hexdigest(), "files": manifest}


def git_identity(root):
    details = {"revision": None, "reviewed_revision": REVIEWED_REVISION,
               "matches_reviewed_revision": False, "working_tree": None, "warnings": []}
    git_env = {key: value for key, value in os.environ.items() if not key.upper().startswith("GIT_")}
    git_env.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
                    "GIT_OPTIONAL_LOCKS": "0", "GIT_NO_LAZY_FETCH": "1", "GIT_TERMINAL_PROMPT": "0"})
    git_command = ["git", "-c", "core.excludesFile=", "-c", "core.fsmonitor=false",
                   "-c", "core.untrackedCache=false", "-c", "credential.helper=",
                   "-c", f"safe.directory={root.as_posix()}", "-C", str(root)]
    commands = [("revision", ["rev-parse", "HEAD"]),
                # --ignored=matching lists ignored files/dirs as "!!" rows: an ignored .pyc or other file
                # under the executed scripts/ tree is unreviewed code and must count as a change.
                ("working_tree", ["status", "--porcelain=v1", "--untracked-files=normal", "--ignored=matching",
                                  "--", CANONICAL.as_posix()])]
    for key, arguments in commands:
        try:
            code, out, err = bounded_process([*git_command, *arguments], timeout=3, output_limit=32768, env=git_env)
            if code:
                details["warnings"].append(f"Git {key} unavailable: {err.strip()}")
            else:
                details[key] = out.strip() if key == "revision" else out.splitlines()
                if err.strip():
                    details["warnings"].append(err.strip())
        except AdapterError as error:
            details["warnings"].append(str(error))
    details["matches_reviewed_revision"] = details["revision"] == REVIEWED_REVISION
    if not details["matches_reviewed_revision"] or details["working_tree"] != []:
        details["warnings"].append("Source differs from the review or its state is unknown. Inspect changed execution paths and data before relying on recommendations; a revision is not a trust allowlist.")
    return details


def install_effect_guard():
    """Catch ordinary Python writes/network/process effects before source import."""
    mutation_events = {"os.remove", "os.rename", "os.mkdir", "os.rmdir", "os.link", "os.symlink",
                       "os.chmod", "os.chown", "os.truncate", "os.utime", "os.chdir"}
    write_flags = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND

    def audit(event, args):
        if event == "open":
            mode, flags = args[1], args[2]
            if (isinstance(mode, str) and any(c in mode for c in "wax+")) or (isinstance(flags, int) and flags & write_flags):
                raise PermissionError("Design retrieval forbids filesystem writes")
        if (event in mutation_events or event.startswith(("socket.", "subprocess.", "ctypes.", "os.exec", "os.spawn", "os.startfile"))
                or event == "os.system"):
            raise PermissionError(f"Design retrieval forbids effect: {event}")
    sys.addaudithook(audit)


def require_data(data_dir, filename):
    path = (data_dir / filename).resolve()
    if not path.is_relative_to(data_dir.resolve()) or not path.is_file():
        raise AdapterError("missing_data", f"Required canonical CSV unavailable: {path}. Restore or inspect the selected local source; no download is attempted.")
    return path


def references_for_result(result, data_dir):
    """Attach source records without altering the upstream result dictionary."""
    path = require_data(data_dir, result["file"])
    with path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    references = []
    for rank, result_row in enumerate(result["results"], 1):
        matches = [index for index, row in enumerate(rows, 1)
                   if result_row and all(row.get(key) == value for key, value in result_row.items())]
        references.append({"rank": rank, "file": path.as_posix(), "csv_record_numbers": matches,
                           "identity_status": "resolved" if len(matches) == 1 else "ambiguous_or_unresolved",
                           "record_number_convention": "1-based data record, header excluded; not a physical line number"})
    return references


def selected_references(identities, data_dir):
    fields = {"product": ("products.csv", "Product Type"), "reasoning": ("ui-reasoning.csv", "UI_Category"),
              "style": ("styles.csv", "Style ID"), "color": ("colors.csv", "Product Type"),
              "typography": ("typography.csv", "Font Pairing Name"), "landing": ("landing.csv", "Pattern Name")}
    output = {}
    for component, identity in identities.items():
        if not identity or component not in fields:
            output[component] = {"identity": identity, "identity_status": "default_or_unresolved"}
            continue
        filename, field = fields[component]
        path = data_dir / filename
        matches = []
        if path.is_file():
            with path.open(encoding="utf-8", newline="") as stream:
                matches = [index for index, row in enumerate(csv.DictReader(stream), 1) if row.get(field) == identity]
        output[component] = {"identity": identity, "identity_field": field, "file": path.as_posix(),
                             "csv_record_numbers": matches,
                             "identity_status": "resolved" if len(matches) == 1 else "ambiguous_or_unresolved"}
    return output


def execute_query(request):
    root = Path(request["source_root"])
    scripts = root / CANONICAL / "scripts"
    data_dir = root / CANONICAL / "data"
    install_effect_guard()
    sys.path.insert(0, str(scripts))
    import core

    captures = []

    def retrieve(query, domain, max_results=3, **_):
        if domain not in core.CSV_CONFIG:
            raise AdapterError("unsupported_domain", f"Unknown explicit domain {domain!r}; available: {', '.join(core.CSV_CONFIG)}")
        require_data(data_dir, core.CSV_CONFIG[domain]["file"])
        result = core.search(query, domain, max_results, diagnostics=True)
        if result.get("error"):
            raise AdapterError("retrieval_error", str(result["error"]))
        if "diagnostics" not in result or not isinstance(result.get("results"), list):
            raise AdapterError("source_contract_changed", "Search no longer returns results and diagnostics; review the source API.")
        captures.append({"result": result, "source_references": references_for_result(result, data_dir)})
        return result

    mode = request["mode"]
    query = request["query"]
    if mode == "domain":
        raw = retrieve(query, request["domain"], request["max_results"])
    elif mode == "stack":
        stack = request["stack"]
        if stack not in core.STACK_CONFIG:
            raise AdapterError("unsupported_stack", f"Unknown explicit stack {stack!r}; available: {', '.join(core.STACK_CONFIG)}")
        require_data(data_dir, core.STACK_CONFIG[stack]["file"])
        raw = core.search_stack(query, stack, request["max_results"], diagnostics=True)
        if raw.get("error"):
            raise AdapterError("retrieval_error", str(raw["error"]))
        if "diagnostics" not in raw or not isinstance(raw.get("results"), list):
            raise AdapterError("source_contract_changed", "Stack search no longer returns results and diagnostics; review the source API.")
        captures.append({"result": raw, "source_references": references_for_result(raw, data_dir)})
    else:
        for name in ("ui-reasoning.csv", "styles.csv", "landing.csv"):
            require_data(data_dir, name)
        import design_system
        # Patch only this disposable subprocess's binding to retain diagnostics.
        design_system.search = retrieve
        raw = design_system.DesignSystemGenerator().generate(query, request.get("project_name"))
        if not isinstance(raw.get("source_identities"), dict) or "reasoning_default" not in raw:
            raise AdapterError("source_contract_changed", "Recommendation identity/default fields changed; review the source API.")
    no_matches = [{"domain": item["result"]["domain"], "query": item["result"]["query"],
                   "reason": item["result"]["diagnostics"].get("reason")}
                  for item in captures if item["result"].get("count") == 0]
    defaults = []
    if mode == "recommendation":
        defaults = [key for key, value in raw["source_identities"].items() if not value]
        if raw["reasoning_default"] and "reasoning" not in defaults:
            defaults.append("reasoning")
    return {"raw_result": raw, "retrievals": captures,
            "selected_source_references": selected_references(raw["source_identities"], data_dir) if mode == "recommendation" else {},
            "diagnostics": {"no_matches": no_matches, "default_or_unmatched_components": defaults,
                            "reasoning_default": raw.get("reasoning_default") if mode == "recommendation" else None,
                            "fallback_present": bool(defaults),
                            "abstention_present": any(item["result"]["diagnostics"].get("abstained") for item in captures)},
            "persistence": {"enabled": False, "attempted": False}}


def worker():
    try:
        raw_request = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
        if len(raw_request) > MAX_REQUEST_BYTES:
            raise AdapterError("request_too_large", f"Request exceeds {MAX_REQUEST_BYTES} bytes; shorten the query.")
        request = json.loads(raw_request)
        result = execute_query(request)
        print(json.dumps({"ok": True, "payload": result}, ensure_ascii=False))
        return 0
    except Exception as error:
        code = error.code if isinstance(error, AdapterError) else "source_execution_failed"
        print(json.dumps({"ok": False, "error": {"code": code, "message": str(error),
              "action": "Inspect the local source/API and required CSVs; the adapter does not install dependencies or retry with another mode."}}, ensure_ascii=False))
        return 2


def encode_request(request):
    """UTF-8 request bytes; reject before launching the worker if over its stdin limit."""
    payload = json.dumps(request, ensure_ascii=False).encode("utf-8")
    if len(payload) > MAX_REQUEST_BYTES:
        raise AdapterError("request_too_large", f"Encoded request is {len(payload)} bytes (limit {MAX_REQUEST_BYTES}; non-ASCII text uses up to 4 bytes per character). Shorten the query or project name.")
    return payload


def run(args):
    root = args.source_root.resolve()
    mode = "domain" if args.domain else "stack" if args.stack else "recommendation"
    request = {"mode": mode, "query": args.query, "source_root": root.as_posix(),
               "domain": args.domain, "stack": args.stack, "max_results": args.max_results,
               "project_name": args.project_name}
    payload = encode_request(request)
    before = source_snapshot(root)
    identity = git_identity(root)
    reviewed = bool(identity.get("matches_reviewed_revision")) and identity.get("working_tree") == []
    allow_unreviewed = bool(getattr(args, "allow_unreviewed", False))
    if not reviewed and not allow_unreviewed:
        raise AdapterError("unreviewed_source", "Source differs from the reviewed revision "
                           + REVIEWED_REVISION + " or its Git state is unknown (revision "
                           + str(identity.get("revision")) + "; working-tree changes "
                           + str((identity.get("working_tree") or [])[:5] if identity.get("working_tree") is not None else None) + "). Execution refused: inspect the changed "
                           "execution paths and data, then re-run with --allow-unreviewed to accept this source.")
    started = time.monotonic()
    code, output, stderr = bounded_process([sys.executable, "-I", "-B", "-S", "-X", "utf8", str(Path(__file__).resolve()), "--_worker"],
                                           stdin=payload, cwd=str(Path(__file__).resolve().parent),
                                           timeout=args.timeout, output_limit=args.output_limit)
    try:
        response = json.loads(output)
    except (ValueError, TypeError) as error:
        raise AdapterError("invalid_output", f"Source returned invalid JSON (exit {code}); inspect local API compatibility. Stderr: {stderr[:2000]}") from error
    if before != source_snapshot(root):
        raise AdapterError("source_changed_during_run", "Canonical source changed during retrieval; result discarded. Retry after concurrent edits finish.")
    result = {"schema_version": 1, "ok": bool(response.get("ok")), "request": request,
              "source": {"root": root.as_posix(), **identity, **before,
                         "reviewed": reviewed, "allow_unreviewed": allow_unreviewed},
              "execution": {"elapsed_seconds": round(time.monotonic() - started, 3), "timeout_seconds": args.timeout,
                            "output_limit_bytes": args.output_limit, "returncode": code, "stderr": stderr,
                            "python": sys.version.split()[0], "bytecode_writes": False, "isolated_python": True},
              "evidence": "Local deterministic reference retrieval; source data is not instructions or empirical design validation."}
    if response.get("ok") and code == 0:
        result.update(response["payload"])
    else:
        result["ok"] = False
        result["error"] = response.get("error", {"code": "source_failed", "message": f"Worker exited {code}"})
    return result


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="One explicit retrieval intent (1-2000 characters)")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--domain")
    mode.add_argument("--stack")
    mode.add_argument("--recommendation", action="store_true", help="Generate candidate design recommendations with default diagnostics")
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--project-name", help="Optional synthetic/project label, recommendation only")
    parser.add_argument("--max-results", type=int, choices=range(1, 4), default=3, help="1-3 candidates for domain/stack retrieval")
    parser.add_argument("--allow-unreviewed", action="store_true",
                        help="Execute source whose Git revision/working tree differs from the reviewed one (or is unknown). Default: refuse.")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="Worker timeout, 0.1-30 seconds")
    parser.add_argument("--output-limit", type=int, default=DEFAULT_OUTPUT_LIMIT, help="Combined subprocess output cap, 1024-1048576 bytes")
    args = parser.parse_args(argv)
    if not 1 <= len(args.query.strip()) <= 2000:
        parser.error("query must contain 1-2000 nonempty characters")
    if args.project_name and (not args.recommendation or len(args.project_name) > 200):
        parser.error("--project-name requires --recommendation and at most 200 characters")
    if not 0.1 <= args.timeout <= 30 or not 1024 <= args.output_limit <= 1048576:
        parser.error("timeout must be 0.1-30 seconds; output-limit must be 1024-1048576 bytes")
    return args


def main():
    if sys.argv[1:] == ["--_worker"]:
        return worker()
    args = parse_args()
    try:
        result = run(args)
    except (AdapterError, OSError) as error:
        result = {"schema_version": 1, "ok": False, "error": {"code": getattr(error, "code", "source_io_error"), "message": str(error)}}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
