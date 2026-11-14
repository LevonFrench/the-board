#!/usr/bin/env python3
"""Read-only validator for a Fieldbook folder (or one built HTML page).

Checks structure, config, topic frontmatter, links, private-path leaks, raw
provenance tags, superlatives, claim traces, uncompiled raw files, staleness,
count drift, status contradictions, ledger paths, money-row basis, orphan
pages, chat leftovers and personal data. It never writes and never runs
anything in the target; the only I/O is reading files as UTF-8.

Usage: check_fieldbook.py <fieldbook-root | page.html> [--json] [--release]
       [--canonical DIR ...] [--site DIR ...] [--max-files N] [--limit N]
Exit codes: 0 no errors, 1 errors found, 2 usage error.
"""
import argparse
import bisect
import datetime as dt
import fnmatch
import html as htmllib
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote

try:
    import yaml
except ImportError:
    yaml = None

CHECKS = ("structure", "config", "frontmatter", "links", "leaks", "raw_tags", "superlatives",
          "claim_trace", "uncompiled", "staleness", "counts", "status", "ledger_paths",
          "money_basis", "orphans", "conversational", "personal_data", "audience")
SEV_ORDER = {"error": 0, "warn": 1, "info": 2}
RELEASE_CHECKS = {"claim_trace", "uncompiled", "staleness", "leaks"}
SKIP_DIRS = {".git", "node_modules", ".next", "dist", "build", "__pycache__", ".venv", "venv",
             ".wrangler", ".astro", ".turbo", ".cache", ".pytest_cache", ".idea", ".vscode"}
MEDIA_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".ico", ".svg", ".psd", ".mp3", ".wav",
             ".flac", ".ogg", ".mp4", ".mov", ".mkv", ".avi", ".webm", ".zip", ".7z", ".rar", ".gz",
             ".tar", ".blend", ".blend1", ".fbx", ".obj", ".glb", ".gltf", ".exe", ".dll", ".pdf",
             ".ttf", ".otf", ".woff", ".woff2", ".pyc", ".lock", ".rbxl", ".rbxm", ".rbxlx"}
TEXT_RAW_EXT = {".md", ".txt", ".csv", ".json", ".html", ".htm", ".yml", ".yaml", ".xml", ".tsv"}
DATA_EXT = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".json"}
DATA_SKIP_NAMES = {"package.json", "package-lock.json", "tsconfig.json", "tsconfig.tsbuildinfo",
                   "next-env.d.ts", "components.json"}
MAX_TEXT = 8_000_000

ENUMS = {
    "subject_kind": ("market", "project-state", "archive", "household", "entity"),
    "mode": ("preview", "guided-auto", "manual-approval"),
    "external_research": ("none", "gap-only", "gap-only-primary-first"),
    "output_mode": ("both", "markdown-kb", "web-fieldbook", "web-app", "single-file"),
    "release_status": ("private", "review", "public"),
    "status": ("on-hold", "building", "published"),
}
WARN_KEYS = ("subject", "audience", "source_roots", "output_mode", "release_status")
INFO_KEYS = ("subject_kind", "exclude", "mode", "external_research", "last_user_direction", "status")
TOPIC_KEYS = ("title", "status", "sources", "local_evidence", "confidence", "updated", "open_questions")

LABELS = ("local-primary", "local-derived", "external-primary", "external-secondary", "search-extract",
          "lead-only", "restricted", "inference", "arithmetic", "contested", "missing", "unknown",
          "hypothesis", "not-checked")
_LABEL_ALT = "|".join(sorted((re.escape(x).replace(r"\-", "[- ]") for x in LABELS), key=len, reverse=True))
RAW_TAG_RE = re.compile(r"\[\s*(?:%s)(?:[\s,;:/|][^\]\n]{0,80})?\]" % _LABEL_ALT, re.I)
LABEL_WORD_RE = re.compile(r"\b(?:%s)\b" % _LABEL_ALT, re.I)


# ---------------------------------------------------------------- YAML

def _strip_comment(s):
    q = None
    for i, ch in enumerate(s):
        if q:
            if ch == q:
                q = None
        elif ch in "\"'" and (i == 0 or s[i - 1] in " \t:[,{-"):
            q = ch
        elif ch == "#" and (i == 0 or s[i - 1] in " \t"):
            return s[:i]
    return s


def _split_inline(s):
    parts, depth, q, cur = [], 0, None, []
    for ch in s:
        if q:
            cur.append(ch)
            if ch == q:
                q = None
        elif ch in "\"'":
            q = ch
            cur.append(ch)
        elif ch in "[{":
            depth += 1
            cur.append(ch)
        elif ch in "]}":
            depth -= 1
            cur.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    if "".join(cur).strip():
        parts.append("".join(cur))
    return parts


def _kv(s):
    q = None
    for i, ch in enumerate(s):
        if q:
            if ch == q:
                q = None
        elif ch in "\"'" and i == 0:
            q = ch
        elif ch == ":" and (i + 1 == len(s) or s[i + 1] in " \t"):
            key = s[:i].strip()
            if key[:1] in "\"'" and key[-1:] == key[:1] and len(key) > 1:
                key = key[1:-1]
            return key, True, s[i + 1:]
    return s, False, ""


def _scalar(s):
    s = s.strip()
    if not s:
        return None
    if len(s) > 1 and s[0] == '"' and s[-1] == '"':
        esc = {"n": "\n", "t": "\t"}
        return re.sub(r"\\(.)", lambda m: esc.get(m.group(1), m.group(1)), s[1:-1])
    if len(s) > 1 and s[0] == "'" and s[-1] == "'":
        return s[1:-1].replace("''", "'")
    if s[0] == "[" and s[-1] == "]":
        return [_scalar(p) for p in _split_inline(s[1:-1])]
    if s[0] == "{" and s[-1] == "}":
        out = {}
        for p in _split_inline(s[1:-1]):
            k, ok, v = _kv(p.strip())
            if ok:
                out[k] = _scalar(v)
        return out
    low = s.lower()
    if low in ("true", "yes"):
        return True
    if low in ("false", "no"):
        return False
    if low in ("null", "~"):
        return None
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    if re.fullmatch(r"-?\d+\.\d+", s):
        return float(s)
    return s


def _block(lines, i, indent):
    is_list = lines[i][1] == "-" or lines[i][1].startswith("- ")
    if is_list:
        out = []
        while i < len(lines) and lines[i][0] == indent and (lines[i][1] == "-" or lines[i][1].startswith("- ")):
            item = lines[i][1][1:].strip()
            if not item:
                i += 1
                if i < len(lines) and lines[i][0] > indent:
                    val, i = _block(lines, i, lines[i][0])
                    out.append(val)
                else:
                    out.append(None)
            elif _kv(item)[1] and item[0] not in "[{\"'":
                lines[i] = (indent + 2, item)
                val, i = _block(lines, i, indent + 2)
                out.append(val)
            else:
                out.append(_scalar(item))
                i += 1
        return out, i
    out = {}
    while i < len(lines) and lines[i][0] >= indent:
        if lines[i][0] > indent:
            i += 1
            continue
        key, ok, rest = _kv(lines[i][1])
        if not ok:
            i += 1
            continue
        rest = rest.strip()
        i += 1
        if rest in ("|", ">", "|-", ">-", "|+", ">+"):
            buf = []
            while i < len(lines) and lines[i][0] > indent:
                buf.append(lines[i][1])
                i += 1
            out[key] = ("\n" if rest[0] == "|" else " ").join(buf)
        elif rest == "":
            nxt = lines[i] if i < len(lines) else None
            if nxt and (nxt[0] > indent or (nxt[0] == indent and (nxt[1] == "-" or nxt[1].startswith("- ")))):
                out[key], i = _block(lines, i, nxt[0])
            else:
                out[key] = None
        else:
            out[key] = _scalar(rest)
    return out, i


def mini_yaml(text):
    """Parse key: value, nested maps, block lists and inline lists. Raises ValueError on garbage."""
    lines = []
    for raw in text.splitlines():
        s = _strip_comment(raw.rstrip())
        if not s.strip() or s.strip() in ("---", "..."):
            continue
        lines.append((len(s) - len(s.lstrip(" ")), s.strip()))
    if not lines:
        return {}
    data, i = _block(lines, 0, lines[0][0])
    if i < len(lines):
        raise ValueError("unparsed content near: " + lines[i][1][:60])
    return data


def load_yaml(text, use_pyyaml=True):
    """Return (data, error). Prefers PyYAML; falls back to mini_yaml."""
    err = None
    if use_pyyaml and yaml is not None:
        try:
            return yaml.safe_load(text), None
        except Exception as exc:
            err = str(exc).splitlines()[0] if str(exc) else type(exc).__name__
    try:
        return mini_yaml(text), None
    except Exception as exc:
        return None, err or str(exc)


