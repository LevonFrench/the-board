"""Build a static, JavaScript-free HTML reader for a Fieldbook from its Markdown.

Usage:
    python build_reader.py <fieldbook-root> [--dry-run] [--force] [--single-file PATH]

Multi-page output: <root>/index.html (redirect), <root>/site/*.html and
<root>/site/styles.css. Single-file output (--single-file, or config
output_mode: single-file with single_file: PATH): one self-contained HTML
document at PATH under the root, with inline CSS and embedded images.

Every HTML page carries <meta name="generator" content="fieldbook-build_reader">.
An existing HTML file without that meta is never overwritten unless --force is
given, and nothing is written at all if any file is refused. Nothing is ever
deleted. Output has no clock input, so a re-run on the same input is
byte-identical.

Markdown is rendered by a built-in renderer for the subset Fieldbooks use
(no pandoc). Raw HTML in Markdown is shown as text. PyYAML is used for
frontmatter and config when importable, with a small fallback parser.

Exit codes: 0 clean; 1 build problems (path leaks, broken links); 2 refused to
overwrite; 3 bad arguments.
"""
import argparse
import base64
import datetime
import html
import posixpath
import re
import sys
import unicodedata
import urllib.parse
from html.parser import HTMLParser
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

GENERATOR = "fieldbook-build_reader"
GENERATOR_META = f'<meta name="generator" content="{GENERATOR}">'
CSS_MARK = f"/* {GENERATOR} */"
IMAGE_LIMIT = 2_000_000
PATH_REMOVED = "[local path removed]"
esc = html.escape

CHIPS = {
    "local-primary": ("local", "Read directly from a primary record held locally."),
    "local-derived": ("local", "Derived from local material; not itself a primary record."),
    "external-primary": ("primary", "Official or first-hand published source, opened and read."),
    "external-secondary": ("secondary", "Reputable secondary reporting or reference work."),
    "search-extract": ("weak", "Seen only in a search-result extract; the page was not opened."),
    "lead-only": ("weak", "A pointer to follow up; not yet usable as evidence."),
    "restricted": ("bad", "Source with access or sharing limits; not reproduced here."),
    "inference": ("warn", "Reasoned from the evidence; not stated by a source."),
    "arithmetic": ("warn", "Computed from other figures in this Fieldbook."),
    "contested": ("bad", "Sources disagree; no side is chosen."),
    "missing": ("open", "Expected evidence that was not found."),
    "unknown": ("open", "Not resolved in this pass."),
    "hypothesis": ("warn", "A working guess to test, not a finding."),
    "not-checked": ("open", "Not checked yet."),
}
CHIP_ALIASES = {}
CHIP_RE = re.compile(r"\[([A-Za-z][^\[\]\n]{0,100})\]")
CHIP_HEAD = re.compile(r"[A-Za-z]+(?:-[A-Za-z]+)*")


def chip_html(content):
    """A provenance chip for 'inference' or 'inference, from the notes'; '' if content is not one."""
    m = CHIP_HEAD.match(content)
    if not m:
        return ""
    head, rest = m.group(0).lower(), content[m.end():]
    if head in CHIPS:
        cls = CHIPS[head][0]
    elif head in CHIP_ALIASES and not rest:
        cls = CHIP_ALIASES[head]
    else:
        return ""
    if rest and rest[0] not in " ,;:/":
        return ""
    more = " chip-long" if rest else ""
    return f'<span class="chip chip-{cls}{more}">{esc(head + rest)}</span>'


ROLES = [
    ("source-ledger", "Sources", "Every source, with its type, date and limits.",
     ["source-ledger.md", "evidence/source-ledger.md", "reports/source-ledger.md"]),
    ("coverage-matrix", "Coverage", "Which questions each topic answers and where coverage is thin.",
     ["coverage-matrix.md", "evidence/coverage-matrix.md", "reports/coverage-matrix.md"]),
    ("gap-register", "Open questions", "Open questions and the check that closes each.",
     ["gap-register.md", "evidence/gap-register.md", "gap-backlog.md", "evidence/gap-backlog.md"]),
    ("refresh-backlog", "Refresh backlog", "Facts that go stale and when to re-check them.",
     ["refresh-backlog.md", "evidence/refresh-backlog.md", "reports/refresh-backlog.md"]),
    ("editorial-note", "Editorial note", "How this Fieldbook was built and where it is weak.",
     ["editorial-note.md", "reports/editorial-note.md", "reports/editorial-provenance-and-caveats.md"]),
    ("local-evidence-inventory", "Evidence inventory", "Local evidence on hand and how each item was used.",
     ["local-evidence-inventory.md", "evidence/local-evidence-inventory.md"]),
    ("guidance", "Guidance log", "Owner steering for the next research pass.",
     ["guidance.md", "evidence/guidance.md"]),
]
EXTRA_DIRS = ("evidence", "reports")
NOT_READER_EXT = {".yml", ".yaml", ".py", ".json", ".toml", ".ini", ".cfg", ".sh", ".ps1", ".bat",
                  ".env", ".lock", ".js", ".ts", ".cmd"}
IMAGE_MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif",
              ".webp": "image/webp", ".svg": "image/svg+xml"}
PUNCT = set("!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~")

DRIVE = r"(?<![\w/.:%~@+-])[A-Za-z]:[\\/]"
UNC = r"(?<![A-Za-z0-9\\])\\\\[A-Za-z0-9_.$-]+\\"
FILEURL = r"(?<![A-Za-z0-9_-])file:/"
HOMEDIR = r"(?<![\w/.:-])/(?:Users|home)/[A-Za-z0-9_.-]+"
PATH_START = f"(?:{DRIVE}|{UNC}|{FILEURL}|{HOMEDIR})"
PATH_FULL = re.compile(PATH_START + r"[^\s<>\"'`]*")
PATH_TO_EOL = re.compile(PATH_START + r"[^\n]*")


# --- YAML ---------------------------------------------------------------

def _split_flow(inner, sep=","):
    """Split the body of an inline list or map on separators that sit outside quotes and brackets."""
    items, cur, quote, depth = [], "", "", 0
    for ch in inner:
        if quote:
            quote = "" if ch == quote else quote
            cur += ch
        elif ch in "\"'":
            quote = ch
            cur += ch
        elif ch == sep and depth == 0:
            items.append(cur)
            cur = ""
        else:
            depth += (ch in "[{") - (ch in "]}")
            cur += ch
    if cur.strip():
        items.append(cur)
    return items


def _scalar(s):
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        return s[1:-1].replace('\\"', '"') if s[0] == '"' else s[1:-1].replace("''", "'")
    if s.startswith("[") and s.endswith("]"):
        return [_scalar(x) for x in _split_flow(s[1:-1])]
    if s.startswith("{") and s.endswith("}"):
        # An inline map, such as labels: {game: "G1"}. Without this the whole map was read as one string.
        out = {}
        for item in _split_flow(s[1:-1]):
            parts = _split_flow(item, ":")
            if len(parts) >= 2:
                out[_scalar(parts[0]) if parts[0].strip()[:1] in "\"'" else parts[0].strip()] = _scalar(":".join(parts[1:]))
        return out
    low = s.lower()
    if low in ("true", "yes"):
        return True
    if low in ("false", "no"):
        return False
    if low in ("null", "~", ""):
        return None
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    return s


def mini_yaml(text):
    """Tiny YAML subset: nested maps, block and inline lists, scalars."""
    lines = [ln.rstrip() for ln in text.split("\n") if ln.strip() and not ln.lstrip().startswith("#")]

    def indent(ln):
        return len(ln) - len(ln.lstrip(" "))

    def block(i, ind):
        if i < len(lines) and lines[i].lstrip().startswith("-") and indent(lines[i]) == ind:
            out = []
            while i < len(lines) and indent(lines[i]) == ind and lines[i].lstrip().startswith("-"):
                out.append(_scalar(lines[i].lstrip()[1:]))
                i += 1
            return out, i
        out = {}
        while i < len(lines) and indent(lines[i]) == ind:
            m = re.match(r"\s*([^:#][^:]*?)\s*:(?:\s+(.*)|$)", lines[i])
            if not m:
                i += 1
                continue
            key, rest = m.group(1).strip("\"'"), (m.group(2) or "").strip()
            i += 1
            if rest in ("|", ">", "|-", ">-"):
                parts = []
                while i < len(lines) and indent(lines[i]) > ind:
                    parts.append(lines[i].strip())
                    i += 1
                out[key] = " ".join(parts)
            elif rest == "":
                if i < len(lines) and (indent(lines[i]) > ind or
                                       (indent(lines[i]) == ind and lines[i].lstrip().startswith("-"))):
                    out[key], i = block(i, indent(lines[i]))
                else:
                    out[key] = None
            else:
                out[key] = _scalar(rest)
        return out, i

    if not lines:
        return {}
    value, _ = block(0, indent(lines[0]))
    return value


def parse_yaml(text):
    if yaml is not None:
        try:
            value = yaml.safe_load(text)
            return value if value is not None else {}
        except Exception:
            pass
    try:
        return mini_yaml(text)
    except Exception:
        return {}


