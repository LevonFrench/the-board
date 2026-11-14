"""Start every shipped script with --help. Catches a script that cannot even load on this system. Run from the repo root."""
import subprocess
import sys
from pathlib import Path

# The fetch script takes no options: any call would start a download.
SKIP = {"fetch_pinned_upstream.py"}


def main():
    root = Path(__file__).resolve().parents[2]
    scripts = sorted(p for p in root.glob("plugins/*/skills/*/scripts/*.py") if p.name not in SKIP and not p.name.startswith("test_"))
    failed = []
    for script in scripts:
        done = subprocess.run([sys.executable, "-B", str(script), "--help"], capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
        if done.returncode:
            failed.append(f"{script.relative_to(root).as_posix()}: exit {done.returncode}: {done.stderr.strip()[-200:]}")
    print(f"{len(scripts) - len(failed)} of {len(scripts)} scripts start")
    for line in failed:
        print(line)
    return 1 if failed or not scripts else 0


if __name__ == "__main__":
    sys.exit(main())