FM_RE = re.compile(r"\A\ufeff?---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.S)


def split_frontmatter(text):
    """Return (dict or None, body offset, error). None means no frontmatter block."""
    m = FM_RE.match(text)
    if not m:
        return None, 0, None
    data, err = load_yaml(m.group(1))
    if not isinstance(data, dict):
        return {}, m.end(), err or "frontmatter is not a mapping"
    return data, m.end(), None


def to_date(v):
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", str(v))
    if m:
        try:
            return dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
    return None


# ---------------------------------------------------------------- text helpers

class Lines:
    """Map character offsets to 1-based line numbers."""

    def __init__(self, text):
        self.starts = [0] + [m.end() for m in re.finditer("\n", text)]

    def at(self, pos):
        return bisect.bisect_right(self.starts, pos)


def _blank(m):
    return re.sub(r"[^\n]", " ", m.group(0))


def mask_fences(text):
    """Blank fenced code blocks and inline code spans, keeping offsets and newlines."""
    text = re.sub(r"(?ms)^[ \t]*(```|~~~).*?^[ \t]*\1[^\n]*$", _blank, text)
    return re.sub(r"`[^`\n]*`", _blank, text)


def html_nocode(text):
    """Blank comments and script bodies; keep tags and offsets."""
    text = re.sub(r"(?s)<!--.*?-->", _blank, text)
    return re.sub(r"(?is)(<script\b[^>]*>)(.*?)(</script>)",
                  lambda m: m.group(1) + re.sub(r"[^\n]", " ", m.group(2)) + m.group(3), text)


def html_visible(text):
    """Visible text of an HTML page, one output line per input line."""
    t = html_nocode(text)
    t = re.sub(r"(?is)<(script|style|noscript|svg|head)\b.*?</\1>", _blank, t)
    t = re.sub(r"(?s)<[^>]*>", _blank, t)
    return "\n".join(htmllib.unescape(ln) for ln in t.split("\n"))


ATTR_RE = re.compile(r"""\b(href|src|poster)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>"']+))""", re.I)
STYLE_REGION_RE = re.compile(r"""(?is)<style\b[^>]*>(.*?)</style>|\bstyle\s*=\s*"([^"]*)"|\bstyle\s*=\s*'([^']*)'""")
SRCSET_RE = re.compile(r"""\bsrcset\s*=\s*(?:"([^"]*)"|'([^']*)')""", re.I)
CSS_URL_RE = re.compile(r"""url\(\s*(?:"([^"]*)"|'([^']*)'|([^)\s'"]*))\s*\)""", re.I)
MD_LINK_RE = re.compile(r"!?\[[^\]\n]*\]\(\s*(<[^>\n]*>|[^)\s]*(?:\([^)\s]*\)[^)\s]*)*)(?:\s+(?:\"[^\"\n]*\"|'[^'\n]*'))?\s*\)")
MD_REF_RE = re.compile(r"(?m)^[ \t]{0,3}\[[^\]\n]+\]:[ \t]*(<[^>\n]*>|\S+)")
SCHEME_RE = re.compile(r"^([A-Za-z][A-Za-z0-9+.\-]*):")


def html_links(text):
    """(target, offset) for every href, src and CSS url() outside comments and scripts."""
    t = html_nocode(text)
    out = []
    for m in ATTR_RE.finditer(t):
        out.append((m.group(2) if m.group(2) is not None else m.group(3) if m.group(3) is not None else m.group(4), m.start()))
    for m in SRCSET_RE.finditer(t):
        for cand in (m.group(1) if m.group(1) is not None else m.group(2)).split(","):
            parts = cand.split()
            if parts:
                out.append((parts[0], m.start()))
    for region in STYLE_REGION_RE.finditer(t):
        body = region.group(1) or region.group(2) or region.group(3) or ""
        base = region.start() + region.group(0).find(body) if body else region.start()
        for m in CSS_URL_RE.finditer(body):
            v = m.group(1) if m.group(1) is not None else m.group(2) if m.group(2) is not None else m.group(3)
            out.append((v, base + m.start()))
    return out


def md_links(text):
    t = mask_fences(text)
    out = []
    for m in MD_LINK_RE.finditer(t):
        out.append((m.group(1).strip("<>"), m.start()))
    for m in MD_REF_RE.finditer(t):
        out.append((m.group(1).strip("<>"), m.start()))
    return out


def norm_num(s):
    s = s.replace(",", "").strip().rstrip(".")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s


NUM_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")
SID_RE = re.compile(r"(?<![\w-])S\d{1,3}(?![\w-])")
CLAIM_PCT = re.compile(r"(?<![\w.])(\d{1,3}(?:\.\d+)?)\s?%")
CLAIM_USD = re.compile(r"\$\s?(\d[\d,]*(?:\.\d+)?)([kKmM]\b)?")
CLAIM_THOU = re.compile(r"(?<![\d,.$])\d{1,3}(?:,\d{3})+(?:\.\d+)?(?!\d)")
SELF_LABEL_RE = re.compile(r"\b(inference|arithmetic|hypothesis|not-checked|unknown|estimate[sd]?|calculated|computed)\b", re.I)
CODE_NOISE = [
    re.compile(r"""class(?:Name)?\s*=\s*(?:"[^"]*"|'[^']*'|\{[^}]*\})"""),
    re.compile(r"style\s*=\s*\{\{[^}]*\}\}"),
    re.compile(r"""style\s*=\s*"[^"]*\""""),
    re.compile(r"\b[\w-]+-\[[^\]]*\]"),
    re.compile(r"\b(?:rgba?|hsla?)\([^)]*\)"),
    re.compile(r"#[0-9a-fA-F]{3,8}\b"),
    re.compile(r"""\b(?:width|height|left|top|right|bottom|flex|margin\w*|padding\w*|inset|min\w+|max\w+|translate\w*|opacity|gap|size)\s*:\s*['"]?[\d.]+%"""),
]


def extract_claims(text, ids=True):
    """{(kind, norm): (display, offset, alt)} for percentages, dollars, thousands numbers and source IDs."""
    found = {}

    def add(kind, norm, disp, pos, alt=None):
        found.setdefault((kind, norm), (disp, pos, alt))

    for m in CLAIM_PCT.finditer(text):
        n = norm_num(m.group(1))
        if n not in ("0", "100"):
            add("number", n, m.group(0).replace(" ", ""), m.start())
    for m in CLAIM_USD.finditer(text):
        n = norm_num(m.group(1))
        if re.fullmatch(r"\d+", n) and (int(n) < 10 or 1900 <= int(n) <= 2100):
            continue
        alt = None
        if m.group(2):
            alt = norm_num(str(round(float(n) * (1000 if m.group(2) in "kK" else 1000000), 2)))
        add("number", n, m.group(0).replace(" ", ""), m.start(), alt)
    for m in CLAIM_THOU.finditer(text):
        add("number", norm_num(m.group(0)), m.group(0), m.start())
    if ids:
        for m in SID_RE.finditer(text):
            add("sid", m.group(0), m.group(0), m.start())
    return found


def sentence_at(line, start):
    left = max(line.rfind(". ", 0, start), line.rfind("? ", 0, start), line.rfind("! ", 0, start))
    right = min([x for x in (line.find(". ", start), line.find("? ", start), line.find("! ", start)) if x >= 0] or [len(line)])
    return line[left + 1:right + 1]


# ---------------------------------------------------------------- context

class Ctx:
    def __init__(self, target, args):
        self.args = args
        self.findings = []
        self.cache = {}
        self.notes = []
        t = Path(target)
        self.single_html = None
        if t.is_file() and t.suffix.lower() in (".html", ".htm"):
            self.single_html = t.resolve()
            self.root = self.single_html.parent
        else:
            self.root = t.resolve()
        self.page_mode = self.single_html is not None
        self.cfg = {}
        self.cfg_path = None
        self.cfg_error = None
        self.cfg_dir = self.root
        self.aliases = []
        self.excl_exact = set()
        self.excl_globs = []
        self.files = []
        self.files_truncated = False
        self.legacy = []
        if not self.page_mode:
            self._load_config()
        self._setup_excludes()
        self.layout_inferred = False
        self._setup_layout()
        self.walk_inventory()
        self.release = bool(args.release) or str(self.cget("release_status")[1]).lower() in ("review", "public")
        self.mode = self._mode()
        self.pages = self._pages()
        self.site_dirs = []
        self.site_files = []
        self._site()

    # ---- findings
    def disp(self, p):
        p = Path(p)
        try:
            return p.relative_to(self.root).as_posix()
        except ValueError:
            return p.as_posix()

    def add(self, check, sev, file, line, msg):
        f = self.disp(file) if isinstance(file, Path) else (file or ".")
        self.findings.append({"check": check, "severity": sev, "file": f, "line": int(line or 0), "message": msg})

    # ---- io
    def text(self, p):
        p = Path(p)
        if p in self.cache:
            return self.cache[p]
        t = read_file(p)
        self.cache[p] = t
        return t

    # ---- config
    def _load_config(self):
        for name in ("fieldbook.config.yml", "fieldbook.config.yaml"):
            p = self.root / name
            if p.is_file():
                self.cfg_path = p
                break
        if not self.cfg_path:
            return
        self.cfg_dir = self.cfg_path.parent
        data, err = load_yaml(read_file(self.cfg_path))
        if data is None and err:
            self.cfg_error = "config could not be parsed: " + err
        elif not isinstance(data, dict):
            self.cfg_error = "config is not a key: value mapping"
        else:
            self.cfg = data

    def cget(self, key):
        """(found, value) with fallbacks to the nested legacy shapes some old Fieldbooks use."""
        if key in self.cfg:
            return True, self.cfg[key]
        nested = self.cfg.get("fieldbook")
        if isinstance(nested, dict) and key in nested:
            if key not in self.aliases:
                self.aliases.append(key)
            return True, nested[key]
        if key == "source_roots":
            ls = self.cfg.get("local_sources")
            if isinstance(ls, dict) and "roots" in ls:
                if key not in self.aliases:
                    self.aliases.append(key)
                return True, ls["roots"]
        return False, None

    def source_root_entries(self):
        found, val = self.cget("source_roots")
        if not found or val is None:
            return []
        items = val if isinstance(val, list) else [val]
        out = []
        for it in items:
            p = it.get("path") if isinstance(it, dict) else it
            if isinstance(p, str) and p.strip():
                out.append(p.strip())
        return out

    def resolve_cfg_path(self, p):
        q = Path(os.path.expanduser(p))
        return Path(os.path.normpath(q if q.is_absolute() else self.cfg_dir / q))

    def _setup_excludes(self):
        found, val = self.cget("exclude")
        for e in (val if isinstance(val, list) else []):
            if not isinstance(e, str) or not e.strip():
                continue
            e = e.strip().replace("\\", "/")
            if "*" in e or "?" in e:
                base = os.path.normpath(self.cfg_dir / e).replace("\\", "/").lower()
                self.excl_globs.append(base)
                self.excl_globs.append(base.replace("**/", ""))
            elif "/" in e or e.startswith("."):
                self.excl_exact.add(Path(os.path.normpath(self.cfg_dir / e)))

    def excluded(self, p):
        if p in self.excl_exact:
            return True
        if self.excl_globs:
            s = p.as_posix().lower()
            return any(fnmatch.fnmatchcase(s, g) for g in self.excl_globs)
        return False

    # ---- layout
    def _setup_layout(self):
        r = self.root
        base = {"ledger": "source-ledger.md", "gaps": "gap-register.md", "coverage": "coverage-matrix.md",
                "backlog": "refresh-backlog.md", "editorial": "editorial-note.md",
                "inventory": "local-evidence-inventory.md", "topics": "topics", "raw": "raw", "output": "output"}
        if not self.page_mode and not (r / "topics").is_dir() and (r / ".wiki" / "wiki" / "topics").is_dir():
            base.update(topics=".wiki/wiki/topics", raw=".wiki/raw", output=".wiki/output")
            self.layout_inferred = True
        over = self.cfg.get("layout")
        overridden = set()
        if isinstance(over, dict):
            for k, v in over.items():
                if isinstance(v, str) and v.strip():
                    base[str(k)] = v.strip()
                    overridden.add(str(k))
        self.layout = {}
        for k, rel in base.items():
            p = r / rel
            if k not in overridden and k not in ("topics", "raw", "output") and not p.exists():
                for alt in ("evidence", ".wiki", "wiki"):
                    if (r / alt / rel).exists():
                        p = r / alt / rel
                        break
            self.layout[k] = p
        if not (self.layout["output"].is_dir()):
            for alt in ("outputs", "reports"):
                if (r / alt).is_dir():
                    self.layout["output"] = r / alt
                    break

    def find(self, rel):
        for alt in ("", "evidence/", ".wiki/", "wiki/"):
            if (self.root / (alt + rel)).exists():
                return self.root / (alt + rel)
        return self.root / rel

    def under(self, p, key):
        d = self.layout.get(key)
        if d is None:
            return False
        try:
            Path(p).relative_to(d)
            return True
        except ValueError:
            return False

    # ---- inventory
    def walk_inventory(self):
        if self.page_mode:
            self.files = [self.single_html]
            return
        self.files, self.files_truncated = walk_files(self, self.root, self.args.max_files)
        found, leg = self.cget("legacy")
        for e in (leg if isinstance(leg, list) else []):
            if isinstance(e, str) and e.strip():
                self.legacy.append(e.strip().replace("\\", "/"))

    def is_legacy(self, p):
        if not self.legacy:
            return False
        rel = self.disp(p).lower()
        for e in self.legacy:
            e = e.lower().strip("/")
            if e.startswith("./"):
                e = e[2:]
            if "*" in e:
                if fnmatch.fnmatchcase(rel, e):
                    return True
            elif rel == e or rel.startswith(e + "/"):
                return True
        return False

    def _mode(self):
        found, v = self.cget("output_mode")
        if isinstance(v, str) and v in ENUMS["output_mode"]:
            return v
        return "both" if self.cfg_path else "markdown-kb"

    def single_file_path(self):
        found, v = self.cget("single_file")
        if isinstance(v, str) and v.strip():
            return self.resolve_cfg_path(v)
        return None

    def _pages(self):
        if self.page_mode:
            return [self.single_html]
        if self.mode == "single-file":
            p = self.single_file_path()
            return [p] if p and p.is_file() else []
        return [f for f in self.files if f.suffix.lower() in (".html", ".htm") and not self.is_legacy(f)]

    def _site(self):
        dirs = []
        for s in self.args.site or []:
            p = Path(s)
            if p.is_dir():
                dirs.append(p.resolve())
            else:
                self.add("structure", "info", s, 0, "--site directory not found; skipped")
        d = self.root / "site"
        if not self.page_mode and d.is_dir() and self.mode != "single-file":
            dirs.append(d)
        seen = set()
        self.site_dirs = dirs
        for d in dirs:
            fs, trunc = walk_files(self, d, self.args.max_files)
            if trunc:
                self.add("claim_trace", "info", d, 0, "site scan truncated at --max-files %d" % self.args.max_files)
            for f in fs:
                if f in seen or self.is_legacy(f):
                    continue
                seen.add(f)
                ext = f.suffix.lower()
                if ext in (".html", ".htm"):
                    if f not in self.pages:
                        self.pages.append(f)
                elif ext in DATA_EXT and f.name not in DATA_SKIP_NAMES and not f.name.endswith((".d.ts", ".min.js")):
                    self.site_files.append(f)

    # ---- collections
    def md_files(self, under=None, skip_raw=False):
        out = []
        for f in self.files:
            if f.suffix.lower() != ".md" or self.is_legacy(f):
                continue
            if under is not None and not self.under(f, under):
                continue
            if skip_raw and self.under(f, "raw"):
                continue
            out.append(f)
        return out

    def topics(self):
        if "topics" in self.cache:
            return self.cache["topics"]
        out = []
        d = self.layout["topics"]
        if d.is_dir():
            for f in self.md_files(under="topics"):
                if f.name.startswith("_") or f.name.lower() == "readme.md":
                    continue
                text = self.text(f)
                fm, off, err = split_frontmatter(text)
                out.append({"path": f, "text": text, "fm": fm, "off": off, "err": err})
        self.cache["topics"] = out
        return out


def read_file(p):
    try:
        if os.path.getsize(p) > MAX_TEXT:
            return ""
        with open(p, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def walk_files(ctx, base, limit):
    """Files under base, pruning dependency and build dirs. Returns (files, truncated)."""
    base = Path(base)
    if base.is_file():
        return [base], False
    out = []
    for dp, dns, fns in os.walk(base):
        dpp = Path(dp)
        dns[:] = sorted(d for d in dns if d not in SKIP_DIRS and not ctx.excluded(dpp / d))
        for fn in sorted(fns):
            p = dpp / fn
            if ctx.excluded(p):
                continue
            out.append(p)
            if len(out) >= limit:
                return out, True
    return out, False


# ---------------------------------------------------------------- link resolution

def classify_link(target):
    """Return 'skip', 'external', 'anchor' or 'local'."""
    t = target.strip()
    if not t:
        return "skip"
    if t.startswith("#"):
        return "anchor"
    if t.startswith("//"):
        return "external"
    m = SCHEME_RE.match(t)
    if m:
        s = m.group(1).lower()
        if s in ("http", "https"):
            return "external"
        return "skip"
    if t == "/":
        return "skip"
    return "local"


def split_target(target):
    t = target.strip()
    frag = ""
    if "#" in t:
        t, frag = t.split("#", 1)
    if "?" in t:
        t = t.split("?", 1)[0]
    return unquote(t), unquote(frag)


def resolve_local(src, ctx, path_part):
    if path_part == "":
        return src
    if path_part.startswith("/"):
        return Path(os.path.normpath(ctx.root / path_part.lstrip("/")))
    return Path(os.path.normpath(src.parent / path_part))


_ID_CACHE = {}


def html_ids(ctx, p):
    if p not in _ID_CACHE:
        t = html_nocode(ctx.text(p))
        ids = set()
        for m in re.finditer(r"""\b(?:id|name)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>"']+))""", t, re.I):
            ids.add(m.group(1) or m.group(2) or m.group(3))
        _ID_CACHE[p] = ids
    return _ID_CACHE[p]


def exists(p):
    try:
        return p.exists()
    except OSError:
        return False


# ---------------------------------------------------------------- checks

def check_structure(ctx):
    if ctx.page_mode:
        return
    if ctx.files_truncated:
        ctx.add("structure", "info", ".", 0, "file scan truncated at --max-files %d; later checks cover the first files only" % ctx.args.max_files)
    if ctx.legacy:
        ctx.add("structure", "info", ".", 0, "legacy paths excluded from reader checks (%d): %s" % (len(ctx.legacy), ", ".join(ctx.legacy[:8])))
    if ctx.layout_inferred:
        ctx.add("structure", "info", ".", 0, "no topics/ folder; inferred .wiki layout (.wiki/wiki/topics, .wiki/raw, .wiki/output)")
    required = [("README.md", ctx.find("README.md")), ("guidance.md", ctx.find("guidance.md")),
                ("coverage-matrix.md", ctx.layout["coverage"]), ("gap-register.md", ctx.layout["gaps"]),
                ("source-ledger.md", ctx.layout["ledger"]), ("refresh-backlog.md", ctx.layout["backlog"]),
                ("editorial-note.md", ctx.layout["editorial"])]
    if ctx.source_root_entries():
        required.append(("local-evidence-inventory.md", ctx.layout["inventory"]))
    for name, p in required:
        if not p.is_file():
            ctx.add("structure", "error", name, 0, "required file missing: %s" % name)
    if not ctx.layout["topics"].is_dir():
        ctx.add("structure", "error", "topics/", 0, "required topics folder missing")
    if ctx.mode == "single-file":
        sf = ctx.single_file_path()
        if sf is None:
            ctx.add("structure", "error", "fieldbook.config.yml", 0, "output_mode single-file needs config single_file: <relative path>")
        elif not sf.is_file():
            ctx.add("structure", "error", sf, 0, "single_file target does not exist")
    elif ctx.mode in ("both", "web-fieldbook", "web-app"):
        sev = "warn" if ctx.mode == "web-app" else "error"
        for rel in ("index.html", "site/index.html"):
            if not (ctx.root / rel).is_file():
                ctx.add("structure", sev, rel, 0, "reader file missing for output_mode %s: %s" % (ctx.mode, rel))


def check_config(ctx):
    if ctx.page_mode:
        return
    if ctx.cfg_path is None:
        ctx.add("config", "warn", "fieldbook.config.yml", 0, "config file not found; checks assume defaults")
        return
    if ctx.cfg_error:
        ctx.add("config", "error", ctx.cfg_path, 0, ctx.cfg_error)
        return
    cp = ctx.cfg_path
    for a in ctx.aliases:
        ctx.add("config", "info", cp, 0, "old config shape: '%s' read from a nested block" % a)
    for key in WARN_KEYS:
        if not ctx.cget(key)[0]:
            ctx.add("config", "warn", cp, 0, "missing key: %s" % key)
    for key in INFO_KEYS:
        if not ctx.cget(key)[0]:
            ctx.add("config", "info", cp, 0, "missing optional key: %s" % key)
    for key, allowed in ENUMS.items():
        found, v = ctx.cget(key)
        if found and v is not None and v not in allowed:
            ctx.add("config", "warn", cp, 0, "%s: %r is not one of %s" % (key, v, " | ".join(allowed)))
    for key, typ in (("exclude", list), ("legacy", list), ("superlative_allow", list), ("layout", dict)):
        if key in ctx.cfg and ctx.cfg[key] is not None and not isinstance(ctx.cfg[key], typ):
            ctx.add("config", "warn", cp, 0, "%s should be a %s" % (key, typ.__name__))
    if ctx.mode == "single-file" and ctx.single_file_path() is None:
        ctx.add("config", "warn", cp, 0, "output_mode single-file needs single_file")
    found, v = ctx.cget("source_roots")
    if found and v is not None and not isinstance(v, (list, str)):
        ctx.add("config", "warn", cp, 0, "source_roots should be a list of paths")
    for entry in ctx.source_root_entries():
        r = ctx.resolve_cfg_path(entry)
        if not exists(r):
            ctx.add("config", "error", cp, 0, "source_roots entry does not resolve from the config file: %s -> %s" % (entry, r.as_posix()))
    st = ctx.cget("status")[1]
    if st == "on-hold":
        built = [p for p in ("index.html", "site/index.html") if (ctx.root / p).is_file()]
        sf = ctx.single_file_path()
        if sf is not None and sf.is_file():
            built.append(ctx.disp(sf))
        mode = ctx.cget("mode")[1]
        if built or mode == "guided-auto":
            why = ("reader output exists (%s)" % ", ".join(built)) if built else "mode is guided-auto"
            ctx.add("config", "warn", cp, 0, "status is on-hold but %s" % why)


def check_frontmatter(ctx):
    for t in ctx.topics():
        if t["fm"] is None:
            ctx.add("frontmatter", "warn", t["path"], 1, "topic has no frontmatter block")
            continue
        if t["err"]:
            ctx.add("frontmatter", "warn", t["path"], 1, "frontmatter could not be parsed cleanly: %s" % t["err"])
        missing = [k for k in TOPIC_KEYS if k not in t["fm"]]
        if missing:
            ctx.add("frontmatter", "warn", t["path"], 1, "frontmatter missing: %s" % ", ".join(missing))


def _check_target(ctx, src, target, off, lines, check_anchors, stats, linked=None):
    kind = classify_link(target)
    if kind == "skip":
        return
    if kind == "external":
        stats["external"] += 1
        return
    path_part, frag = split_target(target)
    if kind == "anchor":
        res = src
    else:
        res = resolve_local(src, ctx, path_part)
    line = lines.at(off)
    fresh = kind == "local" and (src, path_part) not in stats["seen"]
    if fresh:
        stats["seen"].add((src, path_part))
        stats["referenced"] += 1
    if not exists(res):
        ctx.add("links", "error", src, line, "broken link: %s" % target)
        return
    if fresh:
        stats["resolved"] += 1
    if linked is not None and res.is_file():
        linked.add(res)
    if frag and check_anchors and res.is_file() and res.suffix.lower() in (".html", ".htm") and frag.lower() != "top":
        if frag not in html_ids(ctx, res):
            ctx.add("links", "warn", src, line, "anchor #%s not found in %s" % (frag, ctx.disp(res)))


def check_links(ctx):
    stats = {"external": 0, "referenced": 0, "resolved": 0, "seen": set()}
    ctx.link_stats = stats
    ctx.html_linked = set()
    for p in ctx.pages:
        text = ctx.text(p)
        lines = Lines(text)
        for target, off in html_links(text):
            _check_target(ctx, p, target, off, lines, True, stats, ctx.html_linked)
    skip = {ctx.layout["ledger"], ctx.layout["inventory"]}
    files = ctx.md_files(skip_raw=True) if not ctx.page_mode else []
    for p in files:
        if p in skip:
            continue
        text = ctx.text(p)
        lines = Lines(text)
        for target, off in md_links(text):
            _check_target(ctx, p, target, off, lines, True, stats)
    for p in ctx.files:
        if p.suffix.lower() == ".css" and not ctx.is_legacy(p) and not ctx.page_mode:
            text = ctx.text(p)
            lines = Lines(text)
            for m in CSS_URL_RE.finditer(text):
                v = m.group(1) if m.group(1) is not None else m.group(2) if m.group(2) is not None else m.group(3)
                _check_target(ctx, p, v, m.start(), lines, False, stats)
    if stats["external"]:
        ctx.add("links", "info", ".", 0, "%d external links counted, not checked" % stats["external"])


URL_SPAN_RE = re.compile(r"https?://[^\s\"'<>)\]]+", re.I)
SHA256_RE = re.compile(r"(?<![0-9A-Fa-f])[0-9A-Fa-f]{64}(?![0-9A-Fa-f])")
LEAK_PATTERNS = (
    ("file: URL", re.compile(r"\bfile:(?://|\\\\|[A-Za-z]:)", re.I)),
    ("drive-root path", re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]")),
    ("/Users/ path", re.compile(r"(?<![\w.:])/Users/[\w.-]+")),
    ("UNC path", re.compile(r"(?<![\w:\\])\\\\[\w.-]+\\[\w$.-]+")),
)


def scan_leaks(text):
    """{kind: [line numbers]} for private-path patterns outside external URLs."""
    spans = [(m.start(), m.end()) for m in URL_SPAN_RE.finditer(text)]
    starts = [s for s, e in spans]
    lines = Lines(text)
    out = defaultdict(list)
    for kind, rx in LEAK_PATTERNS:
        for m in rx.finditer(text):
            i = bisect.bisect_right(starts, m.start()) - 1
            if i >= 0 and spans[i][0] <= m.start() < spans[i][1]:
                continue
            ln = lines.at(m.start())
            if ln not in out[kind]:
                out[kind].append(ln)
    return out


def check_leaks(ctx):
    linked = getattr(ctx, "html_linked", None)
    if linked is None:
        linked = set()
        for p in ctx.pages:
            text = ctx.text(p)
            for target, off in html_links(text):
                if classify_link(target) == "local":
                    r = resolve_local(p, ctx, split_target(target)[0])
                    if exists(r) and r.is_file():
                        linked.add(r)
    pages = set(ctx.pages)
    targets = [(p, "error", "reader page") for p in ctx.pages]
    seen = set(pages)
    for r in sorted(linked):
        if r in seen or r.suffix.lower() in MEDIA_EXT or r.suffix.lower() in (".html", ".htm"):
            continue
        if ctx.is_legacy(r):
            continue
        seen.add(r)
        targets.append((r, "error", "linked from a reader page"))
    if not ctx.page_mode:
        extra = [f for f in ctx.md_files(skip_raw=True) if f not in seen]
        if ctx.cfg_path and ctx.cfg_path not in seen:
            extra.append(ctx.cfg_path)
        targets += [(f, "info", "Markdown or config") for f in extra]
    for p, sev, why in targets:
        text = ctx.text(p)
        for kind, lns in sorted(scan_leaks(text).items()):
            msg = "%s: %d line(s), first at %d (%s)" % (kind, len(lns), lns[0], why)
            ctx.add("leaks", sev, p, lns[0], msg)
        if why == "reader page":
            lines = Lines(text)
            hashes = [lines.at(m.start()) for m in SHA256_RE.finditer(text)]
            if hashes:
                ctx.add("leaks", "warn", p, hashes[0], "%d SHA-256 value(s) in HTML, first at %d" % (len(hashes), hashes[0]))


def check_raw_tags(ctx):
    for p in ctx.pages:
        vis = html_visible(ctx.text(p))
        lines = Lines(vis)
        hits = [(lines.at(m.start()), m.group(0)) for m in RAW_TAG_RE.finditer(vis)]
        if hits:
            ex = ", ".join(sorted({h[1] for h in hits})[:4])
            ctx.add("raw_tags", "warn", p, hits[0][0], "%d raw provenance tag(s) left as visible text, e.g. %s" % (len(hits), ex))
        if len(vis.strip()) > 1500 and not LABEL_WORD_RE.search(vis):
            ctx.add("raw_tags", "warn", p, 1, "reader page shows no provenance label words")


SUPER_RE = re.compile(r"\b(best(?![- ](?:practices?|effort|guess|case|available|known|fit|estimates?))|strongest|largest|"
                      r"leading(?![- ](?:to|up|zeros?|spaces?|slash|whitespace|edge|indicators?))|most plausible|"
                      r"fastest|top-ranked|high confidence)\b", re.I)
METHOD_RE = re.compile(r"\b(method(?:ology)?|criteria|criterion|rubric|ranked (?:by|on)|ranking (?:is|by|based)|"
                       r"measured (?:by|as|in)|scored|based on|because|according to|"
                       r"by (?:revenue|volume|count|number|total|population|headcount|rating|size|sales|area|"
                       r"enrollment|employees|jobs|square))\b", re.I)
QUOTE_RE = re.compile(r"\u201c[^\u201d\n]*\u201d|\"[^\"\n]{3,}\"")
CODE_COMMENT_RE = re.compile(r"^\s*(//|/\*|\*|import\s|export\s+\*|export\s+\{)")
NAME_RE = re.compile(r"best (?:bath|bets?|buy|western)\b|best (?:external )?source class|best first move|best next action", re.I)
CITATION_RE = re.compile(r"\bAccessed\b[^.\n]{0,20}\d{4}", re.I)


def scan_superlatives(ctx, p, lines, is_data, allow):
    if p.stem == "source-ledger":
        return
    for n, line in enumerate(lines, 1):
        if not line.strip():
            continue
        if is_data and CODE_COMMENT_RE.match(line):
            continue
        if not is_data and line.lstrip().startswith(">"):
            continue
        if CITATION_RE.search(line):
            continue
        for m in SUPER_RE.finditer(line):
            if NAME_RE.match(line, m.start()) or re.match(r"Best(?:\s+[A-Z][\w/-]*){2,}", line[m.start():]):
                continue
            ts = line.rfind(" ", 0, m.start()) + 1
            te = line.find(" ", m.end())
            if "/" in line[ts:(len(line) if te < 0 else te)]:
                continue
            sent = sentence_at(line, m.start())
            if METHOD_RE.search(sent):
                continue
            if any(a and a.lower() in line.lower() for a in allow):
                continue
            if not is_data:
                qs = [(q.start(), q.end()) for q in QUOTE_RE.finditer(line)]
                if any(s <= m.start() < e for s, e in qs):
                    continue
            ctx.add("superlatives", "warn", p, n, "unsupported superlative %r: state the method or reword" % m.group(0))
            break


def check_superlatives(ctx):
    found, allow = ctx.cget("superlative_allow")
    allow = [a for a in (allow if isinstance(allow, list) else []) if isinstance(a, str)]
    md = [t["path"] for t in ctx.topics()]
    if not ctx.page_mode:
        out_dir = ctx.layout["output"]
        if out_dir.is_dir():
            md += [f for f in ctx.md_files() if ctx.under(f, "output") and not f.name.startswith("_")]
    for p in dict.fromkeys(md):
        text = ctx.text(p)
        _, off, _ = split_frontmatter(text)
        body = text[off:]
        body = re.sub(r"(?ms)^```.*?^```", _blank, body)
        scan_superlatives(ctx, p, [""] * text[:off].count("\n") + body.split("\n"), False, allow)
    for p in ctx.pages:
        scan_superlatives(ctx, p, html_visible(ctx.text(p)).split("\n"), False, allow)
    for p in ctx.site_files:
        scan_superlatives(ctx, p, ctx.text(p).split("\n"), True, allow)


def clean_code_line(line):
    for rx in CODE_NOISE:
        line = rx.sub(" ", line)
    return line


def number_tokens(text):
    return {norm_num(t) for t in NUM_RE.findall(text) if t.strip(",")}


RECORD_EXT = {".md", ".txt", ".csv", ".tsv", ".json"}
ID_ROW_RE = re.compile(r"[A-Z]{1,3}-?\d{1,3}")
ID_CITE_RE = re.compile(r"(?<![\w-])([A-Z]{1,3}-?\d{1,3})(?![\w-])")
SEP_ROW_RE = re.compile(r"\|[\s:|\-]+\|?")


def ledger_rows(ctx):
    """{id: {row, date, file, line}} for ledger and inventory table rows, with the Accessed date when given."""
    if "ledger_rows" in ctx.cache:
        return ctx.cache["ledger_rows"]
    rows = {}
    for key in ("ledger", "inventory"):
        f = ctx.layout[key]
        if not f.is_file():
            continue
        lines = ctx.text(f).split("\n")
        acc = None
        for i, line in enumerate(lines):
            s = line.strip()
            if not s.startswith("|") or SEP_ROW_RE.fullmatch(s):
                continue
            cells = [c.strip() for c in s.strip("|").split("|")]
            if i + 1 < len(lines) and SEP_ROW_RE.fullmatch(lines[i + 1].strip()):
                acc = next((n for n, c in enumerate(cells) if "accessed" in c.lower()), None)
                continue
            if not cells or not ID_ROW_RE.fullmatch(cells[0]) or cells[0] in rows:
                continue
            d = to_date(cells[acc]) if acc is not None and acc < len(cells) else None
            if d is None:
                m = re.search(r"accessed\D{0,15}(\d{4}-\d{2}-\d{2})", s, re.I)
                d = to_date(m.group(1)) if m else None
            rows[cells[0]] = {"row": s.lower(), "date": d, "file": f, "line": i + 1}
    ctx.cache["ledger_rows"] = rows
    return rows


def cited_ids(text, rows):
    return {i for i in ID_CITE_RE.findall(text) if i in rows}


def record_paths(ctx):
    """Evidence files for tracing topic numbers when there is no raw/: ledger, inventory, source roots, --canonical."""
    paths = [ctx.layout[k] for k in ("ledger", "inventory") if ctx.layout[k].is_file()]
    ev = ctx.root / "evidence"
    paths += [f for f in ctx.files if f.suffix.lower() in RECORD_EXT and ev in f.parents and f not in paths]
    roots = [Path(c) for c in (ctx.args.canonical or [])] + [ctx.resolve_cfg_path(e) for e in ctx.source_root_entries()]
    trunc = False
    for r in roots:
        if not exists(r):
            continue
        fs, t = walk_files(ctx, r, ctx.args.max_files)
        trunc = trunc or t
        paths += [f for f in fs if f.suffix.lower() in RECORD_EXT and not ctx.under(f, "topics")]
    return paths, trunc


def build_corpus(ctx, mode="site"):
    """(numbers, source ids, files read, truncated). Modes: site (all Markdown), raw (raw/ + ledger), record (no raw/)."""
    nums, sids, n, trunc = set(), set(), 0, False
    paths = []
    if mode == "raw":
        for f in ctx.files:
            if ctx.under(f, "raw") and f.suffix.lower() in TEXT_RAW_EXT:
                paths.append(f)
        lp = ctx.layout["ledger"]
        if lp.is_file():
            paths.append(lp)
    elif mode == "record":
        paths, trunc = record_paths(ctx)
    else:
        for f in ctx.files:
            if f.suffix.lower() == ".md" or (ctx.under(f, "raw") and f.suffix.lower() in TEXT_RAW_EXT):
                paths.append(f)
        extra_roots = [Path(c) for c in (ctx.args.canonical or [])]
        extra_roots += [ctx.resolve_cfg_path(e) for e in ctx.source_root_entries()]
        budget = ctx.args.max_files
        for r in extra_roots:
            if not exists(r):
                continue
            fs, t = walk_files(ctx, r, budget)
            trunc = trunc or t
            paths += [f for f in fs if f.suffix.lower() == ".md"]
    seen = set()
    for f in paths:
        if f in seen:
            continue
        seen.add(f)
        if n >= ctx.args.max_files:
            trunc = True
            break
        t = read_file(f)
        n += 1
        nums |= number_tokens(t)
        sids |= set(SID_RE.findall(t))
    return nums, sids, n, trunc


def _claims_in_lines(lines, is_code):
    found = {}
    for i, line in enumerate(lines, 1):
        if not line.strip():
            continue
        if is_code:
            if CODE_COMMENT_RE.match(line):
                continue
            line = clean_code_line(line)
        for key, (disp, pos, alt) in extract_claims(line).items():
            found.setdefault(key, (disp, i, alt))
    return found


def check_claim_trace(ctx):
    sources = [(p, html_visible(ctx.text(p)).split("\n"), False) for p in ctx.pages]
    sources += [(p, ctx.text(p).split("\n"), True) for p in ctx.site_files]
    sources = [s for s in sources if s[1]]
    if sources:
        nums, sids, nfiles, trunc = build_corpus(ctx)
        if nfiles == 0:
            ctx.add("claim_trace", "info", ".", 0, "no Markdown corpus found (use --canonical DIR); page claims not traced")
        else:
            if trunc:
                ctx.add("claim_trace", "info", ".", 0, "corpus scan truncated at --max-files %d (%d files read)" % (ctx.args.max_files, nfiles))
            ledger = ctx.layout["ledger"]
            ledger_ids = set(SID_RE.findall(read_file(ledger))) if ledger.is_file() else None
            missing_ids = defaultdict(list)
            for p, lines, is_code in sources:
                for (kind, norm), (disp, ln, alt) in sorted(_claims_in_lines(lines, is_code).items(), key=lambda kv: kv[1][1]):
                    if kind == "number":
                        if norm not in nums and (alt is None or alt not in nums):
                            ctx.add("claim_trace", "warn", p, ln, "%s not found in the Markdown corpus" % disp)
                    else:
                        known = ledger_ids if ledger_ids is not None else sids
                        if norm not in known:
                            missing_ids[p].append((ln, norm))
            where = "the source ledger" if ledger_ids is not None else "any Markdown record (no source ledger found)"
            # A rendered wiki article's S1, S2 are its own labels, not this Fieldbook's ledger IDs.
            articles = ctx.cget("reader")[1]
            articles = articles.get("wiki_articles") if isinstance(articles, dict) else None
            stems = {Path(str(a)).stem for a in articles} if isinstance(articles, list) else set()
            for p, items in missing_ids.items():
                if Path(p).stem in stems:
                    continue
                ids = sorted({i for _, i in items}, key=lambda s: int(s[1:]))
                ctx.add("claim_trace", "warn", p, min(l for l, _ in items),
                        "%d source ID(s) absent from %s: %s" % (len(ids), where, ", ".join(ids[:12]) + (" ..." if len(ids) > 12 else "")))
    if ctx.page_mode or not ctx.topics():
        return
    if ctx.layout["raw"].is_dir():
        rnums, _, rfiles, _ = build_corpus(ctx, "raw")
        where = "raw/ or the ledger"
        if rfiles == 0:
            return
    else:
        rnums, _, rfiles, rtrunc = build_corpus(ctx, "record")
        where = "the ledger, inventory, evidence/, source_roots or --canonical"
        if rfiles == 0:
            ctx.add("claim_trace", "info", ".", 0, "topic numbers not traced: no raw/ folder, ledger, inventory, source_roots or --canonical files to trace against")
            return
        ctx.add("claim_trace", "info", ".", 0, "no raw/ folder: topic numbers traced against %d file(s) from the ledger, inventory, evidence/, source_roots and --canonical%s"
                % (rfiles, " (scan truncated at --max-files)" if rtrunc else ""))
    for t in ctx.topics():
        body = t["text"][t["off"]:]
        body = re.sub(r"(?ms)^```.*?^```", _blank, body)
        lines = [ln if not SELF_LABEL_RE.search(ln) else "" for ln in body.split("\n")]
        base = t["text"][:t["off"]].count("\n")
        for (kind, norm), (disp, ln, alt) in sorted(_claims_in_lines(lines, False).items(), key=lambda kv: kv[1][1]):
            if kind == "number" and norm not in rnums and (alt is None or alt not in rnums):
                ctx.add("claim_trace", "warn", t["path"], ln + base, "%s in topic not found in %s" % (disp, where))


MAX_NOTE_FILES = 60
NOTE_EXT = {".md", ".txt", ".csv"}


def capture_files(ctx):
    """(captures, notes) where captures come from raw/ and notes from small declared source_roots."""
    raw = [f for f in ctx.files if ctx.under(f, "raw") and f.suffix.lower() in TEXT_RAW_EXT
           and not f.name.startswith("_") and f.name.lower() != "readme.md"]
    notes, skipped = [], []
    seen = set(raw)
    for e in ctx.source_root_entries():
        r = ctx.resolve_cfg_path(e)
        if not r.is_dir():
            continue
        fs, trunc = walk_files(ctx, r, MAX_NOTE_FILES * 20)
        cand = [f for f in fs if f.suffix.lower() in NOTE_EXT and not f.name.startswith("_")
                and f.name.lower() != "readme.md" and f not in seen and not ctx.under(f, "topics")]
        if trunc or len(cand) > MAX_NOTE_FILES:
            skipped.append((e, len(cand)))
            continue
        notes += [(f, e, ctx.root in r.parents or r == ctx.root) for f in cand]
        seen.update(cand)
    return raw, notes, skipped


def topic_blob(ctx):
    """Lowercase topic text plus the ledger and inventory rows of every ID a topic cites."""
    rows = ledger_rows(ctx)
    parts = []
    for t in ctx.topics():
        parts.append(t["text"])
        parts += [rows[i]["row"] for i in sorted(cited_ids(t["text"], rows))]
    return "\n".join(parts).lower()


def check_uncompiled(ctx):
    if ctx.page_mode:
        return
    raw, notes, skipped = capture_files(ctx)
    for e, n in skipped:
        ctx.add("uncompiled", "info", ".", 0, "source root %s holds %d+ files, too many to treat as captures; declare layout.raw or a raw/ folder to check them" % (e, n))
    if not raw and not notes:
        if not skipped:
            ctx.add("uncompiled", "info", ".", 0, "uncompiled check did not run: no raw/ folder and no small declared source_roots to check")
        return
    if not ctx.topics():
        ctx.add("uncompiled", "info", ".", 0, "uncompiled check did not run: no topic pages found")
        return
    blob = topic_blob(ctx)
    for f in raw:
        if f.stem.lower() not in blob:
            ctx.add("uncompiled", "warn", f, 0, "raw file is not named by any topic (filename, sources, link or cited ledger ID)")
    by_root = defaultdict(list)
    for f, e, inside in notes:
        by_root[(e, inside)].append(f)
    for (e, inside), fs in by_root.items():
        missing = [f for f in fs if f.stem.lower() not in blob]
        if not inside and len(missing) == len(fs):
            ctx.add("uncompiled", "info", ".", 0, "source root %s is outside the Fieldbook and no topic names any of its %d file(s); cannot tell captures from reference material" % (e, len(fs)))
            continue
        for f in missing:
            ctx.add("uncompiled", "warn", f, 0, "source-root note is not named by any topic (filename, sources, link or cited ledger ID)")


def file_date(f):
    """Date prefix of a capture name (YYYY-MM-DD-...), else its modified date."""
    m = re.match(r"(\d{4}-\d{2}-\d{2})", f.name)
    d = to_date(m.group(1)) if m else None
    if d:
        return d
    try:
        return dt.date.fromtimestamp(f.stat().st_mtime)
    except OSError:
        return None


def check_staleness(ctx):
    if ctx.page_mode:
        return
    cands, seen, trunc = [], 0, False
    roots = [r for r in (ctx.resolve_cfg_path(e) for e in ctx.source_root_entries()) if exists(r)]
    best = None
    for r in roots:
        fs, t = walk_files(ctx, r, max(ctx.args.max_files - seen, 0) or 1)
        trunc = trunc or t
        for f in fs:
            if f.suffix.lower() in MEDIA_EXT:
                continue
            try:
                m = f.stat().st_mtime
            except OSError:
                continue
            if best is None or m > best[0]:
                best = (m, f)
        seen += len(fs)
        if seen >= ctx.args.max_files:
            trunc = True
            break
    if best is not None:
        cands.append((dt.date.fromtimestamp(best[0]), "source record %s" % ctx.disp(best[1]), best[1]))
    raw, notes, _ = capture_files(ctx)
    dated = {}
    for f in raw + [n[0] for n in notes]:
        d = file_date(f)
        if d:
            dated[f] = d
            cands.append((d, "capture %s" % ctx.disp(f), f))
    rows = ledger_rows(ctx)
    for i, r in rows.items():
        if r["date"]:
            cands.append((r["date"], "ledger Accessed date of %s" % i, r["file"]))
    note = " (scan truncated at --max-files %d, newer files may exist)" % ctx.args.max_files if trunc else ""
    if not cands:
        ctx.add("staleness", "info", ".", 0, "staleness not computed: no source_roots files, raw/ captures or ledger Accessed dates found%s" % note)
        return
    tops = [(to_date(t["fm"].get("updated")), t) for t in ctx.topics() if t["fm"] and t["fm"].get("updated") is not None]
    tops = [x for x in tops if x[0]]
    if not tops:
        ctx.add("staleness", "info", ".", 0, "no topic has an updated date; staleness not computed%s" % note)
        return
    newest_src = max(cands, key=lambda c: c[0])
    newest_topic = max(tops, key=lambda x: x[0])
    if newest_src[0] > newest_topic[0]:
        ctx.add("staleness", "warn", newest_src[2], 0,
                "newest %s is dated %s, newer than the newest topic updated %s (%s)%s"
                % (newest_src[1], newest_src[0].isoformat(), newest_topic[0].isoformat(), ctx.disp(newest_topic[1]["path"]), note))
    elif trunc:
        ctx.add("staleness", "info", ".", 0, "source scan truncated at --max-files %d; no newer source seen so far" % ctx.args.max_files)
    for d, t in tops:
        text = t["text"]
        low = text.lower()
        ids = cited_ids(text, rows)
        cited = [(rows[i]["date"], "ledger source %s" % i, rows[i]["file"]) for i in sorted(ids) if rows[i]["date"]]
        cited += [(dd, "capture %s" % ctx.disp(f), f) for f, dd in dated.items() if f.stem.lower() in low]
        newer = [c for c in cited if c[0] > d and not (t is newest_topic[1] and c[2] == newest_src[2] and c[0] == newest_src[0])]
        if newer:
            top = max(newer, key=lambda c: c[0])
            ctx.add("staleness", "warn", t["path"], 0,
                    "topic updated %s is older than %d source(s) it cites; newest is %s dated %s"
                    % (d.isoformat(), len(newer), top[1], top[0].isoformat()))


COUNT_A = re.compile(r"\b(outputs?|topics?|raw(?:\s+(?:sources?|documents?|files?|captures?))?|sources)\s*[:=]\s*\**(\d+)\b(\s+raw\b)?", re.I)
COUNT_B = re.compile(r"(?<![\d-])\b(\d+)\s+(raw(?:\s+(?:sources?|documents?|files?|captures?))?|topics?(?:\s+pages?)?|outputs?|generated\s+artifacts)\b", re.I)
PAST_RE = re.compile(r"\b(was|were|previously|had|from \d+ to)\b|->|\u2192", re.I)


def _kind(word):
    w = word.lower()
    if w.startswith("raw"):
        return "raw"
    if w.startswith("topic"):
        return "topics"
    return "outputs"


def check_counts(ctx):
    if ctx.page_mode:
        return
    actual = {}
    if ctx.layout["topics"].is_dir():
        actual["topics"] = len(ctx.topics())
    if ctx.layout["raw"].is_dir():
        actual["raw"] = sum(1 for f in ctx.files if ctx.under(f, "raw") and not f.name.startswith("_") and f.suffix.lower() in TEXT_RAW_EXT)
    if ctx.layout["output"].is_dir() and ctx.layout["output"].name in ("output", "outputs"):
        actual["outputs"] = sum(1 for f in ctx.files if ctx.under(f, "output") and f.suffix.lower() == ".md" and not f.name.startswith("_"))
    names = {"readme.md", "_index.md", "handoff.md", "walkthrough.md"}
    for f in ctx.files:
        if f.name.lower() not in names or ctx.is_legacy(f):
            continue
        parts = f.relative_to(ctx.root).parts
        if len(parts) > 2 or (len(parts) == 2 and parts[0] != ".wiki"):
            continue
        done = set()
        for n, line in enumerate(ctx.text(f).split("\n"), 1):
            if PAST_RE.search(line):
                continue
            stated = []
            for m in COUNT_A.finditer(line):
                label = m.group(1).lower()
                if label == "sources":
                    if not m.group(3):
                        continue
                    stated.append(("raw", int(m.group(2))))
                else:
                    stated.append((_kind(label), int(m.group(2))))
            for m in COUNT_B.finditer(line):
                stated.append((_kind(m.group(2)), int(m.group(1))))
            for kind, num in stated:
                if (n, kind, num) in done or kind not in actual:
                    continue
                done.add((n, kind, num))
                if actual[kind] != num:
                    ctx.add("counts", "warn", f, n, "says %d %s; the folder holds %d" % (num, kind, actual[kind]))


NOT_BUILT_RE = re.compile(r"\bnot\s+(?:yet\s+)?(?:been\s+)?(?:built|generated|created)\b|\bsite[\\/]?\s+(?:folder\s+)?is\s+empty\b", re.I)


def check_status(ctx):
    if ctx.page_mode:
        return
    tops = ctx.topics()
    vals = {str(t["fm"].get("status")) for t in tops if t["fm"] and t["fm"].get("status") is not None}
    if len(vals) > 1:
        ctx.add("status", "info", ctx.layout["topics"], 0, "topics use mixed status values: %s" % ", ".join(sorted(vals)))
    if (ctx.root / "site" / "index.html").is_file():
        cands = [ctx.layout["editorial"], ctx.find("README.md"), ctx.root / "site" / "editorial-note.html"]
        for p in cands:
            if not p.is_file():
                continue
            text = ctx.text(p)
            if p.suffix == ".html":
                text = html_visible(text)
            for n, line in enumerate(text.split("\n"), 1):
                if NOT_BUILT_RE.search(line) and re.search(r"reader|site|html|index", line, re.I):
                    ctx.add("status", "warn", p, n, "says the reader or site was not built, but site/index.html exists")
                    break
    rs = ctx.cget("release_status")[1]
    if rs in (None, "private"):
        hosting = [f for f in ctx.files if (f.name == "hosting.json" and f.parent.name == ".openai") or
                   re.fullmatch(r"wrangler\.(toml|jsonc?)", f.name)]
        for f in hosting[:3]:
            ctx.add("status", "warn", f, 0, "release_status is %s but hosting config exists" % (rs or "unset"))
    for t in tops:
        for m in re.finditer(r"`((?:site|evidence)/[^`\s*<>{}]+)`", t["text"]):
            rel = m.group(1).rstrip(".,;:")
            if not exists(ctx.root / rel):
                ln = t["text"][:m.start()].count("\n") + 1
                ctx.add("status", "warn", t["path"], ln, "phantom asset: %s does not exist" % rel)


BACKTICK_RE = re.compile(r"`([^`\n]+)`")


def path_candidate(ctx, tok, base_dir):
    t = tok.strip()
    if not t or len(t) > 260 or "://" in t or t.startswith("#") or re.search(r"[*<>{}|$=?;]", t) or t.count(" ") > 4:
        return None
    if "/" not in t and "\\" not in t:
        return None
    if re.fullmatch(r"[\d.]+(/[\d.]+)+", t) or re.search(r"\s[/\\]\s", t):
        return None
    t = re.sub(r"[:#]\d+(?:-\d+)?$", "", t).rstrip(".,;:")
    first = re.split(r"[\\/]", t.replace("\\", "/"))[0]
    absolute = re.match(r"^([A-Za-z]:|/|\\\\)", t) is not None
    looks = absolute or t.startswith(("../", "./", "..\\")) or t.endswith(("/", "\\")) or "\\" in t \
        or "." in re.split(r"[\\/]", t)[-1] or exists(ctx.root / first) or exists(base_dir / first)
    return t if looks else None


def md_link_targets(text):
    out = []
    for target, off in md_links(text):
        if classify_link(target) == "local":
            out.append((split_target(target)[0], off))
    return out


def check_ledger_paths(ctx):
    if ctx.page_mode:
        return
    files = [ctx.layout["ledger"], ctx.layout["inventory"]]
    if ctx.cfg_path:
        files.append(ctx.cfg_path)
    seen_files = set()
    for f in files:
        if f in seen_files or not f.is_file():
            continue
        seen_files.add(f)
        text = ctx.text(f)
        lines = Lines(text)
        toks = []
        for m in BACKTICK_RE.finditer(text):
            c = path_candidate(ctx, m.group(1), ctx.root)
            if c:
                toks.append((c, m.start()))
        toks += [(t, off) for t, off in md_link_targets(text) if t]
        done = set()
        for tok, off in toks:
            if tok in done:
                continue
            done.add(tok)
            p = Path(tok.replace("\\", "/"))
            cands = [p] if p.is_absolute() or re.match(r"^[A-Za-z]:", tok) else [ctx.root / p, f.parent / p]
            hit = next((c for c in cands if exists(c)), None)
            ln = lines.at(off)
            if hit is None and len(cands) == 2 and not p.is_absolute():
                roots = [ctx.resolve_cfg_path(e) for e in ctx.source_root_entries()]
                if any(exists(r / p) for r in roots if r.is_dir()):
                    continue
            if hit is None:
                ctx.add("ledger_paths", "warn", f, ln, "path does not resolve from the Fieldbook root: %s" % tok)
                continue
            try:
                os.path.normpath(hit).replace("\\", "/")
                Path(os.path.normpath(hit)).relative_to(ctx.root)
            except ValueError:
                hp = Path(os.path.normpath(hit))
                roots = [ctx.resolve_cfg_path(e) for e in ctx.source_root_entries()]
                if any(hp == r or r in hp.parents for r in roots):
                    ctx.add("ledger_paths", "info", f, ln, "path is outside the Fieldbook root but inside a declared source root: %s" % tok)
                else:
                    ctx.add("ledger_paths", "warn", f, ln, "path points outside the Fieldbook root: %s" % tok)


BASIS_RE = re.compile(r"https?://|\]\(|\b[A-Z]{1,2}-?\d{1,3}\b|\[\d{1,3}\]|unsourced|allowance|\bsource", re.I)


def check_money_basis(ctx):
    if ctx.page_mode:
        return
    for f in ctx.md_files(skip_raw=True):
        if f.name.startswith("_") or f.parent.name == "evidence":
            continue
        rows, bad = 0, []
        for n, line in enumerate(ctx.text(f).split("\n"), 1):
            s = line.strip()
            if not s.startswith("|") or re.fullmatch(r"\|[\s:|\-]+\|?", s) or not re.search(r"\$\s?\d", s):
                continue
            rows += 1
            if not (BASIS_RE.search(s) or LABEL_WORD_RE.search(s)):
                bad.append((n, s))
        if bad:
            ex = "; ".join(re.sub(r"\s+", " ", b[1])[:70] for b in bad[:3])
            ctx.add("money_basis", "warn", f, bad[0][0], "%d of %d table rows with a dollar figure have no source ID, URL or label, e.g. %s" % (len(bad), rows, ex))


def check_orphans(ctx):
    if ctx.page_mode:
        return
    home = ctx.root / "site" / "index.html"
    if not home.is_file():
        return
    reach, queue = {home}, [home]
    while queue:
        cur = queue.pop()
        for target, off in html_links(ctx.text(cur)):
            if classify_link(target) != "local":
                continue
            r = resolve_local(cur, ctx, split_target(target)[0])
            if r.is_dir():
                r = r / "index.html"
            if r.suffix.lower() in (".html", ".htm") and exists(r) and r not in reach:
                reach.add(r)
                queue.append(r)
    sd = ctx.root / "site"
    for f in ctx.files:
        if f.suffix.lower() in (".html", ".htm") and not ctx.is_legacy(f):
            try:
                f.relative_to(sd)
            except ValueError:
                continue
            if f not in reach:
                ctx.add("orphans", "warn", f, 0, "HTML page is not reachable from site/index.html")


CONV_RE = re.compile(r"\b(?:the\s+\w+\s+you\s+(?:pasted|sent|shared|provided|gave|uploaded)|you\s+(?:said|mentioned|asked|pasted|wanted|noted|told)|"
                     r"as\s+you\s+(?:asked|requested|said|mentioned|wanted)|the\s+pasted|(?<![-\w])pasted\s+(?:article|text|page|link)|"
                     r"let\s+me\s+know\s+if)\b", re.I)


INTERNAL_RE = re.compile(r"\b(?:orchestrators?|sub-?agents?|worker[ -]agents?)\b", re.I)
AUDIENCE_RE = re.compile(r"\b(?:delivery costs?|contribution margins?|margins?(?!\s+of\s+error)|cost[- ]to[- ]serve|fallback fees?)\b", re.I)
AUDIENCE_WORDS = re.compile(r"prospect|client|public", re.I)


def check_conversational(ctx):
    for p in ctx.pages:
        scan_conv(ctx, p, html_visible(ctx.text(p)).split("\n"), True)
    for t in ctx.topics():
        scan_conv(ctx, t["path"], t["text"].split("\n"))


def audience_on(ctx):
    if getattr(ctx.args, "audience", None):
        return True
    aud = ctx.cget("audience")[1]
    if isinstance(aud, str):
        aud = re.sub(r"\bnot\s+(?:a\s+|for\s+)?(?:the\s+)?(?:prospects?|clients?|public)\b", "", aud, flags=re.I)
    return (isinstance(aud, str) and bool(AUDIENCE_WORDS.search(aud))) or ctx.cget("release_status")[1] == "public"


def check_audience(ctx):
    if not audience_on(ctx):
        return
    for p in ctx.pages:
        vis = html_visible(ctx.text(p))
        lines = Lines(vis)
        hits = [(lines.at(m.start()), m.group(0)) for m in AUDIENCE_RE.finditer(vis)]
        if hits:
            ex = ", ".join(sorted({h[1].lower() for h in hits})[:4])
            ctx.add("audience", "warn", p, hits[0][0], "%d internal cost term(s) in a prospect-facing page, e.g. %s" % (len(hits), ex))


def scan_conv(ctx, p, lines, html=False):
    rxs = (CONV_RE, INTERNAL_RE) if html and ctx.cget("subject_kind")[1] != "project-state" else (CONV_RE,)
    hits = [(n, m.group(0)) for n, line in enumerate(lines, 1) for rx in rxs for m in rx.finditer(line)]
    hits.sort()
    if hits:
        ex = ", ".join(sorted({h[1].lower() for h in hits})[:4])
        ctx.add("conversational", "warn", p, hits[0][0], "%d chat leftover(s), e.g. %s" % (len(hits), ex))


PHONE_RE = re.compile(r"(?<![\d.-])(?:\+?1[\s.-])?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}(?![\d-])")
EIN_RE = re.compile(r"(?<![\d-])\d{2}-\d{7}(?![\d-])")
ADDR_RE = re.compile(r"\b\d{1,5}[ \t]+(?:[NSEW]\.?[ \t]+)?[A-Z][A-Za-z0-9.']+(?:[ \t]+[A-Z][A-Za-z0-9.']+){0,3}[ \t]+"
                     r"(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Way|Place|Pl|Parkway|Pkwy|Highway|Hwy)\b"
                     r"(?!\.?[ \t]+(?:Louis|Charles|Peters|Ann|Paul|Clair|John|Joseph)\b)")


def check_personal_data(ctx):
    ok = ctx.cget("personal_data_ok")[1] is True
    sev = "info" if ok else "warn"
    for p in ctx.pages:
        vis = html_visible(ctx.text(p))
        lines = Lines(vis)
        for kind, rx in (("phone number", PHONE_RE), ("EIN-like number", EIN_RE), ("street-address-like string", ADDR_RE)):
            hits = [(lines.at(m.start()), m.group(0)) for m in rx.finditer(vis)]
            if hits:
                # Never echo the value: this output gets saved as a receipt.
                ctx.add("personal_data", sev, p, hits[0][0], "%d %s(s) in page text, first at this line" % (len(hits), kind))


CHECK_FUNCS = {"structure": check_structure, "config": check_config, "frontmatter": check_frontmatter,
               "links": check_links, "leaks": check_leaks, "raw_tags": check_raw_tags,
               "superlatives": check_superlatives, "claim_trace": check_claim_trace,
               "uncompiled": check_uncompiled, "staleness": check_staleness, "counts": check_counts,
               "status": check_status, "ledger_paths": check_ledger_paths, "money_basis": check_money_basis,
               "orphans": check_orphans, "conversational": check_conversational,
               "personal_data": check_personal_data, "audience": check_audience}


# ---------------------------------------------------------------- run and report

def run(target, args):
    ctx = Ctx(target, args)
    for name in CHECKS:
        try:
            CHECK_FUNCS[name](ctx)
        except Exception as exc:
            ctx.add(name, "warn", ".", 0, "check crashed and was skipped: %s: %s" % (type(exc).__name__, exc))
    if ctx.release:
        for f in ctx.findings:
            if f["check"] in RELEASE_CHECKS:
                if f["severity"] == "warn" or (f["check"] == "leaks" and f["severity"] == "info"):
                    f["severity"] = "error"
    ctx.findings.sort(key=lambda f: (CHECKS.index(f["check"]), SEV_ORDER[f["severity"]], f["file"], f["line"]))
    return ctx


def totals(findings):
    t = {"error": 0, "warn": 0, "info": 0}
    for f in findings:
        t[f["severity"]] += 1
    return t


def render_text(ctx, limit):
    out = ["Fieldbook check: %s" % ctx.root.as_posix(),
           "config: %s | mode: %s | release checks: %s | files scanned: %d" % (
               ctx.disp(ctx.cfg_path) if ctx.cfg_path else "none", ctx.mode, "on" if ctx.release else "off", len(ctx.files))]
    ls = getattr(ctx, "link_stats", None)
    if ls:
        out.append("links: %d distinct local references, %d resolved, %d broken, %d external occurrences (not checked)" % (
            ls["referenced"], ls["resolved"], ls["referenced"] - ls["resolved"], ls["external"]))
    by = defaultdict(list)
    for f in ctx.findings:
        by[f["check"]].append(f)
    for name in CHECKS:
        items = by.get(name)
        if not items:
            continue
        t = totals(items)
        out.append("")
        out.append("== %s (%d error, %d warn, %d info) ==" % (name, t["error"], t["warn"], t["info"]))
        for f in items[:limit]:
            loc = f["file"] + (":%d" % f["line"] if f["line"] else "")
            out.append("  [%s] %s  %s" % (f["severity"], loc, f["message"]))
        if len(items) > limit:
            out.append("  ... %d more hidden (use --json for all, --limit to raise the cap)" % (len(items) - limit))
    t = totals(ctx.findings)
    out.append("")
    out.append("Totals: %d error(s), %d warning(s), %d info" % (t["error"], t["warn"], t["info"]))
    return "\n".join(out)


def render_json(ctx):
    return json.dumps({"root": ctx.root.as_posix(), "config": ctx.cfg_path.as_posix() if ctx.cfg_path else None,
                       "output_mode": ctx.mode, "release": ctx.release, "files_scanned": len(ctx.files),
                       "links": {k: v for k, v in (getattr(ctx, "link_stats", None) or {}).items() if k != "seen"} or None,
                       "totals": totals(ctx.findings), "findings": ctx.findings}, indent=2, ensure_ascii=False)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Read-only Fieldbook validator.")
    ap.add_argument("root", help="Fieldbook folder, or one built .html file")
    ap.add_argument("--json", action="store_true", help="print all findings as JSON")
    ap.add_argument("--release", action="store_true", help="promote claim-trace, uncompiled, staleness and leak findings to errors")
    ap.add_argument("--canonical", action="append", default=[], metavar="DIR", help="extra Markdown corpus directory (repeatable)")
    ap.add_argument("--site", action="append", default=[], metavar="DIR", help="site source directory with data files (repeatable)")
    ap.add_argument("--audience", metavar="KIND", help="force the audience check on (for example: prospect), mainly for a bare HTML run")
    ap.add_argument("--max-files", type=int, default=20000, help="file scan bound per walk (default 20000)")
    ap.add_argument("--limit", type=int, default=20, help="findings shown per check in text mode (default 20)")
    args = ap.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    t = Path(args.root)
    if not t.exists() or args.max_files < 1:
        print("error: root not found or bad --max-files: %s" % args.root, file=sys.stderr)
        return 2
    if t.is_file() and t.suffix.lower() not in (".html", ".htm"):
        print("error: a file root must be an .html page", file=sys.stderr)
        return 2
    ctx = run(t, args)
    print(render_json(ctx) if args.json else render_text(ctx, args.limit))
    return 1 if totals(ctx.findings)["error"] else 0


if __name__ == "__main__":
    sys.exit(main())
