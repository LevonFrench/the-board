"""Fetch the upstream files named in references/source-lock.json into vendor/, at the pinned commit, byte for byte, then verify them.

Writes only vendor/ and runs no upstream code. Needs Git and network access. Line-ending conversion stays off because the lock pins exact bytes.
"""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor"
SAFE_GIT = ["git", "-c", "core.hooksPath=/dev/null", "-c", "protocol.ext.allow=never"]


def git(*args, stdin=None):
    subprocess.run(SAFE_GIT + list(args), input=stdin, text=True, encoding="utf-8", capture_output=True, check=True)


def fetch_files(repository, commit, relative_paths, folder):
    patterns = "".join("/" + rel.removeprefix("vendor/") + "\n" for rel in relative_paths)
    git("clone", "--quiet", "--no-checkout", "--filter=blob:none", "-c", "core.autocrlf=false", "-c", "core.longpaths=true", repository, str(folder))
    git("-C", str(folder), "sparse-checkout", "set", "--no-cone", "--stdin", stdin=patterns)
    git("-C", str(folder), "checkout", "--quiet", commit)


def main():
    lock = json.loads((ROOT / "references/source-lock.json").read_text(encoding="utf-8"))
    if VENDOR.exists():
        print(f"Already present, left alone: {VENDOR}", file=sys.stderr)
        return 2
    try:
        fetch_files(lock["repository"], lock["commit"], lock["files"], VENDOR)
    except (OSError, subprocess.CalledProcessError) as error:
        print(f"Could not fetch the pinned upstream: {getattr(error, 'stderr', '') or error}", file=sys.stderr)
        print(f"Delete {VENDOR} before trying again.", file=sys.stderr)
        return 2
    return subprocess.run([sys.executable, "-B", str(ROOT / "scripts/catalog.py"), "--verify"], check=False).returncode


if __name__ == "__main__":
    sys.exit(main())