def split_frontmatter(text):
    lines = text.split("\n")
    if lines and lines[0].rstrip() == "---" and len(lines) > 1 and (
            not lines[1].strip() or re.match(r"[\w-]+\s*:|#", lines[1])):
        for i in range(1, len(lines)):
            if lines[i].rstrip() in ("---", "..."):
                meta = parse_yaml("\n".join(lines[1:i]))
                return (meta if isinstance(meta, dict) else {}), "\n".join(lines[i + 1:]).lstrip("\n")
    return {}, text


def read_text(path):
    text = Path(path).read_text(encoding="utf-8-sig", errors="replace")
    return text.replace("\r\n", "\n").replace("\r", "\n")


def norm_value(v):
    if isinstance(v, (datetime.date, datetime.datetime)):
        return v.isoformat()[:10]
    return "" if v is None else str(v)


# --- Markdown -----------------------------------------------------------

def slugify(text):
    out = []
    for ch in text.strip().lower():
        cat = unicodedata.category(ch)
        if ch == " ":
            out.append("-")
        elif ch == "-" or cat[0] in "LMN" or cat == "Pc":
            out.append(ch)
    return "".join(out)


def plain(fragment):
    return html.unescape(re.sub(r"<[^>]+>", "", fragment))


def default_resolver(href, is_image=False):
    """Allow http(s), mailto, tel and scheme-less targets; everything else becomes text."""
    compact = re.sub(r"[\x00-\x20\x7f]", "", href)
    m = re.match(r"([A-Za-z][A-Za-z0-9+.-]*):", compact)
    if m:
        scheme = m.group(1).lower()
        if is_image:
            return None
        if scheme in ("http", "https"):
            return href.strip(), True
        if scheme in ("mailto", "tel"):
            return href.strip(), False
        return None
    return href.strip(), False


