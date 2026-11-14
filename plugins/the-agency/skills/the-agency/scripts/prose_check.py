#!/usr/bin/env python3
"""Check that a prose pass changed wording only: every protected span in the original is still there.

  python prose_check.py <before> <after>

Protected spans, compared as multisets: numbers (with units and percent signs), dates with a month name,
quoted strings, URLs,
markdown link targets, wikilinks, inline and fenced code, evidence-tier tags such as [primary] or
[UNSUPPORTED ...], and frontmatter. Headings must keep their order and level. Prints one JSON object
and exits 0 when nothing protected changed, 1 when something did, 2 on bad usage.

It proves the spans survived, not that the meaning did: a qualifier such as "about" or "may" is
prose, so the person accepting the pass still reads the change list.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

FENCE = re.compile(r"```.*?```", re.S)
PATTERNS = {
    "code": re.compile(r"`[^`\n]+`"),
    "url": re.compile(r"https?://[^\s)>\]]*[^\s)>\].,;:!?'\"]"),
    "link_target": re.compile(r"\]\(([^)\s]+)\)"),
    "wikilink": re.compile(r"\[\[[^\]]+\]\]"),
    "tier": re.compile(r"\[(?:primary|community|press|inference|UNKNOWN|UNSUPPORTED[^\]]*|DISPUTED[^\]]*)\]"),
    "quote": re.compile(r"\"[^\"\n]{3,}\"|“[^”\n]{3,}”"),
    "date": re.compile(r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sept?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?(?:\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}|\s+\d{1,2}(?:st|nd|rd|th)?\b|\s+\d{4})"),
    "number": re.compile(r"(?<![\w.])[-+]?\d[\d,]*(?:\.\d+)?(?:\s?(?:%|percent|[kKMGT]?B|ms|s|min|h|fps|Hz|kHz|dB|LUFS|px|x))?(?![\w])"),
}
HEADING = re.compile(r"(?m)^(#{1,6})\s+\S")


def frontmatter(text):
    if text.startswith("---\n") or text.startswith("---\r\n"):
        end = text.find("\n---", 4)
        if end != -1:
            return text[: end + 4], text[end + 4 :]
    return "", text


def spans(text):
    front, body = frontmatter(text.replace("\r\n", "\n"))
    fences = FENCE.findall(body)
    body = FENCE.sub(" ", body)
    found = {"frontmatter": Counter([front] if front else []), "fence": Counter(fences)}
    for name, pattern in PATTERNS.items():
        found[name] = Counter(m if isinstance(m, str) else m[0] for m in pattern.findall(body))
    found["headings"] = [m.group(1) for m in HEADING.finditer(body)]
    return found


def compare(before, after):
    a, b = spans(before), spans(after)
    changes = {}
    for name in a:
        if name == "headings":
            if a[name] != b[name]:
                changes[name] = {"before": a[name], "after": b[name]}
            continue
        lost, gained = a[name] - b[name], b[name] - a[name]
        if lost or gained:
            changes[name] = {"lost": sorted(lost.elements())[:20], "added": sorted(gained.elements())[:20]}
    return {"ok": not changes, "changes": changes,
            "counts": {k: (len(v) if isinstance(v, list) else sum(v.values())) for k, v in a.items()}}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] in ("-h", "--help"):
        print(__doc__.split("\n\n")[1])
        return 0
    if len(argv) != 2:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    try:
        before, after = (Path(p).read_text(encoding="utf-8") for p in argv)
    except OSError as error:
        print(json.dumps({"ok": False, "error": str(error)}))
        return 2
    report = compare(before, after)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