FENCE = re.compile(r"^( {0,3})(`{3,}|~{3,})\s*([^`]*)$")
HEADING = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?(?:[ \t]+#+)?[ \t]*$")
HR = re.compile(r"^ {0,3}([-*_])(?:[ \t]*\1){2,}[ \t]*$")
SETEXT = re.compile(r"^ {0,3}(=+|-+)[ \t]*$")
BQ = re.compile(r"^ {0,3}>")
LIST = re.compile(r"^( {0,3})([-+*]|\d{1,9}[.)])( *)(.*)$")
DELIM_ROW = re.compile(r"^ {0,3}\|?[ \t]*:?-+:?[ \t]*(?:\|[ \t]*:?-+:?[ \t]*)*\|?[ \t]*$")
ENTITY = re.compile(r"&(?:#\d{1,7}|#[xX][0-9A-Fa-f]{1,6}|[A-Za-z][A-Za-z0-9]{1,31});")
AUTOLINK = re.compile(r"<([A-Za-z][A-Za-z0-9+.-]{1,31}:[^\s<>]*)>")
BARE_URL = re.compile(r"(?:https?://|www\.)[^\s<]+")


def split_row(line):
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", s)]


def list_item(line):
    m = LIST.match(line)
    if m and (m.group(3) or not m.group(4)) and not HR.match(line):
        return m
    return None


class Markdown:
    """Render the Fieldbook Markdown subset to HTML.

    resolver(href, is_image) returns None (render as text), (href, external)
    or (None, False, note) for an image replaced by a text note.
    """

    def __init__(self, resolver=None, shift=0, id_prefix=""):
        self.resolver = resolver or default_resolver
        self.shift = shift
        self.id_prefix = id_prefix
        self.headings = []
        self.used_ids = {}

    def render(self, text):
        lines = text.replace("\r\n", "\n").replace("\r", "\n").expandtabs(4).split("\n")
        return self.blocks(lines)

    # blocks
    def heading_id(self, text):
        base = slugify(text) or "section"
        n = self.used_ids.get(base)
        if n is None:
            self.used_ids[base] = 0
            return self.id_prefix + base
        while True:
            n += 1
            cand = f"{base}-{n}"
            if cand not in self.used_ids:
                self.used_ids[base] = n
                self.used_ids[cand] = 0
                return self.id_prefix + cand

    def starts_block(self, lines, i):
        line = lines[i]
        if FENCE.match(line) or HEADING.match(line) or HR.match(line) or BQ.match(line):
            return True
        m = list_item(line)
        if m and m.group(4).strip() and (not m.group(2)[0].isdigit() or int(m.group(2)[:-1]) == 1):
            return True
        return self.table_at(lines, i)

    def table_at(self, lines, i):
        if "|" not in lines[i] or i + 1 >= len(lines):
            return False
        nxt = lines[i + 1]
        return bool("|" in nxt and DELIM_ROW.match(nxt) and len(split_row(lines[i])) == len(split_row(nxt)))

    def blocks(self, lines, tight=False):
        out, i, n = [], 0, len(lines)
        while i < n:
            line = lines[i]
            if not line.strip():
                i += 1
                continue
            m = FENCE.match(line)
            if m:
                i = self.fenced(lines, i, m, out)
                continue
            m = HEADING.match(line)
            if m:
                self.add_heading(out, len(m.group(1)), (m.group(2) or "").strip())
                i += 1
                continue
            if HR.match(line):
                out.append("<hr>")
                i += 1
                continue
            if line.lstrip().startswith("<!--"):
                while i < n and "-->" not in lines[i]:
                    i += 1
                i += 1
                continue
            if BQ.match(line):
                i = self.quote(lines, i, out)
                continue
            if list_item(line):
                i = self.list_block(lines, i, out)
                continue
            if self.table_at(lines, i):
                i = self.table(lines, i, out)
                continue
            para = [line.lstrip()]
            i += 1
            setext = 0
            while i < n and lines[i].strip():
                sm = SETEXT.match(lines[i])
                if sm:
                    setext = 1 if sm.group(1)[0] == "=" else 2
                    i += 1
                    break
                if self.starts_block(lines, i):
                    break
                para.append(lines[i].lstrip())
                i += 1
            text = "\n".join(para).rstrip()
            if setext:
                self.add_heading(out, setext, " ".join(p.strip() for p in para))
            elif tight:
                out.append(self.inline(text))
            else:
                out.append(f"<p>{self.inline(text)}</p>")
        return "\n".join(out)

    def add_heading(self, out, level, text):
        inner = self.inline(text)
        hid = self.heading_id(plain(inner))
        self.headings.append((level, plain(inner), hid))
        shown = min(6, level + self.shift)
        out.append(f'<h{shown} id="{esc(hid)}">{inner}</h{shown}>')

    def fenced(self, lines, i, m, out):
        indent, fence, info = len(m.group(1)), m.group(2), m.group(3).strip()
        i += 1
        body = []
        while i < len(lines):
            ln = lines[i]
            cm = re.match(r"^ {0,3}(" + re.escape(fence[0]) + "{" + str(len(fence)) + r",})[ \t]*$", ln)
            if cm:
                i += 1
                break
            body.append(re.sub(r"^ {0,%d}" % indent, "", ln))
            i += 1
        lang = info.split()[0] if info else ""
        cls = f' class="language-{esc(lang)}"' if lang else ""
        out.append(f"<pre><code{cls}>{esc(chr(10).join(body))}\n</code></pre>")
        return i

    def quote(self, lines, i, out):
        inner = []
        while i < len(lines):
            ln = lines[i]
            if BQ.match(ln):
                inner.append(re.sub(r"^ {0,3}> ?", "", ln))
            elif ln.strip() and inner and inner[-1].strip() and not self.starts_block(lines, i):
                inner.append(ln)
            else:
                break
            i += 1
        out.append(f"<blockquote>\n{self.blocks(inner)}\n</blockquote>")
        return i

    def list_block(self, lines, i, out):
        first = list_item(lines[i])
        ordered = first.group(2)[0].isdigit()
        kind = (ordered, first.group(2)[-1] if ordered else first.group(2))
        start = int(first.group(2)[:-1]) if ordered else 1
        items, loose = [], False
        n = len(lines)
        while i < n:
            m = list_item(lines[i])
            if not m:
                break
            ordered_m = m.group(2)[0].isdigit()
            if (ordered_m, m.group(2)[-1] if ordered_m else m.group(2)) != kind:
                break
            indent = len(m.group(1))
            spaces = len(m.group(3))
            rest = m.group(4)
            if not rest.strip():
                content_indent = indent + len(m.group(2)) + 1
            else:
                content_indent = indent + len(m.group(2)) + (spaces if spaces <= 4 else 1)
            item = [rest]
            i += 1
            while i < n:
                ln = lines[i]
                if not ln.strip():
                    item.append("")
                    i += 1
                    continue
                ind = len(ln) - len(ln.lstrip(" "))
                if ind >= content_indent:
                    item.append(ln[content_indent:])
                elif ind > indent and list_item(ln):
                    item.append(ln.lstrip(" "))
                elif item[-1].strip() and not self.starts_block(lines, i) and not list_item(ln):
                    item.append(ln.lstrip(" "))
                else:
                    break
                i += 1
            blanks = 0
            while item and not item[-1].strip():
                item.pop()
                blanks += 1
            if blanks and i < n:
                nm = list_item(lines[i])
                nord = bool(nm) and nm.group(2)[0].isdigit()
                if nm and (nord, nm.group(2)[-1] if nord else nm.group(2)) == kind:
                    loose = True
            items.append(item)
        parts = []
        for item in items:
            task = ""
            li_class = ""
            tm = re.match(r"^\[([ xX])\][ \t]+", item[0]) if item else None
            if tm:
                checked = " checked" if tm.group(1) in "xX" else ""
                task = f'<input type="checkbox" disabled{checked}> '
                item = [item[0][tm.end():]] + item[1:]
                li_class = ' class="task"'
            inner = self.blocks(item, tight=not loose)
            if task:
                inner = "<p>" + task + inner[3:] if inner.startswith("<p>") else task + inner
            parts.append(f"<li{li_class}>{inner}</li>")
        tag = "ol" if ordered else "ul"
        attr = f' start="{start}"' if ordered and start != 1 else ""
        out.append(f"<{tag}{attr}>\n" + "\n".join(parts) + f"\n</{tag}>")
        return i

    def table(self, lines, i, out):
        head = split_row(lines[i])
        aligns = []
        for cell in split_row(lines[i + 1]):
            left, right = cell.startswith(":"), cell.endswith(":")
            aligns.append("c" if left and right else "r" if right else "")
        i += 2
        rows = []
        while i < len(lines) and lines[i].strip() and "|" in lines[i] and not self.starts_block_non_table(lines, i):
            rows.append(split_row(lines[i]))
            i += 1
        cols = len(head)

        def cell(tag, text, k):
            cls = f' class="al-{aligns[k]}"' if aligns[k] else ""
            scope = ' scope="col"' if tag == "th" else ""
            return f"<{tag}{scope}{cls}>{self.inline(text)}</{tag}>"

        html_rows = ["<thead><tr>" + "".join(cell("th", head[k], k) for k in range(cols)) + "</tr></thead>"]
        body = []
        for r in rows:
            r = (r + [""] * cols)[:cols]
            body.append("<tr>" + "".join(cell("td", r[k], k) for k in range(cols)) + "</tr>")
        out.append('<div class="scroll" role="region" aria-label="Scrollable table" tabindex="0"><table>'
                   + html_rows[0] + "<tbody>" + "".join(body) + "</tbody></table></div>")
        return i

    def starts_block_non_table(self, lines, i):
        line = lines[i]
        return bool(FENCE.match(line) or HEADING.match(line) or BQ.match(line))

    # inline
    def text_node(self, s):
        return esc(ENTITY.sub(lambda m: html.unescape(m.group(0)), s) if "&" in s else s)

    def inline(self, s, in_link=False):
        toks, buf = [], []
        i, n = 0, len(s)

        def flush():
            if buf:
                toks.append(self.text_node("".join(buf)))
                buf.clear()

        while i < n:
            c = s[i]
            if c == "\\":
                if i + 1 < n and s[i + 1] == "\n":
                    flush()
                    toks.append("<br>\n")
                    i += 2
                    while i < n and s[i] == " ":
                        i += 1
                elif i + 1 < n and s[i + 1] in PUNCT:
                    buf.append(s[i + 1])
                    i += 2
                else:
                    buf.append(c)
                    i += 1
            elif c == "`":
                run = re.match(r"`+", s[i:]).group(0)
                close = re.compile(r"(?<!`)" + "`" * len(run) + r"(?!`)").search(s, i + len(run))
                if close:
                    flush()
                    code = s[i + len(run):close.start()].replace("\n", " ")
                    if len(code) > 2 and code[0] == " " and code[-1] == " " and code.strip():
                        code = code[1:-1]
                    chip = CHIP_RE.fullmatch(code)
                    toks.append((chip and chip_html(chip.group(1))) or f"<code>{esc(code)}</code>")
                    i = close.end()
                else:
                    buf.append(run)
                    i += len(run)
            elif c == "\n":
                text = "".join(buf)
                hard = text.endswith("  ")
                buf[:] = [text.rstrip(" ")]
                if hard:
                    flush()
                    toks.append("<br>\n")
                else:
                    buf.append("\n")
                i += 1
                while i < n and s[i] == " ":
                    i += 1
            elif c == "&":
                m = ENTITY.match(s, i)
                if m:
                    buf.append(html.unescape(m.group(0)))
                    i = m.end()
                else:
                    buf.append(c)
                    i += 1
            elif c == "<":
                m = AUTOLINK.match(s, i)
                if m:
                    flush()
                    toks.append(self.make_link(m.group(1), esc(m.group(1)), in_link))
                    i = m.end()
                else:
                    buf.append(c)
                    i += 1
            elif c == "!" and s[i + 1:i + 2] == "[":
                r = self.bracket(s, i + 1)
                if r:
                    label, dest, title, end = r
                    flush()
                    toks.append(self.make_image(label, dest, title))
                    i = end
                else:
                    buf.append(c)
                    i += 1
            elif c == "[":
                cm = CHIP_RE.match(s, i)
                chip = chip_html(cm.group(1)) if cm and s[cm.end():cm.end() + 1] not in ("(", "[") else ""
                if chip:
                    flush()
                    toks.append(chip)
                    i = cm.end()
                    continue
                r = None if in_link else self.bracket(s, i)
                if r:
                    label, dest, title, end = r
                    flush()
                    toks.append(self.make_link(dest, self.inline(label, True), in_link, title))
                    i = end
                else:
                    buf.append(c)
                    i += 1
            elif c in "*_~":
                j = i
                while j < n and s[j] == c:
                    j += 1
                prev = s[i - 1] if i > 0 else " "
                nxt = s[j] if j < n else " "
                if c == "~" and j - i != 2:
                    buf.append(s[i:j])
                else:
                    flush()
                    can_open, can_close = self.flanking(prev, nxt, c)
                    toks.append([c, j - i, j - i, can_open, can_close])
                i = j
            elif c in "hw" and not in_link and (i == 0 or not s[i - 1].isalnum()):
                m = BARE_URL.match(s, i)
                if m and (c == "h" or m.group(0).startswith("www.")):
                    url = m.group(0)
                    while url and (url[-1] in ".,:;!?\"'*_~" or (url[-1] == ")" and url.count(")") > url.count("("))):
                        url = url[:-1]
                    if len(url) > 8:
                        flush()
                        href = url if url.startswith("http") else "http://" + url
                        toks.append(self.make_link(href, esc(url), in_link))
                        i += len(url)
                        continue
                buf.append(c)
                i += 1
            else:
                buf.append(c)
                i += 1
        flush()
        return self.emphasis(toks)

    @staticmethod
    def flanking(prev, nxt, ch):
        def punct(c):
            return unicodedata.category(c)[0] in "PS"

        ws_p, ws_n = prev.isspace(), nxt.isspace()
        left = not ws_n and (not punct(nxt) or ws_p or punct(prev))
        right = not ws_p and (not punct(prev) or ws_n or punct(nxt))
        if ch == "_":
            return left and (not right or punct(prev)), right and (not left or punct(nxt))
        return left, right

    @staticmethod
    def emphasis(toks):
        def as_text(parts):
            return "".join(p if isinstance(p, str) else esc(p[0] * p[1]) for p in parts)

        j = 0
        while j < len(toks):
            t = toks[j]
            if isinstance(t, list) and t[4]:
                k = j - 1
                while k >= 0:
                    o = toks[k]
                    if isinstance(o, list) and o[0] == t[0] and o[3]:
                        if t[0] == "~" and not (o[1] >= 2 and t[1] >= 2):
                            k -= 1
                            continue
                        if (o[4] or t[3]) and (o[2] + t[2]) % 3 == 0 and not (o[2] % 3 == 0 and t[2] % 3 == 0):
                            k -= 1
                            continue
                        break
                    k -= 1
                if k >= 0:
                    o = toks[k]
                    use = 2 if (t[0] == "~" or (o[1] >= 2 and t[1] >= 2)) else 1
                    tag = "del" if t[0] == "~" else "strong" if use == 2 else "em"
                    new = f"<{tag}>{as_text(toks[k + 1:j])}</{tag}>"
                    o[1] -= use
                    t[1] -= use
                    tail = toks[j + 1:]
                    left = toks[:k] + ([o] if o[1] > 0 else [])
                    j = len(left) + 1
                    toks = left + [new] + ([t] if t[1] > 0 else []) + tail
                    continue
            j += 1
        return as_text(toks)

    def bracket(self, s, i):
        """Parse [label](dest "title") at s[i] == '['; returns (label, dest, title, end) or None."""
        depth, j, n = 0, i, len(s)
        while j < n:
            c = s[j]
            if c == "\\":
                j += 2
                continue
            if c == "`":
                run = re.match(r"`+", s[j:]).group(0)
                close = re.compile(r"(?<!`)" + "`" * len(run) + r"(?!`)").search(s, j + len(run))
                j = close.end() if close else j + len(run)
                continue
            if c == "[":
                depth += 1
            elif c == "]":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        else:
            return None
        if s[j + 1:j + 2] != "(":
            return None
        label = s[i + 1:j]
        k = j + 2
        while k < n and s[k] in " \t\n":
            k += 1
        if k < n and s[k] == "<":
            e = s.find(">", k)
            if e == -1 or "\n" in s[k:e]:
                return None
            dest, k = s[k + 1:e], e + 1
        else:
            start, parens = k, 0
            while k < n:
                c = s[k]
                if c == "\\":
                    k += 2
                    continue
                if c in " \t\n" or ord(c) < 32:
                    break
                if c == "(":
                    parens += 1
                elif c == ")":
                    if parens == 0:
                        break
                    parens -= 1
                k += 1
            dest = s[start:k]
        while k < n and s[k] in " \t\n":
            k += 1
        title = ""
        if k < n and s[k] in "\"'(":
            closer = ")" if s[k] == "(" else s[k]
            e = s.find(closer, k + 1)
            if e == -1:
                return None
            title, k = s[k + 1:e], e + 1
            while k < n and s[k] in " \t\n":
                k += 1
        if k >= n or s[k] != ")":
            return None
        dest = re.sub(r"\\([!-/:-@\[-`{-~])", r"\1", dest)
        return label, dest, title, k + 1

    def make_link(self, dest, label_html, in_link, title=""):
        r = self.resolver(dest, False)
        if not r or in_link:
            return label_html
        href, external = r[0], r[1]
        if href is None:
            return label_html
        ext = ' target="_blank" rel="noopener noreferrer"' if external else ""
        ttl = f' title="{esc(title)}"' if title else ""
        return f'<a href="{esc(href)}"{ttl}{ext}>{label_html}</a>'

    def make_image(self, label, dest, title):
        alt = plain(self.inline(label, True))
        r = self.resolver(dest, True)
        if not r:
            return esc(alt)
        if r[0] is None:
            return esc(r[2] if len(r) > 2 else alt)
        ttl = f' title="{esc(title)}"' if title else ""
        return f'<img src="{esc(r[0])}" alt="{esc(alt)}"{ttl}>'




# --- Styles -------------------------------------------------------------

STYLES = CSS_MARK + """
:root {
  --bg: #f5f6f4; --surface: #ffffff; --fg: #1d2321; --muted: #566059; --line: #d5dad6;
  --accent: #0f6b5c; --on-accent: #ffffff; --accent-soft: #e3f0ec;
  --link: #1b5b86; --ok: #2b6a3a; --warn: #8a5a00; --bad: #9b2c2c;
  --display: "Avenir Next Condensed", "Arial Narrow", "Roboto Condensed", "Helvetica Neue", Arial, sans-serif;
  --body: "Charter", "Bitstream Charter", "Iowan Old Style", Georgia, "Times New Roman", serif;
  --ui: -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  --mono: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
  color-scheme: light dark;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #131715; --surface: #1b201d; --fg: #e4e8e5; --muted: #a0a9a3; --line: #333a35;
    --accent: #4fc3a9; --on-accent: #0c1512; --accent-soft: #1c2f2a;
    --link: #8ec5e6; --ok: #8ccf98; --warn: #e2b45c; --bad: #f19a9a;
  }
}
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; scroll-padding-top: 12px; }
body { margin: 0; background: var(--bg); color: var(--fg); font-family: var(--body); font-size: 17px; line-height: 1.6; }
.skip { position: absolute; left: 8px; top: -60px; z-index: 10; background: var(--accent); color: var(--on-accent); padding: 8px 12px; font-family: var(--ui); }
.skip:focus { top: 8px; }
.bar { background: var(--surface); border-bottom: 3px solid var(--accent); padding: 12px max(16px, env(safe-area-inset-right, 0px)) 10px max(16px, env(safe-area-inset-left, 0px)); }
.bar-inner { max-width: 820px; margin: 0 auto; }
.brand { font-family: var(--display); font-weight: 700; font-size: 1.15rem; text-decoration: none; color: var(--fg); overflow-wrap: anywhere; }
.badge { font-family: var(--ui); font-size: .72rem; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; padding: 1px 8px; margin-left: 8px; border: 1px solid var(--accent); border-radius: 999px; color: var(--accent); white-space: nowrap; }
nav ul { list-style: none; display: flex; flex-wrap: wrap; gap: 6px; margin: 10px 0 0; padding: 0; }
nav li { margin: 0; max-width: none; }
nav a { display: inline-block; font-family: var(--ui); font-size: .82rem; text-decoration: none; color: var(--fg); padding: 4px 10px; border: 1px solid var(--line); border-radius: 999px; background: var(--bg); }
nav a[aria-current="page"] { background: var(--accent); border-color: var(--accent); color: var(--on-accent); }
nav a:hover { border-color: var(--accent); }
main { padding: 20px max(16px, env(safe-area-inset-right, 0px)) 56px max(16px, env(safe-area-inset-left, 0px)); }
.col { max-width: 820px; margin: 0 auto; min-width: 0; }
.page { margin-bottom: 56px; }
.page + .page { border-top: 3px solid var(--line); padding-top: 28px; }
.private { font-family: var(--ui); font-size: .8rem; color: var(--muted); margin: 0 0 14px; }
.meta { font-family: var(--ui); font-size: .88rem; background: var(--surface); border: 1px solid var(--line); border-left: 4px solid var(--accent); padding: 10px 14px; margin: 0 0 22px; display: grid; gap: 6px; }
.meta .row { display: flex; flex-wrap: wrap; gap: 4px 16px; }
.meta b { font-weight: 600; }
.meta details summary { cursor: pointer; }
.meta details ul { margin: 6px 0 0; }
h1, h2, h3, h4, h5, h6 { font-family: var(--display); line-height: 1.15; text-wrap: balance; }
h1 { font-size: clamp(1.9rem, 6vw, 2.6rem); margin: 0 0 14px; }
h2 { font-size: 1.55rem; margin: 40px 0 10px; padding-top: 10px; border-top: 1px solid var(--line); }
h1 + .meta + h2, h1 + h2 { margin-top: 20px; }
h3 { font-size: 1.22rem; margin: 26px 0 8px; }
h4 { font-size: 1.05rem; margin: 20px 0 6px; }
h5, h6 { font-size: 1rem; margin: 16px 0 6px; }
p, li { max-width: 70ch; overflow-wrap: anywhere; }
a { color: var(--link); text-underline-offset: 2px; overflow-wrap: anywhere; }
a:focus-visible, summary:focus-visible, .scroll:focus-visible { outline: 3px solid var(--accent); outline-offset: 2px; }
blockquote { margin: 16px 0; padding: 10px 14px; background: var(--accent-soft); border-left: 4px solid var(--accent); font-family: var(--ui); font-size: .92rem; }
blockquote > :first-child { margin-top: 0; }
blockquote > :last-child { margin-bottom: 0; }
code { font-family: var(--mono); font-size: .88em; background: var(--surface); border: 1px solid var(--line); padding: 0 4px; border-radius: 3px; overflow-wrap: anywhere; }
pre { overflow-x: auto; background: var(--surface); border: 1px solid var(--line); padding: 10px; max-width: 100%; }
pre code { border: 0; padding: 0; overflow-wrap: normal; }
hr { border: 0; border-top: 1px solid var(--line); margin: 24px 0; }
.scroll { overflow-x: auto; margin: 14px 0; border: 1px solid var(--line); background: var(--surface); -webkit-overflow-scrolling: touch; }
table { border-collapse: collapse; width: 100%; font-family: var(--ui); font-size: .86rem; line-height: 1.4; }
.scroll table { min-width: 560px; }
th, td { text-align: left; vertical-align: top; padding: 7px 9px; border-bottom: 1px solid var(--line); }
th { font-size: .74rem; letter-spacing: .05em; text-transform: uppercase; color: var(--muted); background: var(--bg); }
td { font-variant-numeric: tabular-nums; }
.al-r { text-align: right; } .al-c { text-align: center; }
tr:last-child td { border-bottom: 0; }
ul, ol { padding-left: 22px; }
li { margin: 3px 0; }
li.task { list-style: none; margin-left: -22px; }
li > input[type=checkbox], li > p > input[type=checkbox] { margin-right: 6px; }
img { max-width: 100%; height: auto; border: 1px solid var(--line); }
.chip-long { white-space: normal !important; }
.chip { font-family: var(--ui); font-size: .72rem; letter-spacing: .02em; padding: 1px 7px; border-radius: 999px; border: 1px solid var(--line); white-space: nowrap; color: var(--muted); background: var(--surface); }
.chip-local, .chip-primary { color: var(--ok); border-color: currentColor; }
.chip-secondary { color: var(--link); border-color: currentColor; }
.chip-warn { color: var(--warn); border-color: currentColor; }
.chip-bad { color: var(--bad); border-color: currentColor; }
.chip-weak { color: var(--muted); }
.chip-open { color: var(--muted); border-style: dashed; border-color: currentColor; }
.cards { list-style: none; padding: 0; display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 10px; margin: 14px 0 6px; }
.cards li { max-width: none; margin: 0; }
.cards a { display: block; height: 100%; text-decoration: none; color: var(--fg); background: var(--surface); border: 1px solid var(--line); padding: 12px 14px; }
.cards a:hover { border-color: var(--accent); }
.cards b, .cards span { display: block; }
.cards b { font-family: var(--display); font-size: 1.08rem; margin-bottom: 2px; }
.cards span { font-family: var(--ui); font-size: .84rem; color: var(--muted); }
.cards .state { color: var(--accent); font-weight: 600; margin-bottom: 4px; }
dl.legend { display: grid; grid-template-columns: max-content 1fr; gap: 6px 14px; font-family: var(--ui); font-size: .9rem; margin: 12px 0; }
dl.legend dt, dl.legend dd { margin: 0; }
@media (max-width: 480px) { body { font-size: 16px; } h2 { font-size: 1.35rem; } dl.legend { grid-template-columns: 1fr; gap: 2px; } dl.legend dd { margin-bottom: 8px; } }
@media (max-width: 720px) { nav ul { flex-wrap: nowrap; overflow-x: auto; padding-bottom: 4px; } nav li { flex: none; } }
.top { font-family: var(--ui); font-size: .8rem; margin: 24px 0 0; }
footer { font-family: var(--ui); font-size: .8rem; color: var(--muted); margin-top: 48px; padding-top: 12px; border-top: 1px solid var(--line); }
@media print {
  body { background: #fff; color: #000; font-size: 11pt; }
  .skip, nav, .top { display: none; }
  .bar { border-bottom: 1px solid #000; background: none; }
  .page + .page { break-before: page; }
  .scroll { overflow: visible; }
  .scroll table { min-width: 0; }
  tr, pre, img, blockquote { break-inside: avoid; }
  a { color: inherit; }
  main a[href^="http"]::after { content: " (" attr(href) ")"; font-size: .8em; }
}
"""


def accent_css(accent):
    """Extra rules that retint the accent from reader.accent (#rrggbb)."""
    r, g, b = (int(accent[k:k + 2], 16) for k in (1, 3, 5))
    lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
    on = "#ffffff" if lum < 0.55 else "#111111"
    return (f":root {{ --accent: {accent}; --on-accent: {on}; --accent-soft: color-mix(in srgb, {accent} 12%, var(--surface)); }}\n"
            "@media (prefers-color-scheme: dark) { @supports (color: color-mix(in srgb, red, white)) {\n"
            f"  :root {{ --accent: color-mix(in srgb, {accent} 62%, #ffffff); --on-accent: #111111; "
            f"--accent-soft: color-mix(in srgb, {accent} 22%, var(--surface)); }} }} }}\n")


# --- Checks -------------------------------------------------------------

class Collector(HTMLParser):
    """Collect ids and href/src references from generated HTML."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids, self.dup_ids, self.refs = set(), [], []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            if a["id"] in self.ids:
                self.dup_ids.append(a["id"])
            self.ids.add(a["id"])
        for key in ("href", "src"):
            if a.get(key) is not None:
                self.refs.append((tag, key, a[key]))
        if tag == "meta" and (a.get("http-equiv") or "").lower() == "refresh":
            m = re.search(r"url=(.+)$", a.get("content") or "", re.I)
            if m:
                self.refs.append((tag, "refresh", m.group(1).strip()))


def scrub_paths(doc):
    """Replace local paths in text nodes. Returns (doc, count_in_code, count_in_text)."""
    depth = n_code = n_text = 0
    out = []
    for part in re.split(r"(<[^>]*>)", doc):
        if part.startswith("<"):
            m = re.match(r"<(/?)\s*([A-Za-z0-9]+)", part)
            if m and m.group(2).lower() in ("code", "pre"):
                depth = max(0, depth + (-1 if m.group(1) else 1))
            out.append(part)
            continue
        text = html.unescape(part)
        if depth:
            new, n = PATH_TO_EOL.subn(PATH_REMOVED, text)
            n_code += n
        else:
            new, n = PATH_FULL.subn(
                lambda m: PATH_REMOVED + re.search(r"[.,;:!?)\]}]*$", m.group(0)).group(0), text)
            n_text += n
        out.append(esc(new) if n else part)
    return "".join(out), n_code, n_text


def check_outputs(outputs, root):
    """Resolve every relative href/src in generated HTML. Returns a list of problems."""
    problems = []
    parsed = {}
    for rel, text in outputs.items():
        if rel.endswith(".html"):
            c = Collector()
            c.feed(text)
            c.close()
            parsed[rel] = c
            for dup in c.dup_ids:
                problems.append(f"{rel}: duplicate id #{dup}")
    checked = 0
    for rel, c in sorted(parsed.items()):
        base = posixpath.dirname(rel)
        for tag, key, url in c.refs:
            checked += 1
            low = url.strip().lower()
            if low.startswith(("http://", "https://", "mailto:", "tel:")):
                continue
            if low.startswith("data:") and key == "src" and tag == "img":
                continue
            if re.match(r"[a-z][a-z0-9+.-]*:", low) or low.startswith(("/", "\\")):
                problems.append(f"{rel}: forbidden target {url[:60]}")
                continue
            path, _, frag = url.partition("#")
            frag = urllib.parse.unquote(frag)
            if not path:
                target = rel
            else:
                target = posixpath.normpath(posixpath.join(base, urllib.parse.unquote(path.split("?")[0])))
            if target in outputs:
                if frag and target in parsed and frag not in parsed[target].ids:
                    problems.append(f"{rel}: missing anchor {url}")
            elif target.startswith("..") or not (Path(root) / target).is_file():
                problems.append(f"{rel}: broken link {url}")
    return problems, checked


# --- Reader -------------------------------------------------------------

class Page:
    def __init__(self, slug, src, kind, label="", desc=""):
        self.slug, self.src, self.kind = slug, src, kind
        self.label, self.desc = label, desc
        self.meta, self.md, self.html, self.title = {}, "", "", ""


def humanise(stem):
    return stem.replace("-", " ").replace("_", " ").strip().capitalize()


WIKILINK = re.compile(r"\[\[[^\[\]\n]*\]\] \((\[[^\[\]\n]*\]\([^()\n]*\))\)")
BARE_WIKILINK = re.compile(r"\[\[(?:[^\[\]|\n]*\|)?([^\[\]|\n]*)\]\]")


def clean_wiki_md(md):
    """Wiki articles write links as [[name|Label]] ([Label](path)); keep one plain link."""
    return BARE_WIKILINK.sub(r"\1", WIKILINK.sub(r"\1", md))


def short_label(title):
    if len(title) > 24:
        for sep in (":", " — ", " – ", " - "):
            if sep in title and len(title.split(sep)[0]) >= 4:
                return title.split(sep)[0].strip()
    return title


def lead_text(md, limit=170):
    """A one-line blurb: a 'Bottom line' paragraph if present, else the first plain paragraph."""
    m = re.search(r"^\*\*(?:Bottom line|Summary|Short answer)[.:]?\*\*:?\s*(.+)$", md, re.M | re.I)
    text = m.group(1) if m else ""
    if not text:
        para = []
        for ln in md.split("\n"):
            if not ln.strip():
                if para:
                    break
                continue
            if re.match(r"\s*(#|>|\||[-*+] |\d+[.)] |```|~~~|---)", ln):
                if para:
                    break
                continue
            para.append(ln.strip())
        text = " ".join(para)
    text = re.sub(r"\[(?:" + "|".join(CHIPS) + r")(?:[ ,;:/][^\]\n]*)?\]", "", text, flags=re.I)
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"`([^`]*)`", lambda m: PATH_REMOVED if PATH_FULL.search(m.group(1)) else m.group(1), text)
    text = re.sub(r"[*_`]", "", text).strip()
    if len(text) > limit:
        text = text[:limit].rsplit(" ", 1)[0] + "…"
    return text


class Reader:
    def __init__(self, root, single_file=None):
        self.root = Path(root).resolve()
        self.cfg = {}
        for name in ("fieldbook.config.yml", "fieldbook.config.yaml"):
            f = self.root / name
            if f.is_file():
                cfg = parse_yaml(read_text(f))
                self.cfg = cfg if isinstance(cfg, dict) else {}
                break
        fb = self.cfg.get("fieldbook") if isinstance(self.cfg.get("fieldbook"), dict) else {}
        rd = self.cfg.get("reader") if isinstance(self.cfg.get("reader"), dict) else {}
        self.rd = rd
        self.subject = norm_value(self.cfg.get("subject") or fb.get("title") or self.cfg.get("title")) or self.root.name
        self.release = norm_value(self.cfg.get("release_status") or fb.get("release_status"))
        self.private = self.release.lower().startswith("private")
        self.title = norm_value(rd.get("title")) or self.derive_title(norm_value(fb.get("title")))
        self.footer = norm_value(rd.get("footer")) or (
            "Generated from the Markdown files in this Fieldbook; the Markdown is the canonical record. "
            "Prices, ratings and rules change, so verify a figure before relying on it.")
        accent = norm_value(rd.get("accent"))
        self.accent = accent if re.fullmatch(r"#[0-9A-Fa-f]{6}", accent) else ""
        self.single = None
        want = single_file
        if want is None and str(self.cfg.get("output_mode", "")).lower() == "single-file":
            want = norm_value(self.cfg.get("single_file")) or "fieldbook.html"
        if want is not None:
            self.single = self.check_single_path(want)
        self.status = norm_value(self.cfg.get("status") or fb.get("status")).lower().replace("_", "-").strip()
        self.output_mode = str(self.cfg.get("output_mode") or fb.get("output_mode") or "").lower().strip()
        raw = rd.get("include_internal")
        if isinstance(raw, str):
            raw = {"true": True, "yes": True, "false": False, "no": False}.get(raw.strip().lower())
        self.include_internal = raw if isinstance(raw, bool) else not (
            self.single or self.release.lower().startswith(("review", "public")))
        self.left_out = []
        self.shift = 1 if self.single else 0
        self.outdir = posixpath.dirname(self.single) if self.single else "site"
        self.pages, self.by_src, self.by_slug = [], {}, {}
        self.dropped, self.failures, self.notes = {}, [], []

    def refuse_reason(self):
        """Why the config says not to build a reader, or ''."""
        if self.status == "on-hold":
            return "the config has status: on-hold, so this Fieldbook is paused"
        if self.output_mode == "markdown-kb":
            return "the config asks for Markdown only (output_mode: markdown-kb)"
        return ""

    @staticmethod
    def check_single_path(path):
        p = path.replace("\\", "/").strip()
        norm = posixpath.normpath(p)
        if (not p or p.startswith("/") or re.match(r"[A-Za-z]:", p) or norm.startswith("..")
                or not norm.lower().endswith((".html", ".htm"))):
            raise ValueError(f"--single-file must be a relative .html path inside the Fieldbook: {path}")
        return norm

    def derive_title(self, fb_title):
        if fb_title:
            return fb_title
        first = re.split(r"\s[—–-]\s|:\s", self.subject)[0].strip()
        base = first if len(first) >= 8 else self.subject
        return base if "fieldbook" in base.lower() else base + " Fieldbook"

    # discovery
    def add_page(self, page):
        self.pages.append(page)
        self.by_slug[page.slug] = page
        if page.src:
            self.by_src[page.src] = page

    def unique_slug(self, stem, prefix):
        """A page name unused on a case-insensitive filesystem."""
        taken = {"index"} | {r[0] for r in ROLES} | {s.lower() for s in self.by_slug}
        slug = stem
        if slug.lower() in taken:
            slug = f"{prefix}-{stem}"
        n = 2
        while slug.lower() in taken:
            slug = f"{prefix}-{stem}-{n}"
            n += 1
        return slug

    def discover(self):
        root = self.root
        readme = next((f for f in ("README.md", "readme.md") if (root / f).is_file()), None)
        self.add_page(Page("index", readme, "index", "Start"))
        internal = {"guidance", "local-evidence-inventory"}
        topics = sorted(p.name for p in (root / "topics").glob("*.md")) if (root / "topics").is_dir() else []
        order = self.rd.get("topics") if isinstance(self.rd.get("topics"), list) else []
        wanted = [Path(norm_value(t)).stem for t in order]
        topics.sort(key=lambda n: (wanted.index(Path(n).stem) if Path(n).stem in wanted else len(wanted), n))
        for name in wanted:
            if not any(Path(t).stem == name for t in topics):
                self.notes.append(f"reader.topics lists '{name}' but topics/{name}.md does not exist")
        for name in topics:
            stem = Path(name).stem
            slug = self.unique_slug(stem, "topic")
            self.add_page(Page(slug, f"topics/{name}", "topic"))
        articles = self.rd.get("wiki_articles")
        for rel in articles if isinstance(articles, list) else []:
            src = self.check_wiki_article(norm_value(rel))
            if src and src not in self.by_src:
                self.add_page(Page(self.unique_slug(Path(src).stem, "data"), src, "wiki"))
        claimed = set()
        for key, label, desc, cands in ROLES:
            for cand in cands:
                if (root / cand).is_file():
                    claimed.add(cand)
                    if key in internal and not self.include_internal:
                        self.left_out.append(cand)
                    else:
                        self.add_page(Page(key, cand, "support", label, desc))
                    break
        for d in EXTRA_DIRS:
            if (root / d).is_dir():
                for f in sorted(p.name for p in (root / d).glob("*.md")):
                    rel = f"{d}/{f}"
                    if rel in claimed:
                        continue
                    slug = self.unique_slug(Path(f).stem, d)
                    self.add_page(Page(slug, rel, "extra", humanise(Path(f).stem), ""))
        if self.left_out:
            self.notes.append("left out as internal (reader.include_internal: true adds them): "
                              + ", ".join(self.left_out))
        for page in self.pages:
            if page.src:
                page.meta, page.md = split_frontmatter(read_text(root / page.src))
                if page.kind == "wiki":
                    page.md = clean_wiki_md(page.md)
            title = norm_value(page.meta.get("title"))
            if not title:
                m = re.search(r"^# +(.+?)\s*#*\s*$", page.md, re.M)
                title = re.sub(r"[*_`]", "", m.group(1)) if m else ""
            page.title = title or page.label or humanise(Path(page.src or page.slug).stem)
        self.by_src_ci = {k.lower(): v for k, v in self.by_src.items()}
        self.index = self.by_slug["index"]
        self.index.title = self.title

    def check_wiki_article(self, rel):
        """A reader.wiki_articles entry as a normalised source path, or '' with a failure recorded."""
        norm = posixpath.normpath(rel.replace("\\", "/"))
        file = (self.root / norm).resolve()
        roots = self.cfg.get("source_roots")
        roots = [(self.root / norm_value(r)).resolve() for r in roots] if isinstance(roots, list) else []
        if not (norm.lower().endswith(".md") and file.is_file()
                and any(file.is_relative_to(r) for r in roots)):
            self.failures.append(f"reader.wiki_articles: {rel} is not a Markdown file inside a declared source root")
            return ""
        return norm

    # links
    def drop(self, page, target, reason, fail=False):
        key = (page.src or page.slug, target, reason)
        self.dropped[key] = self.dropped.get(key, 0) + 1
        if fail:
            self.failures.append(f"{key[0]}: link to local path dropped: {target[:80]}")

    def href_to(self, slug, frag=""):
        if self.single:
            return f"#{slug}--{frag}" if frag else f"#page-{slug}"
        return f"{slug}.html" + (f"#{frag}" if frag else "")

    def resolve(self, page, href, is_image):
        raw = href.strip()
        if not raw:
            self.drop(page, "(empty)", "empty target")
            return None
        compact = re.sub(r"[\x00-\x20\x7f]", "", raw)
        low = compact.lower()
        if low.startswith("#"):
            frag = compact[1:]
            if is_image or not frag:
                return None if is_image else ("#", False)
            return (f"#{page.slug}--{frag}" if self.single else "#" + frag), False
        m = re.match(r"([a-z][a-z0-9+.-]*):", low)
        if m:
            scheme = m.group(1)
            if len(scheme) == 1 and compact[1:3] in (":\\", ":/"):
                self.drop(page, raw, "absolute local path", True)
                return None
            if scheme == "file":
                self.drop(page, raw, "file: link", True)
                return None
            if scheme in ("http", "https"):
                if is_image:
                    self.drop(page, raw, "remote image")
                    return None
                return raw, True
            if scheme in ("mailto", "tel") and not is_image:
                return raw, False
            self.drop(page, raw, f"blocked scheme {scheme}:")
            return None
        if compact.startswith("\\\\"):
            self.drop(page, raw, "UNC path", True)
            return None
        if compact.startswith(("/", "\\")):
            self.drop(page, raw, "absolute path")
            return None
        path, _, frag = compact.partition("#")
        path = path.split("?")[0]
        base = posixpath.dirname(page.src or "")
        p = urllib.parse.unquote(path).replace("\\", "/")
        if not p:
            return None
        target = posixpath.normpath(posixpath.join(base, p))
        known = self.by_src.get(target) or self.by_src_ci.get(target.lower())
        if known and not is_image:
            return self.href_to(known.slug, frag), False
        if target.startswith("..") or target == ".":
            self.drop(page, raw, "leaves the Fieldbook" if target != "." else "directory")
            return None
        if target.lower().endswith(".md") and not is_image:
            pg = self.by_src.get(target) or self.by_src_ci.get(target.lower())
            if pg:
                return self.href_to(pg.slug, frag), False
            self.drop(page, raw, "not a generated page")
            return None
        ext = posixpath.splitext(target)[1].lower()
        parts = set(target.lower().split("/"))
        if ext in NOT_READER_EXT or "research_notes" in parts or ".git" in parts or ext == ".md":
            self.drop(page, raw, "not a reader file")
            return None
        file = self.root / target
        if not file.is_file():
            self.drop(page, raw, "missing target")
            return None
        if is_image and self.single:
            return self.embed_image(page, raw, target, file, ext)
        rel = posixpath.relpath(target, self.outdir or ".")
        if self.single and rel.startswith(".."):
            self.drop(page, raw, "outside the single file's folder")
            return None
        return urllib.parse.quote(rel, safe="/") + (("#" + frag) if frag and not is_image else ""), False

    def embed_image(self, page, raw, target, file, ext):
        mime = IMAGE_MIME.get(ext)
        size = file.stat().st_size
        if not mime:
            self.drop(page, raw, "image type not embeddable")
            return None
        if size > IMAGE_LIMIT:
            self.drop(page, raw, f"image over 2 MB ({size / 1e6:.1f} MB), not embedded")
            return (None, False, f"[image not embedded: {posixpath.basename(target)}, {size / 1e6:.1f} MB]")
        data = base64.b64encode(file.read_bytes()).decode("ascii")
        self.notes.append(f"embedded {target} ({size} bytes)")
        return f"data:{mime};base64,{data}", False

    # rendering
    def render_pages(self):
        for page in self.pages:
            if not page.src:
                continue
            md = Markdown(resolver=lambda h, im, pg=page: self.resolve(pg, h, im),
                          shift=1 if page.kind == "index" else self.shift,
                          id_prefix=f"{page.slug}--" if self.single else "")
            page.html = md.render(page.md)
            page.headings = md.headings
            if page.kind == "index" and not page.html.startswith("<h2 "):
                page.html = "<h2>Start here</h2>\n" + page.html

    def inline_for(self, page, text):
        md = Markdown(resolver=lambda h, im, pg=page: self.resolve(pg, h, im))
        return md.inline(text)

    def meta_box(self, page):
        meta = page.meta
        if not meta:
            return ""
        row = []
        if meta.get("status"):
            row.append(f"<span><b>Status</b> {esc(norm_value(meta['status']))}</span>")
        if meta.get("updated"):
            row.append(f"<span><b>Updated</b> {esc(norm_value(meta['updated']))}</span>")
        src = self.sources_label(meta.get("sources"))
        if src:
            row.append(f"<span>{src}</span>")
        bits = []
        if row:
            bits.append('<div class="row">' + "".join(row) + "</div>")
        conf = norm_value(meta.get("confidence")).strip()
        if conf:
            if len(conf) > 140:
                head = conf[:140].rsplit(" ", 1)[0] + "…"
                bits.append(f"<details><summary><b>Confidence</b> {esc(head)}</summary>"
                            f"<p>{self.inline_for(page, conf)}</p></details>")
            else:
                bits.append(f"<div><b>Confidence</b> {self.inline_for(page, conf)}</div>")
        oq = meta.get("open_questions")
        if isinstance(oq, list) and oq:
            items = "".join(f"<li>{self.inline_for(page, norm_value(q))}</li>" for q in oq)
            noun = "open question" if len(oq) == 1 else "open questions"
            bits.append(f"<details><summary>{len(oq)} {noun}</summary><ul>{items}</ul></details>")
        if not bits:
            return ""
        return '<div class="meta" role="group" aria-label="Page details">' + "".join(bits) + "</div>"

    @staticmethod
    def sources_label(value):
        if value is None or value == "" or value == []:
            return ""
        if isinstance(value, bool):
            return ""
        count = None
        if isinstance(value, int):
            count = value
        elif isinstance(value, (list, tuple, dict)):
            count = len(value)
        elif isinstance(value, str) and value.strip().isdigit():
            count = int(value.strip())
        if count is not None:
            return f"<b>{count}</b> {'source' if count == 1 else 'sources'}"
        return f"<b>Sources</b> {esc(norm_value(value))}"

    def page_body(self, page):
        level = 1 + self.shift
        body = page.html
        meta = self.meta_box(page)
        if page.kind == "wiki":
            note = norm_value(self.rd.get("wiki_note")) or (
                "Full data page: a wiki article rendered as it stands, keeping the wiki's own tags. "
                "Correct it in the wiki and rebuild.")
            meta = f'<div class="meta">{esc(note)}</div>\n' + meta
        if body.startswith(f"<h{level} "):
            return re.sub(rf"(</h{level}>)", lambda m: m.group(1) + "\n" + meta, body, count=1)
        return f"<h{level}>{esc(page.title)}</h{level}>\n{meta}\n{body}"

    # index sections
    def newest_update(self):
        dates = []
        pool = [p for p in self.pages if p.kind == "topic"] or self.pages
        for p in pool:
            m = re.match(r"\d{4}-\d{2}-\d{2}", norm_value(p.meta.get("updated")))
            if m:
                dates.append(m.group(0))
        return max(dates) if dates else ""

    def index_html(self):
        h = 1
        topics = [p for p in self.pages if p.kind == "topic"]
        wiki = [p for p in self.pages if p.kind == "wiki"]
        evid = [p for p in self.pages if p.kind in ("support", "extra")]
        rows = [f"<div><b>Subject</b> {esc(self.subject)}</div>"]
        aud = norm_value(self.cfg.get("audience"))
        if aud:
            rows.append(f"<div><b>Audience</b> {esc(aud)}</div>")
        if self.release:
            badge = ' <span class="badge">Private</span>' if self.private else ""
            rows.append(f"<div><b>Release status</b> {esc(self.release)}{badge}</div>")
        else:
            rows.append("<div><b>Release status</b> not stated</div>")
        newest = self.newest_update()
        rows.append(f"<div><b>Last updated</b> {esc(newest) if newest else 'not stated'}"
                    " (newest topic page)</div>")
        newest_src = norm_value(self.rd.get("newest_source"))
        if newest_src:
            rows.append(f"<div><b>Newest source</b> {esc(newest_src)}</div>")
        rows.append(f"<div><b>Contents</b> {len(topics)} topic page{'s' if len(topics) != 1 else ''}, "
                    + (f"{len(wiki)} full data page{'s' if len(wiki) != 1 else ''}, " if wiki else "")
                    + f"{len(evid)} evidence page{'s' if len(evid) != 1 else ''}</div>")
        steer = ""
        if "guidance" in self.by_slug:
            steer = (f' To steer the next research pass, add a dated entry to the '
                     f'<a href="{esc(self.href_to("guidance"))}">guidance log</a>.')
        rows.append("<div><b>How to use</b> Start with the section below, then open a topic. Every claim carries "
                    "a provenance label; the legend explains them. Follow the evidence routes to check a claim "
                    "against its sources. The Markdown files are the canonical record and this reader is a "
                    f"generated view of them.{steer}</div>")
        out = [f"<h{h}>{esc(self.title)}</h{h}>", ""]
        sec = '<section id="fb-start">\n' + self.index.html + "\n</section>" if self.index.src else ""
        out.append(sec)
        cards = []
        for p in topics:
            state = " · ".join(x for x in (norm_value(p.meta.get("status")), norm_value(p.meta.get("updated"))) if x)
            blurb = lead_text(p.md)
            cards.append(f'<li><a href="{esc(self.href_to(p.slug))}"><b>{esc(p.title)}</b>'
                         + (f'<span class="state">{esc(state)}</span>' if state else "")
                         + (f"<span>{esc(blurb)}</span>" if blurb else "") + "</a></li>")
        if cards:
            out.append(f'<section id="fb-topics"><h{h + 1}>Topics</h{h + 1}><ul class="cards">' + "".join(cards) + "</ul></section>")
        if wiki:
            data = [f'<li><a href="{esc(self.href_to(p.slug))}"><b>{esc(p.title)}</b></a></li>' for p in wiki]
            out.append(f'<section id="fb-data"><h{h + 1}>Full data</h{h + 1}><ul class="cards">' + "".join(data) + "</ul></section>")
        routes = [f'<li><a href="{esc(self.href_to(p.slug))}"><b>{esc(p.label or p.title)}</b>'
                  f"<span>{esc(p.desc or p.title)}</span></a></li>" for p in evid]
        if routes:
            out.append(f'<section id="fb-evidence"><h{h + 1}>Evidence</h{h + 1}><ul class="cards">' + "".join(routes) + "</ul></section>")
        legend = "".join(f'<dt><span class="chip chip-{c}">{esc(k)}</span></dt><dd>{esc(d)}</dd>' for k, (c, d) in CHIPS.items())
        out.append(f'<section id="fb-legend"><h{h + 1}>Provenance labels</h{h + 1}><dl class="legend">{legend}</dl></section>')
        out.append(self.next_html(h + 1))
        body = "\n".join(x for x in out if x)
        # Jump only to sections this book has; one with no topics or no start page has fewer.
        jump = " &middot; ".join(f'<a href="#fb-{k}">{v}</a>' for k, v in
                                 (("start", "Start here"), ("topics", "Topics"), ("data", "Full data"), ("evidence", "Evidence"),
                                  ("legend", "Labels"), ("next", "Next research"))
                                 if f'id="fb-{k}"' in body)
        out[1] = ('<div class="meta" role="group" aria-label="Orientation">' + "".join(rows)
                  + f'<div class="row">{jump}</div></div>')
        return "\n".join(x for x in out if x)

    def next_html(self, h):
        items = []
        gap = self.by_slug.get("gap-register")
        if gap:
            rows = [split_row(ln) for ln in gap.md.split("\n") if ln.strip().startswith("|")]
            rows = [r for r in rows if r and not all(re.fullmatch(r":?-+:?", c) for c in r if c)]
            if rows:
                rows = rows[1:]
            rows = [r for r in rows if not any(re.fullmatch(r"(?i)resolved|closed|merged|done", c) for c in r)]
            if not rows:
                for ln in gap.md.split("\n"):
                    m = re.match(r"\s*[-*] (.+)", ln)
                    if m:
                        rows.append([m.group(1)])
            for r in rows[:6]:
                cells = [c for c in r[:2] if c]
                if cells:
                    items.append("<li>" + self.inline_for(gap, " — ".join(cells)) + "</li>")
        links = []
        for slug, label in (("gap-register", "gap register"), ("refresh-backlog", "refresh backlog"),
                            ("guidance", "guidance log")):
            if slug in self.by_slug:
                links.append(f'<a href="{esc(self.href_to(slug))}">{label}</a>')
        if not items and not links:
            return ""
        guide = self.by_slug.get("guidance")
        dates = sorted(re.findall(r"^##\s+(\d{4}-\d{2}-\d{2})", guide.md, re.M)) if guide else []
        tail = f" Latest steering entry: {dates[-1]}." if dates else ""
        text = f"<p>Full lists: {', '.join(links)}.{tail}</p>" if links else ""
        ul = "<ul>" + "".join(items) + "</ul>" if items else ""
        return f'<section id="fb-next"><h{h}>Next research</h{h}>{ul}{text}</section>'

    # chrome
    def nav_html(self, current):
        def item(p):
            label = "Start" if p.kind == "index" else (p.label if p.kind == "support" else short_label(p.title))
            labels = self.rd.get("labels")
            if isinstance(labels, dict) and norm_value(labels.get(p.slug)):
                label = norm_value(labels.get(p.slug))
            cur = ' aria-current="page"' if (not self.single and p.slug == current) else ""
            return f'<li><a href="{esc(self.href_to(p.slug))}"{cur}>{esc(label)}</a></li>'

        read = [p for p in self.pages if p.kind in ("index", "topic")]
        evid = [p for p in self.pages if p.kind in ("support", "extra")]
        wiki = [p for p in self.pages if p.kind == "wiki"]
        label = "Contents" if self.single else "Fieldbook pages"
        text = f'<nav aria-label="{label}"><ul>{"".join(item(p) for p in read)}</ul>'
        if wiki:
            text += f'<ul aria-label="Full data">{"".join(item(p) for p in wiki)}</ul>'
        if evid:
            text += f'<ul aria-label="Evidence">{"".join(item(p) for p in evid)}</ul>'
        return text + "</nav>"

    def head(self, title, css):
        robots = '<meta name="robots" content="noindex">\n' if self.private else ""
        return ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
                '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
                + GENERATOR_META + "\n" + robots + '<meta name="color-scheme" content="light dark">\n'
                + f"<title>{esc(title)}</title>\n{css}\n</head>\n")

    def banner(self):
        if not self.private:
            return ""
        newest = self.newest_update()
        when = f" · updated {esc(newest)}" if newest else ""
        return f'<p class="private"><b>Private Fieldbook</b> · not for publication{when}</p>\n'

    def shell(self, page_title, current, main_inner, css):
        brand = f'<a class="brand" href="{esc(self.href_to("index"))}">{esc(self.title)}</a>'
        if self.private:
            brand += ' <span class="badge">Private</span>'
        return (self.head(page_title, css)
                + '<body id="fb-top">\n<a class="skip" href="#fb-main">Skip to content</a>\n'
                + f'<header class="bar"><div class="bar-inner">{brand}\n{self.nav_html(current)}</div></header>\n'
                + f'<main id="fb-main"><div class="col">\n{self.banner()}{main_inner}\n'
                + f"<footer>{esc(self.footer)}</footer>\n</div></main>\n</body>\n</html>\n")

    def stylesheet(self):
        return STYLES + (accent_css(self.accent) if self.accent else "")

    # outputs
    def build_outputs(self):
        out = {}
        self.render_pages()
        if self.single:
            sections = []
            for p in self.pages:
                if p.kind == "index":
                    inner = self.index_html()
                else:
                    inner = self.page_body(p)
                sections.append(f'<section class="page" id="page-{esc(p.slug)}">\n{inner}\n'
                                '<p class="top"><a href="#fb-top">Back to top</a></p>\n</section>')
            out[self.single] = scrub_page(self.shell(self.title, "index", "\n".join(sections),
                                                     f"<style>\n{self.stylesheet()}</style>"), self)
            return out
        css = '<link rel="stylesheet" href="styles.css">'
        for p in self.pages:
            inner = self.index_html() if p.kind == "index" else self.page_body(p)
            title = self.title if p.kind == "index" else f"{p.title} · {self.title}"
            out[f"site/{p.slug}.html"] = scrub_page(self.shell(title, p.slug, inner, css), self, p)
        out["site/styles.css"] = self.stylesheet()
        out["index.html"] = (
            "<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            + GENERATOR_META + "\n"
            + (f"<title>{esc(self.title)}</title>\n")
            + '<meta http-equiv="refresh" content="0; url=site/index.html">\n</head>\n<body>\n'
            + f'<p><a href="site/index.html">Open {esc(self.title)}</a></p>\n</body>\n</html>\n')
        return out


def scrub_page(doc, reader, page=None):
    doc, in_code, in_text = scrub_paths(doc)
    where = (page.src or page.slug) if page else (reader.single or "")
    if in_code:
        reader.notes.append(f"{where}: {in_code} local path(s) in code text replaced")
    if in_text:
        reader.failures.append(f"{where}: {in_text} local path(s) in text replaced")
    return doc


# --- CLI ----------------------------------------------------------------

def plan(reader):
    reader.discover()
    outputs = reader.build_outputs()
    problems, checked = check_outputs(outputs, reader.root)
    return outputs, problems, checked


def refusals(reader, outputs):
    refused = []
    for rel in sorted(outputs):
        f = reader.root / rel
        if not f.is_file():
            continue
        old = f.read_text(encoding="utf-8", errors="replace")
        if rel.endswith(".html"):
            if GENERATOR_META not in old:
                refused.append(rel)
        elif rel.endswith(".css") and CSS_MARK not in old and old != outputs[rel]:
            refused.append(rel)
    return refused


def escaping(reader, outputs):
    """Output paths whose real location (links, junctions) is outside the Fieldbook root."""
    bad = []
    for rel in sorted(outputs):
        target = reader.root / rel
        for path in (target.parent, target):
            try:
                inside = path.resolve().is_relative_to(reader.root)
            except OSError:
                inside = False
            if not inside:
                bad.append(rel)
                break
    return bad


def run(argv=None):
    ap = argparse.ArgumentParser(description="Build a static HTML reader for a Fieldbook.")
    ap.add_argument("root", help="Fieldbook root folder")
    ap.add_argument("--dry-run", action="store_true", help="list pages and problems; write nothing")
    ap.add_argument("--force", action="store_true", help="overwrite HTML files not made by this script")
    ap.add_argument("--single-file", metavar="PATH", help="write one self-contained HTML file at PATH under the root")
    args = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    root = Path(args.root)
    if not root.is_dir():
        print(f"not a folder: {root}")
        return 3
    try:
        reader = Reader(root, args.single_file)
    except ValueError as e:
        print(e)
        return 3
    reason = reader.refuse_reason()
    if reason and not args.force:
        print(f"{GENERATOR}: REFUSED to build: {reason}. Nothing written. Use --force to build anyway.")
        return 2
    outputs, problems, checked = plan(reader)
    print(f"{GENERATOR}: {reader.root}")
    escaped = escaping(reader, outputs)
    if escaped:
        print("REFUSED: these outputs resolve outside the Fieldbook root (junction or symlink); nothing written:")
        for rel in escaped:
            print(f"  {rel}")
        return 2
    refused = [] if args.force else refusals(reader, outputs)
    print(f"mode: {'single-file ' + reader.single if reader.single else 'multi-page'}"
          f"{' (dry run)' if args.dry_run else ''}")
    print(f"pages: {len(reader.pages)} ({sum(1 for p in reader.pages if p.kind == 'topic')} topics)")
    if refused:
        print(f"REFUSED to overwrite {len(refused)} file(s) not made by {GENERATOR}; nothing written. Use --force:")
        for rel in refused:
            print(f"  {rel}")
    elif args.dry_run:
        print("would write:")
        for rel in sorted(outputs):
            print(f"  {rel}")
    else:
        for rel, text in sorted(outputs.items()):
            f = reader.root / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            with open(f, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
        print(f"wrote {len(outputs)} file(s):")
        for rel in sorted(outputs):
            print(f"  {rel}")
    if reader.dropped:
        print(f"links and images shown as text ({len(reader.dropped)} distinct):")
        for (src, target, reason), n in sorted(reader.dropped.items()):
            print(f"  {src} -> {target}  [{reason}]" + (f" x{n}" if n > 1 else ""))
    for note in reader.notes:
        if not note.startswith("embedded "):
            print(f"note: {note}")
    emb = sum(1 for n in reader.notes if n.startswith("embedded "))
    if emb:
        print(f"embedded images: {emb}")
    if not reader.single and not refused:
        stale = sorted(str(p.relative_to(reader.root)).replace("\\", "/")
                       for p in (reader.root / "site").glob("*.html")
                       if f"site/{p.name}" not in outputs and GENERATOR_META in p.read_text(encoding="utf-8", errors="replace"))
        for rel in stale:
            print(f"note: {rel} was made by this script but is not in this build; left in place")
    for f in reader.failures:
        print(f"PROBLEM: {f}")
    for p in problems:
        print(f"PROBLEM: {p}")
    print(f"self-check: {checked} references checked, {len(problems)} broken")
    if refused:
        return 2
    return 1 if (reader.failures or problems) else 0


if __name__ == "__main__":
    sys.exit(run())
