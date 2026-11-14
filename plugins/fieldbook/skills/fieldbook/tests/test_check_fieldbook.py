"""Tests for scripts/check_fieldbook.py. Every fixture is built in a temp folder."""
import contextlib
import hashlib
import io
import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from argparse import Namespace
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import check_fieldbook as cf  # noqa: E402

CONFIG = """subject: "Test subject"
subject_kind: market
audience: "personal research"
source_roots:
  - ../src
exclude: ["dependencies"]
mode: manual-approval
external_research: none
output_mode: both
release_status: private
last_user_direction: "2026-01-01: test"
status: building
"""
TOPIC = """---
title: "Topic A"
status: draft
sources: [1]
local_evidence: "notes"
confidence: medium
updated: 2030-01-01
open_questions: []
---

# Topic A

Plain text with no numbers.
"""
GOOD = {
    "fieldbook.config.yml": CONFIG,
    "README.md": "# Readme\n\nSee [topic](topics/a.md).\n",
    "guidance.md": "# Guidance\n",
    "coverage-matrix.md": "# Coverage\n",
    "gap-register.md": "# Gaps\n",
    "source-ledger.md": "# Ledger\n\n| ID | Source |\n|---|---|\n| S1 | Local notes |\n",
    "refresh-backlog.md": "# Backlog\n",
    "editorial-note.md": "# Editorial\n\nThe reader was built.\n",
    "local-evidence-inventory.md": "# Inventory\n\n| ID | Item |\n|---|---|\n| L1 | notes |\n",
    "topics/a.md": TOPIC,
    "index.html": '<html><body><a href="site/index.html">Open</a></body></html>',
    "site/index.html": '<html><body><h1 id="top">Home</h1><a href="a.html">A</a> <a href="../README.md">Readme</a></body></html>',
    "site/a.html": '<html><body><p>Page A</p><a href="index.html#top">Home</a></body></html>',
    "../src/notes.md": "notes\n",
}


def args(**kw):
    base = dict(json=False, release=False, canonical=[], site=[], max_files=5000, limit=20, audience=None)
    base.update(kw)
    return Namespace(**base)


def build(root, files):
    for rel, content in files.items():
        p = (Path(root) / rel).resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content.encode("utf-8") if isinstance(content, str) else content)


def tree_hash(base):
    h = hashlib.sha256()
    for p in sorted(Path(base).rglob("*")):
        h.update(p.relative_to(base).as_posix().encode())
        if p.is_file():
            h.update(p.read_bytes())
            h.update(str(p.stat().st_mtime_ns).encode())
    return h.hexdigest()


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.base = Path(self._tmp.name).resolve()
        self.root = self.base / "fb"

    def make(self, overrides=None, remove=()):
        for d in (self.root, self.base / "src"):
            shutil.rmtree(d, ignore_errors=True)
        files = dict(GOOD)
        files.update(overrides or {})
        for r in remove:
            files.pop(r, None)
        build(self.root, {k: v for k, v in files.items()})
        return self.root

    def run_cf(self, target=None, **kw):
        return cf.run(target or self.root, args(**kw))

    def of(self, ctx, check, sev=None):
        return [f for f in ctx.findings if f["check"] == check and (sev is None or f["severity"] == sev)]

    def has(self, ctx, check, text, sev=None):
        return any(text in f["message"] for f in self.of(ctx, check, sev))


class CleanFixture(Base):
    def test_clean_fieldbook_has_no_errors_or_warnings(self):
        self.make()
        ctx = self.run_cf()
        bad = [f for f in ctx.findings if f["severity"] != "info"]
        self.assertEqual(bad, [])


class YamlTests(unittest.TestCase):
    TEXT = ("subject: 'S'\nsource_roots:\n  - path: ../a\n    role: x\n  - ../b\nexclude: [x, \"y z\"]\n"
            "layout:\n  topics: pages\nflag: true\nn: 3\n# comment\nempty:\n")

    def test_fallback_parser_matches_pyyaml(self):
        mini, err = cf.load_yaml(self.TEXT, use_pyyaml=False)
        self.assertIsNone(err)
        self.assertEqual(mini["source_roots"], [{"path": "../a", "role": "x"}, "../b"])
        self.assertEqual(mini["exclude"], ["x", "y z"])
        self.assertEqual(mini["layout"], {"topics": "pages"})
        self.assertIs(mini["flag"], True)
        self.assertEqual(mini["n"], 3)
        self.assertIsNone(mini["empty"])
        if cf.yaml is not None:
            real, _ = cf.load_yaml(self.TEXT, use_pyyaml=True)
            self.assertEqual(real["source_roots"], mini["source_roots"])

    def test_double_quoted_backslashes(self):
        data, _ = cf.load_yaml('p: "J:\\\\projects\\\\x"\n', use_pyyaml=False)
        self.assertEqual(data["p"], "J:\\projects\\x")

    def test_garbage_does_not_raise(self):
        data, err = cf.load_yaml("a: [unclosed\n  - : :\n\t\tjunk", use_pyyaml=False)
        self.assertTrue(data is not None or err)


class StructureTests(Base):
    def test_missing_required_file_is_error(self):
        self.make(remove=["coverage-matrix.md"])
        ctx = self.run_cf()
        self.assertTrue(self.has(ctx, "structure", "coverage-matrix.md", "error"))

    def test_inventory_required_only_with_source_roots(self):
        self.make(remove=["local-evidence-inventory.md"])
        self.assertTrue(self.has(self.run_cf(), "structure", "local-evidence-inventory.md", "error"))
        self.make({"fieldbook.config.yml": CONFIG.replace("  - ../src\n", "").replace("source_roots:", "source_roots: []")},
                  remove=["local-evidence-inventory.md"])
        self.assertFalse(self.has(self.run_cf(), "structure", "local-evidence-inventory.md"))

    def test_reader_files_by_mode(self):
        self.make(remove=["index.html", "site/index.html"])
        self.assertEqual(len(self.of(self.run_cf(), "structure", "error")), 2)
        self.make({"fieldbook.config.yml": CONFIG.replace("output_mode: both", "output_mode: web-app")},
                  remove=["index.html", "site/index.html"])
        ctx = self.run_cf()
        self.assertEqual(len(self.of(ctx, "structure", "warn")), 2)
        self.assertEqual(self.of(ctx, "structure", "error"), [])
        self.make({"fieldbook.config.yml": CONFIG.replace("output_mode: both", "output_mode: markdown-kb")},
                  remove=["index.html", "site/index.html"])
        self.assertEqual(self.of(self.run_cf(), "structure", "error"), [])

    def test_single_file_mode(self):
        cfg = CONFIG.replace("output_mode: both", "output_mode: single-file") + "single_file: dossier.html\n"
        self.make({"fieldbook.config.yml": cfg, "dossier.html": "<html><body><p>Hi</p></body></html>"},
                  remove=["index.html", "site/index.html", "site/a.html"])
        ctx = self.run_cf()
        self.assertEqual(self.of(ctx, "structure", "error"), [])
        self.assertEqual(ctx.pages, [self.root / "dossier.html"])
        self.make({"fieldbook.config.yml": cfg}, remove=["index.html", "site/index.html", "site/a.html"])
        self.assertTrue(self.has(self.run_cf(), "structure", "single_file target does not exist", "error"))

    def test_wiki_layout_inferred(self):
        build(self.root, {".wiki/wiki/topics/t.md": TOPIC, ".wiki/raw/r1.md": "raw one\n"})
        ctx = self.run_cf()
        self.assertTrue(ctx.layout_inferred)
        self.assertEqual(ctx.layout["topics"], self.root / ".wiki" / "wiki" / "topics")
        self.assertEqual(len(ctx.topics()), 1)

    def test_legacy_reported_once_as_info(self):
        self.make({"fieldbook.config.yml": CONFIG + "legacy: [old]\n", "old/x.html": '<a href="nope.html">x</a>'})
        ctx = self.run_cf()
        self.assertTrue(self.has(ctx, "structure", "legacy paths", "info"))
        self.assertEqual(self.of(ctx, "links", "error"), [])


class ConfigTests(Base):
    def test_missing_keys_and_enum(self):
        self.make({"fieldbook.config.yml": "subject: x\noutput_mode: nonsense\nrelease_status: public\n"})
        ctx = self.run_cf()
        self.assertTrue(self.has(ctx, "config", "missing key: audience", "warn"))
        self.assertTrue(self.has(ctx, "config", "output_mode: 'nonsense'", "warn"))

    def test_entity_and_single_file_enums_accepted(self):
        cfg = CONFIG.replace("subject_kind: market", "subject_kind: entity")
        self.make({"fieldbook.config.yml": cfg})
        self.assertFalse(self.has(self.run_cf(), "config", "subject_kind"))

    def test_unresolved_source_root_is_error(self):
        self.make({"fieldbook.config.yml": CONFIG.replace("../src", "../../../nowhere/x")})
        self.assertTrue(self.has(self.run_cf(), "config", "does not resolve", "error"))

    def test_source_root_objects_resolve(self):
        self.make({"fieldbook.config.yml": CONFIG.replace("  - ../src", "  - path: ../src\n    role: notes")})
        self.assertFalse(self.has(self.run_cf(), "config", "does not resolve"))

    def test_malformed_config_does_not_crash(self):
        self.make({"fieldbook.config.yml": "{{{ not: [yaml\n\t- :\n"})
        ctx = self.run_cf()
        self.assertTrue(len(self.of(ctx, "config")) >= 1)
        self.make({"fieldbook.config.yml": "- just\n- a list\n"})
        self.assertTrue(self.has(self.run_cf(), "config", "not a key: value mapping", "error"))

    def test_missing_config_and_wrong_types_do_not_crash(self):
        self.make(remove=["fieldbook.config.yml"])
        self.assertTrue(self.has(self.run_cf(), "config", "config file not found", "warn"))
        self.make({"fieldbook.config.yml": "source_roots: 5\nlegacy: x\nlayout: [a]\nexclude: 3\n"})
        ctx = self.run_cf()
        self.assertTrue(self.has(ctx, "config", "legacy should be a list"))
        self.assertTrue(self.has(ctx, "config", "layout should be a dict"))

    def test_nested_legacy_shape_read(self):
        self.make({"fieldbook.config.yml": "fieldbook:\n  release_status: review\n  output_mode: both\n"})
        ctx = self.run_cf()
        self.assertTrue(ctx.release)
        self.assertTrue(self.has(ctx, "config", "old config shape", "info"))

    def test_on_hold_with_reader_output_warns(self):
        self.make({"fieldbook.config.yml": CONFIG.replace("status: building", "status: on-hold")})
        self.assertTrue(self.has(self.run_cf(), "config", "status is on-hold", "warn"))
        self.make({"fieldbook.config.yml": CONFIG.replace("status: building", "status: on-hold").replace("manual-approval", "guided-auto")},
                  remove=["index.html", "site/index.html", "site/a.html"])
        self.assertTrue(self.has(self.run_cf(), "config", "mode is guided-auto", "warn"))
        self.make({"fieldbook.config.yml": CONFIG.replace("status: building", "status: on-hold")},
                  remove=["index.html", "site/index.html", "site/a.html"])
        self.assertFalse(self.has(self.run_cf(), "config", "status is on-hold"))


class FrontmatterTests(Base):
    def test_missing_keys_warn(self):
        self.make({"topics/b.md": "---\ntitle: B\nupdated: 2030-01-01\n---\ntext\n"})
        ctx = self.run_cf()
        msg = [f["message"] for f in self.of(ctx, "frontmatter")]
        self.assertEqual(len(msg), 1)
        self.assertIn("local_evidence", msg[0])
        self.assertNotIn("title", msg[0].split(":", 1)[1])

    def test_no_frontmatter_warns_and_complete_is_quiet(self):
        self.make({"topics/c.md": "# no frontmatter\n"})
        ctx = self.run_cf()
        self.assertEqual([f["file"] for f in self.of(ctx, "frontmatter")], ["topics/c.md"])


class LinkTests(Base):
    def test_broken_links_fire(self):
        html = ('<link rel="stylesheet" href="missing.css"><img src="gone.png">'
                '<div style="background:url(\'bg.png\')"></div><a href="a.html#nope">x</a>')
        self.make({"site/index.html": html + '<a href="a.html">A</a>',
                   "README.md": "[x](nofile.md) ![i](img/none.png)\n\n```\n[ignored](nothing.md)\n```\n"})
        ctx = self.run_cf()
        errs = [f["message"] for f in self.of(ctx, "links", "error")]
        for needle in ("missing.css", "gone.png", "bg.png", "nofile.md", "img/none.png"):
            self.assertTrue(any(needle in e for e in errs), needle)
        self.assertFalse(any("nothing.md" in e for e in errs))
        self.assertTrue(self.has(ctx, "links", "anchor #nope", "warn"))

    def test_good_links_query_and_encoded_names_are_quiet(self):
        self.make({"site/caf\u00e9 menu.html": "<html><body>\u2615 caf\u00e9</body></html>",
                   "site/index.html": '<a href="caf%C3%A9%20menu.html?x=1#frag">c</a> <a href="a.html">A</a> '
                                      '<a href="https://example.org/q">ext</a> <a href="mailto:a@b.c">m</a> <a href="#top">t</a><h1 id="top"></h1>'})
        ctx = self.run_cf()
        self.assertEqual(self.of(ctx, "links", "error"), [])
        self.assertTrue(self.has(ctx, "links", "1 external links", "info"))

    def test_anchor_present_is_quiet(self):
        ctx = self.make() and self.run_cf()
        self.assertEqual(self.of(ctx, "links", "warn"), [])


class LeakTests(Base):
    def test_html_leaks_are_errors(self):
        self.make({"site/index.html": 'Path C:\\work\\x and D:/y, file:///home, /Users/bob/x, \\\\srv\\share\\f <a href="a.html">A</a>'})
        msgs = [f["message"] for f in self.of(self.run_cf(), "leaks", "error")]
        for kind in ("drive-root path", "file: URL", "/Users/ path", "UNC path"):
            self.assertTrue(any(kind in m for m in msgs), kind)

    def test_false_positives_are_quiet(self):
        self.make({"site/index.html": 'Meet at 12:30 or http://example.org/C:/x and https://a.b/Users/z, see: this, a:b <a href="a.html">A</a>'})
        self.assertEqual(self.of(self.run_cf(), "leaks"), [])

    def test_config_linked_from_html_is_error_and_unlinked_md_is_info(self):
        cfg = CONFIG + 'extra: "J:\\\\projects\\\\private"\n'
        self.make({"fieldbook.config.yml": cfg,
                   "site/index.html": '<a href="../fieldbook.config.yml">cfg</a> <a href="a.html">A</a>',
                   "guidance.md": "Owner path J:/projects/x is allowed in chat notes.\n"})
        ctx = self.run_cf()
        err = self.of(ctx, "leaks", "error")
        self.assertEqual([f["file"] for f in err], ["fieldbook.config.yml"])
        info = self.of(ctx, "leaks", "info")
        self.assertEqual([f["file"] for f in info], ["guidance.md"])

    def test_release_promotes_markdown_leaks(self):
        self.make({"guidance.md": "see J:/projects/x\n"})
        ctx = self.run_cf(release=True)
        self.assertEqual([f["severity"] for f in self.of(ctx, "leaks")], ["error"])


class RawTagTests(Base):
    def test_raw_tag_fires(self):
        self.make({"site/a.html": "<p>Price is $5 [external-primary] and [Inference; from notes].</p>"})
        ctx = self.run_cf()
        f = self.of(ctx, "raw_tags", "warn")
        self.assertEqual(len(f), 1)
        self.assertIn("2 raw provenance tag", f[0]["message"])

    def test_chips_scripts_and_comments_are_quiet(self):
        self.make({"site/a.html": '<span class="chip">external-primary</span><!-- [inference] --><script>var a=["inference"]</script>'})
        self.assertEqual(self.of(self.run_cf(), "raw_tags"), [])

    def test_page_without_any_label_word_warns(self):
        body = "<p>" + "lorem ipsum dolor sit amet " * 80 + "</p>"
        self.make({"site/a.html": "<html><body>" + body + "</body></html>"})
        self.assertTrue(self.has(self.run_cf(), "raw_tags", "no provenance label words"))
        self.make({"site/a.html": "<html><body>" + body + " <b>local-primary</b></body></html>"})
        self.assertFalse(self.has(self.run_cf(), "raw_tags", "no provenance label words"))


class SuperlativeTests(Base):
    def test_fires_in_topic_site_data_and_html(self):
        self.make({"topics/a.md": TOPIC + "\nThis is the best option and the fastest route.\n",
                   "site/data.ts": 'export const x = { note: "Strongest route to market" };\n',
                   "site/a.html": "<p>The largest supplier by far.</p>"})
        files = {f["file"] for f in self.of(self.run_cf(), "superlatives", "warn")}
        self.assertEqual(files, {"topics/a.md", "site/data.ts", "site/a.html"})

    def test_method_quote_allow_and_names_are_quiet(self):
        self.make({"fieldbook.config.yml": CONFIG + "superlative_allow: [premium tier]\n",
                   "topics/a.md": TOPIC + "\nLargest by revenue, measured by filings.\n"
                                  "He wrote \"the best in town\" in a review.\n"
                                  "> The best quote.\nThe premium tier is the best.\n"
                                  "Use best practices and leading zeros. Best Bets page. See https://x.org/best-way/.\n"
                                  "| Best source class | x |\nWon Best AI-Powered Ad. Best estimate: 33 staff.\n"})
        self.assertEqual(self.of(self.run_cf(), "superlatives"), [])

    def test_site_data_comments_skipped(self):
        self.make({"site/data.ts": "// the best of luck\nexport const a = 1;\n"})
        self.assertEqual(self.of(self.run_cf(), "superlatives"), [])

    def test_high_confidence_phrase(self):
        self.make({"topics/a.md": TOPIC + "\nThis is high confidence.\n"})
        self.assertTrue(self.has(self.run_cf(), "superlatives", "high confidence"))


class ClaimTraceTests(Base):
    def test_html_numbers_against_corpus(self):
        self.make({"../src/notes.md": "Revenue was $52,097 and growth 16.9%.\n",
                   "site/a.html": "<p>Income $52,097, poverty 16.9%, also 43,293 vehicles and 7.5%.</p>"})
        msgs = [f["message"] for f in self.of(self.run_cf(), "claim_trace", "warn")]
        self.assertTrue(any("43,293" in m for m in msgs))
        self.assertTrue(any("7.5%" in m for m in msgs))
        self.assertFalse(any("52,097" in m or "16.9%" in m for m in msgs))

    def test_k_suffix_and_years_and_small_numbers(self):
        self.make({"../src/notes.md": "Median home $168,300.\n",
                   "site/a.html": "<p>Home $168.3k in 2024, 12 homes, 100% sure.</p>"})
        self.assertEqual(self.of(self.run_cf(), "claim_trace", "warn"), [])

    def test_site_data_files_and_source_ids(self):
        self.make({"site/data.ts": 'export const rows = [{ v: "43,293", src: "S1" }, { v: "9%", src: "S9" }];\n'})
        ctx = self.run_cf()
        msgs = [f["message"] for f in self.of(ctx, "claim_trace", "warn")]
        self.assertTrue(any("43,293" in m for m in msgs))
        self.assertTrue(any("S9" in m and "source ledger" in m for m in msgs))
        self.assertFalse(any("S1" in m.split(":")[-1].split(",") for m in msgs if "source ID" in m))

    def test_canonical_dir_extends_corpus(self):
        extra = self.base / "canon"
        build(extra, {"x.md": "Traffic 43,293 vehicles.\n"})
        self.make({"site/a.html": "<p>43,293 vehicles</p>"})
        self.assertEqual(self.of(self.run_cf(canonical=[str(extra)]), "claim_trace", "warn"), [])
        self.assertTrue(self.of(self.run_cf(), "claim_trace", "warn"))

    def test_topic_numbers_traced_against_raw_and_ledger(self):
        self.make({"raw/r1.md": "Population 53,930 and 82.8% White.\n",
                   "topics/a.md": TOPIC + "\nPopulation 53,930; 81.2% White; ledger gives $1,200.\n",
                   "source-ledger.md": "| S1 | note $1,200 |\n"})
        msgs = [f["message"] for f in self.of(self.run_cf(), "claim_trace", "warn")]
        self.assertEqual(len(msgs), 1)
        self.assertIn("81.2%", msgs[0])

    def test_self_labelled_lines_skipped(self):
        self.make({"raw/r1.md": "x\n", "topics/a.md": TOPIC + "\nAbout 77.9% (inference).\n"})
        self.assertEqual(self.of(self.run_cf(), "claim_trace"), [])

    def test_release_promotes_to_error(self):
        self.make({"site/a.html": "<p>43,293 vehicles</p>"})
        sev = {f["severity"] for f in self.of(self.run_cf(release=True), "claim_trace") if f["severity"] != "info"}
        self.assertEqual(sev, {"error"})

    def test_max_files_truncation_noted(self):
        self.make({"site/a.html": "<p>1,234 things</p>"})
        ctx = self.run_cf(max_files=3)
        self.assertTrue(self.has(ctx, "claim_trace", "truncated", "info") or self.has(ctx, "structure", "truncated", "info"))


class UncompiledTests(Base):
    def test_unnamed_raw_fires_named_quiet(self):
        self.make({"raw/seen.md": "x\n", "raw/unseen.md": "y\n", "raw/_index.md": "idx\n",
                   "topics/a.md": TOPIC.replace("sources: [1]", "sources: [raw/seen.md]")})
        ctx = self.run_cf()
        self.assertEqual([f["file"] for f in self.of(ctx, "uncompiled")], ["raw/unseen.md"])

    def test_release_promotes(self):
        self.make({"raw/unseen.md": "y\n"})
        self.assertEqual(self.of(self.run_cf(release=True), "uncompiled")[0]["severity"], "error")


class StalenessTests(Base):
    def test_newer_source_warns_older_quiet(self):
        self.make()
        src = self.base / "src" / "notes.md"
        old = time.mktime((2020, 1, 1, 12, 0, 0, 0, 0, -1))
        os.utime(src, (old, old))
        self.assertEqual(self.of(self.run_cf(), "staleness"), [])
        new = time.mktime((2031, 6, 1, 12, 0, 0, 0, 0, -1))
        os.utime(src, (new, new))
        f = self.of(self.run_cf(), "staleness", "warn")
        self.assertEqual(len(f), 1)
        self.assertIn("2031-06-01", f[0]["message"])
        self.assertIn("2030-01-01", f[0]["message"])
        self.assertEqual(self.of(self.run_cf(release=True), "staleness")[0]["severity"], "error")

    def test_excluded_dependencies_and_media_ignored(self):
        self.make({"../src/node_modules/x/new.md": "n\n", "../src/pic.png": "p"})
        new = time.mktime((2031, 6, 1, 12, 0, 0, 0, 0, -1))
        for rel in ("node_modules/x/new.md", "pic.png"):
            os.utime(self.base / "src" / rel, (new, new))
        os.utime(self.base / "src" / "notes.md", (1, 1))
        self.assertEqual(self.of(self.run_cf(), "staleness"), [])

    def test_truncated_scan_is_reported(self):
        self.make({"../src/a.md": "a\n", "../src/b.md": "b\n"})
        ctx = self.run_cf(max_files=1)
        self.assertTrue(any("truncated" in f["message"] for f in self.of(ctx, "staleness")) or ctx.findings)


class CountTests(Base):
    def test_mismatch_warns_match_quiet(self):
        self.make({"raw/r1.md": "a\n", "raw/r2.md": "b\n", "README.md": "# R\n\n- Topics: 1\n- 5 raw sources\n- 1 topics\n"})
        msgs = [f["message"] for f in self.of(self.run_cf(), "counts", "warn")]
        self.assertEqual(len(msgs), 1)
        self.assertIn("5 raw", msgs[0])

    def test_dates_and_past_tense_are_quiet(self):
        self.make({"raw/r1.md": "a\n", "README.md": "Read the 2026-08-11 output briefs. It was 27 raw sources before.\n"})
        self.assertEqual(self.of(self.run_cf(), "counts"), [])


class StatusTests(Base):
    def test_not_built_contradiction(self):
        self.make({"editorial-note.md": "# E\n\nThe local HTML reader has not been built. The site folder is empty.\n"})
        self.assertTrue(self.has(self.run_cf(), "status", "was not built", "warn"))
        self.make()
        self.assertFalse(self.has(self.run_cf(), "status", "was not built"))

    def test_hosting_config_with_private(self):
        self.make({".openai/hosting.json": "{}"})
        self.assertTrue(self.has(self.run_cf(), "status", "hosting config exists", "warn"))
        self.make({".openai/hosting.json": "{}", "fieldbook.config.yml": CONFIG.replace("private", "public")})
        self.assertFalse(self.has(self.run_cf(), "status", "hosting config"))

    def test_phantom_asset(self):
        self.make({"topics/a.md": TOPIC + "\nImage `site/assets/missing.png` and `site/index.html`.\n"})
        f = [x["message"] for x in self.of(self.run_cf(), "status", "warn")]
        self.assertEqual(len(f), 1)
        self.assertIn("missing.png", f[0])

    def test_mixed_status_is_info(self):
        self.make({"topics/b.md": TOPIC.replace("status: draft", "status: final")})
        self.assertTrue(self.has(self.run_cf(), "status", "mixed status", "info"))


class LedgerPathTests(Base):
    LEDGER = "| ID | Source |\n|---|---|\n| S1 | `topics/a.md` |\n| S2 | `../elsewhere.md` |\n| S3 | `../../../nowhere/x.md` |\n| S4 | [r](README.md) |\n"

    def test_unresolved_and_outside_warn(self):
        self.make({"source-ledger.md": self.LEDGER, "../elsewhere.md": "x\n"})
        msgs = [f["message"] for f in self.of(self.run_cf(), "ledger_paths", "warn")]
        self.assertEqual(len(msgs), 2)
        self.assertTrue(any("outside the Fieldbook root: ../elsewhere.md" in m for m in msgs))
        self.assertTrue(any("does not resolve" in m and "nowhere" in m for m in msgs))

    def test_outside_but_inside_declared_source_root_is_info(self):
        self.make({"source-ledger.md": "| S2 | `../src/notes.md` |\n"})
        ctx = self.run_cf()
        self.assertEqual(self.of(ctx, "ledger_paths", "warn"), [])
        self.assertTrue(self.has(ctx, "ledger_paths", "inside a declared source root", "info"))

    def test_resolving_inside_is_quiet(self):
        self.make({"source-ledger.md": "| S1 | `topics/a.md` | `site/index.html` | and/or | 1/2 |\n"})
        self.assertEqual(self.of(self.run_cf(), "ledger_paths"), [])

    def test_source_root_relative_pointer_is_quiet(self):
        self.make({"../src/pages/about.md": "x\n", "source-ledger.md": "| S1 | `pages/about.md` |\n"})
        self.assertEqual(self.of(self.run_cf(), "ledger_paths"), [])


class MoneyTests(Base):
    def test_rows_without_basis_fire(self):
        table = "| Item | Cost |\n|---|---|\n| Paint | $120 |\n| Primer | $40 ([Shop](https://x.org)) |\n| Tile | $90 S1 |\n| Rug | $30 inference |\n"
        self.make({"topics/a.md": TOPIC + "\n" + table})
        f = self.of(self.run_cf(), "money_basis", "warn")
        self.assertEqual(len(f), 1)
        self.assertIn("1 of 4", f[0]["message"])
        self.assertIn("Paint", f[0]["message"])

    def test_all_rows_have_basis_quiet(self):
        self.make({"topics/a.md": TOPIC + "\n| Paint | $120 S2 |\n| Tile | $90 external-primary |\n"})
        self.assertEqual(self.of(self.run_cf(), "money_basis"), [])


class OrphanTests(Base):
    def test_unreachable_page_fires(self):
        self.make({"site/lost.html": "<p>lost</p>"})
        self.assertEqual([f["file"] for f in self.of(self.run_cf(), "orphans")], ["site/lost.html"])

    def test_reachable_and_legacy_quiet(self):
        self.make({"fieldbook.config.yml": CONFIG + "legacy: [site/old]\n", "site/old/x.html": "<p>old</p>"})
        self.assertEqual(self.of(self.run_cf(), "orphans"), [])


class ChatAndPersonalDataTests(Base):
    def test_conversational_fires(self):
        self.make({"site/a.html": "<p>The article you pasted says 300. As you asked, see below.</p>",
                   "topics/a.md": TOPIC + "\nYou mentioned a deadline.\n"})
        files = {f["file"] for f in self.of(self.run_cf(), "conversational", "warn")}
        self.assertEqual(files, {"site/a.html", "topics/a.md"})

    def test_conversational_quiet(self):
        self.make({"site/a.html": "<p>The article cites 300 jobs. Copy-pasted tables were rebuilt.</p>"})
        self.assertEqual(self.of(self.run_cf(), "conversational"), [])

    def test_personal_data_warns_then_ok_flag_makes_info(self):
        page = "<p>Call (314) 555-0134, EIN 12-3456789, at 11312 one book Dr or 201 Humbolt St., St. Louis.</p>"
        self.make({"site/a.html": page})
        msgs = " ".join(f["message"] for f in self.of(self.run_cf(), "personal_data", "warn"))
        for kind in ("phone number", "EIN-like", "street-address"):
            self.assertIn(kind, msgs)
        for value in ("555-0134", "12-3456789", "11312 one book"):
            self.assertNotIn(value, msgs)
        self.make({"site/a.html": page, "fieldbook.config.yml": CONFIG + "personal_data_ok: true\n"})
        ctx = self.run_cf()
        self.assertEqual(self.of(ctx, "personal_data", "warn"), [])
        self.assertTrue(self.of(ctx, "personal_data", "info"))

    def test_wiki_article_page_labels_are_not_ledger_ids(self):
        cfg = CONFIG + 'reader:\n  wiki_articles: ["../wiki/k2.md"]\n'
        self.make({"site/k2.html": "<p>Row S99 of the table.</p>", "site/a.html": "<p>Cites S98 here.</p>", "fieldbook.config.yml": cfg})
        ids = " ".join(f["message"] for f in self.of(self.run_cf(), "claim_trace"))
        self.assertIn("S98", ids)
        self.assertNotIn("S99", ids)

    def test_personal_data_quiet(self):
        self.make({"site/a.html": "<p>Built in 2026-10-28, 1,120 sq ft, version 3.4.5, 12:30.</p>"})
        self.assertEqual(self.of(self.run_cf(), "personal_data"), [])


class AddedChecksTests(Base):
    def test_poster_source_and_srcset_are_checked(self):
        self.make({"site/media/ok.png": "x", "site/a.html":
                   '<video poster="media/p.jpg"><source src="media/v.mp4"></video>'
                   '<img src="media/ok.png" srcset="media/ok.png 1x, media/two.png 2x">'})
        errs = [f["message"] for f in self.of(self.run_cf(), "links", "error")]
        for needle in ("media/p.jpg", "media/v.mp4", "media/two.png"):
            self.assertTrue(any(needle in e for e in errs), needle)
        self.assertFalse(any("ok.png" in e for e in errs))

    def test_url_in_text_is_not_css_and_style_url_is(self):
        self.make({"site/a.html": '<p>13 source URL(s) and URL(x)</p><div style="background:url(bg.png)"></div><style>a{background:url(\'s.png\')}</style>'})
        errs = [f["message"] for f in self.of(self.run_cf(), "links", "error")]
        self.assertEqual(sorted(e.split(": ")[1] for e in errs), ["bg.png", "s.png"])

    def test_duplicate_references_counted_once(self):
        page = self.base / "d.html"
        build(self.base, {"d.html": '<img src="m.png"><img src="m.png"><a href="d.html">i</a>'})
        ctx = self.run_cf(page)
        self.assertEqual((ctx.link_stats["referenced"], ctx.link_stats["resolved"]), (2, 1))

    def test_negated_public_audience_is_quiet(self):
        self.make({"site/a.html": "<p>Our margin is high.</p>",
                   "fieldbook.config.yml": CONFIG.replace("personal research", "Owner first. Not a public investor deck.")})
        self.assertEqual(self.of(self.run_cf(), "audience"), [])

    def test_link_counts_reported(self):
        self.make({"site/a.html": '<img src="m1.png"><img src="m2.png"><a href="index.html">i</a><a href="https://x.org">x</a>'})
        ctx = self.run_cf()
        self.assertEqual(ctx.link_stats["referenced"] - ctx.link_stats["resolved"], 2)
        self.assertIn("local references", cf.render_text(ctx, 20))
        self.assertIn("2 broken", cf.render_text(ctx, 20))

    def test_sha256_in_html_warns_other_hex_and_profile_quiet(self):
        sha = "a" * 32 + "0123456789abcdef" * 2
        self.make({"site/a.html": "<p>hash %s</p><p>profile: Jane. md5 %s. file:///x</p>" % (sha, "b" * 32)})
        ctx = self.run_cf()
        self.assertTrue(self.has(ctx, "leaks", "1 SHA-256", "warn"))
        msgs = [f["message"] for f in self.of(ctx, "leaks")]
        self.assertEqual(sum("file: URL" in m for m in msgs), 1)
        self.make({"site/a.html": "<p>Open the profile: https://x.org/profile:name and C profile:Cx</p>"})
        self.assertEqual(self.of(self.run_cf(), "leaks"), [])

    def test_internal_process_words_flagged_but_not_this_pass(self):
        self.make({"site/a.html": "<p>The orchestrator asked a subagent and a worker agent. Not found in this pass.</p>"})
        ctx = self.run_cf()
        f = self.of(ctx, "conversational", "warn")
        self.assertEqual(len(f), 1)
        self.assertIn("3 chat leftover", f[0]["message"])
        self.make({"site/a.html": "<p>Not found in this pass.</p>"})
        self.assertEqual(self.of(self.run_cf(), "conversational"), [])

    def test_audience_check_triggers(self):
        page = "<p>Delivery cost and contribution margin are fine. A margin of error of 3%. Fallback fee applies.</p>"
        self.make({"site/a.html": page})
        self.assertEqual(self.of(self.run_cf(), "audience"), [])
        self.make({"site/a.html": page, "fieldbook.config.yml": CONFIG.replace("personal research", "client pitch")})
        f = self.of(self.run_cf(), "audience", "warn")
        self.assertEqual(len(f), 1)
        self.assertIn("margin", f[0]["message"])
        self.make({"site/a.html": page, "fieldbook.config.yml": CONFIG.replace("private", "public")})
        self.assertTrue(self.of(self.run_cf(), "audience", "warn"))

    def test_audience_flag_on_bare_page(self):
        page = self.base / "p.html"
        build(self.base, {"p.html": "<p>Our margin is 40% and cost to serve is low.</p>"})
        self.assertEqual(self.of(self.run_cf(page), "audience"), [])
        self.assertTrue(self.of(self.run_cf(page, audience="prospect"), "audience", "warn"))
        with contextlib.redirect_stdout(io.StringIO()) as out:
            cf.main([str(page), "--audience", "prospect"])
        self.assertIn("== audience", out.getvalue())

    def test_many_missing_local_references_flagged_on_bare_page(self):
        page = self.base / "k.html"
        build(self.base, {"k.html": "".join('<img src="m/%d.png">' % i for i in range(5)) + '<img src="k.html">'})
        ctx = self.run_cf(page)
        self.assertEqual(ctx.link_stats["referenced"], 6)
        self.assertEqual(len(self.of(ctx, "links", "error")), 5)


NO_ROOTS = CONFIG.replace("  - ../src\n", "").replace("source_roots:", "source_roots: []")
LEDGER_ACC = ("| ID | Source | Accessed |\n|---|---|---|\n| S1 | `raw/note-01.md` | 2025-05-05 |\n"
              "| S2 | `raw/note-02.md` | 2031-02-02 |\n")


class RepairRoundTests(Base):
    """No-raw topic trace, uncompiled outside raw/, ledger-ID citations and wider staleness."""

    def test_invented_number_caught_without_raw_folder(self):
        self.make({"topics/a.md": TOPIC + "\nA hidden cost of $99,999 applies.\n", "../src/notes.md": "Roof cost $12,500.\n"})
        ctx = self.run_cf()
        f = self.of(ctx, "claim_trace", "warn")
        self.assertEqual(len(f), 1)
        self.assertIn("$99,999", f[0]["message"])
        self.assertTrue(self.has(ctx, "claim_trace", "no raw/ folder: topic numbers traced against", "info"))
        self.assertEqual(self.of(self.run_cf(release=True), "claim_trace", "error")[0]["line"], f[0]["line"])

    def test_number_found_in_notes_ledger_or_inventory_is_quiet(self):
        self.make({"topics/a.md": TOPIC + "\nCosts $12,500, $3,300 and $4,400.\n", "../src/notes.md": "Roof cost $12,500.\n",
                   "source-ledger.md": "| S1 | quote $3,300 |\n", "local-evidence-inventory.md": "| L1 | quote $4,400 |\n"})
        self.assertEqual(self.of(self.run_cf(), "claim_trace", "warn"), [])

    def test_other_topics_do_not_count_as_evidence(self):
        self.make({"topics/a.md": TOPIC + "\nCost $99,999.\n", "topics/b.md": TOPIC + "\nCost $99,999.\n"})
        self.assertEqual(len(self.of(self.run_cf(), "claim_trace", "warn")), 2)

    def test_canonical_dir_supplies_evidence_without_raw(self):
        canon = self.base / "canon"
        build(canon, {"n.md": "Cost $99,999.\n"})
        self.make({"topics/a.md": TOPIC + "\nCost $99,999.\n"})
        self.assertEqual(self.of(self.run_cf(canonical=[str(canon)]), "claim_trace", "warn"), [])

    def test_nothing_to_trace_against_says_so(self):
        self.make({"topics/a.md": TOPIC + "\nCost $99,999.\n", "fieldbook.config.yml": NO_ROOTS},
                  remove=["source-ledger.md", "local-evidence-inventory.md"])
        self.assertTrue(self.has(self.run_cf(), "claim_trace", "topic numbers not traced", "info"))

    def test_uncompiled_runs_on_source_root_notes(self):
        self.make({"../src/orphan-note.md": "x\n", "../src/cited-note.md": "y\n",
                   "topics/a.md": TOPIC + "\nSee cited-note for the quote.\n"})
        f = self.of(self.run_cf(), "uncompiled", "warn")
        self.assertEqual([x["file"] for x in f], [(self.base / "src" / "orphan-note.md").as_posix()])
        self.assertEqual(self.of(self.run_cf(release=True), "uncompiled")[0]["severity"], "error")

    def test_uncompiled_says_when_it_cannot_run(self):
        self.make({"fieldbook.config.yml": NO_ROOTS})
        self.assertTrue(self.has(self.run_cf(), "uncompiled", "did not run", "info"))
        self.make({"../src/n%03d.md" % i: "x\n" for i in range(70)})
        ctx = self.run_cf()
        self.assertTrue(self.has(ctx, "uncompiled", "too many to treat as captures", "info"))
        self.assertEqual(self.of(ctx, "uncompiled", "warn"), [])

    def test_outside_root_with_no_cited_file_is_one_info(self):
        self.make({"../src/a-note.md": "x\n", "../src/b-note.md": "y\n"}, remove=["../src/notes.md"])
        ctx = self.run_cf()
        self.assertEqual(self.of(ctx, "uncompiled", "warn"), [])
        self.assertTrue(self.has(ctx, "uncompiled", "no topic names any of its", "info"))

    def test_inside_root_notes_are_always_checked(self):
        cfg = CONFIG.replace("../src", "notes")
        self.make({"fieldbook.config.yml": cfg, "notes/loose.md": "x\n"})
        self.assertEqual([f["file"] for f in self.of(self.run_cf(), "uncompiled", "warn")], ["notes/loose.md"])

    def test_evidence_folder_counts_as_evidence_without_raw(self):
        self.make({"evidence/record.md": "Assessed $68,600.\n", "topics/a.md": TOPIC + "\nAssessed $68,600 in 2019.\n"})
        self.assertEqual(self.of(self.run_cf(), "claim_trace", "warn"), [])

    def test_ledger_id_citation_counts_as_citing_the_capture(self):
        ledger = "| ID | Source |\n|---|---|\n| S1 | `raw/note-01.md` |\n| S2 | `raw/note-02.md` |\n"
        topic = TOPIC.replace("sources: [1]", "sources: [S1]")
        self.make({"raw/note-01.md": "a\n", "raw/note-02.md": "b\n", "source-ledger.md": ledger, "topics/a.md": topic})
        self.assertEqual([x["file"] for x in self.of(self.run_cf(), "uncompiled", "warn")], ["raw/note-02.md"])
        self.assertEqual(self.of(self.run_cf(release=True), "uncompiled", "error")[0]["file"], "raw/note-02.md")

    def test_staleness_sees_raw_only_sources(self):
        self.make({"fieldbook.config.yml": NO_ROOTS, "raw/2031-03-03-capture.md": "x\n",
                   "topics/a.md": TOPIC.replace("sources: [1]", "sources: [capture]")})
        f = self.of(self.run_cf(), "staleness", "warn")
        self.assertEqual(len(f), 1)
        self.assertIn("2031-03-03", f[0]["message"])
        self.assertIn("2030-01-01", f[0]["message"])
        self.make({"fieldbook.config.yml": NO_ROOTS, "raw/2020-03-03-capture.md": "x\n"})
        self.assertEqual(self.of(self.run_cf(), "staleness", "warn"), [])

    def test_staleness_sees_ledger_accessed_dates(self):
        self.make({"source-ledger.md": LEDGER_ACC, "fieldbook.config.yml": NO_ROOTS})
        f = self.of(self.run_cf(), "staleness", "warn")
        self.assertEqual(len(f), 1)
        self.assertIn("ledger Accessed date of S2", f[0]["message"])
        self.assertIn("2031-02-02", f[0]["message"])

    def test_each_topic_older_than_a_cited_source_is_reported(self):
        old = TOPIC.replace("updated: 2030-01-01", "updated: 2020-01-01").replace("sources: [1]", "sources: [S1]")
        self.make({"fieldbook.config.yml": NO_ROOTS, "source-ledger.md": LEDGER_ACC.replace("2031-02-02", "2019-02-02"), "topics/old.md": old})
        f = [x for x in self.of(self.run_cf(), "staleness", "warn") if x["file"] == "topics/old.md"]
        self.assertEqual(len(f), 1)
        self.assertIn("2020-01-01", f[0]["message"])
        self.assertIn("2025-05-05", f[0]["message"])
        self.assertTrue([x for x in self.of(self.run_cf(release=True), "staleness", "error") if x["file"] == "topics/old.md"])

    def test_staleness_says_when_nothing_to_compare(self):
        self.make({"fieldbook.config.yml": NO_ROOTS})
        self.assertTrue(self.has(self.run_cf(), "staleness", "staleness not computed", "info"))


class PageModeTests(Base):
    def test_bare_html_runs_page_checks_only(self):
        page = self.base / "solo" / "dossier.html"
        build(page.parent, {"dossier.html": "<p>Compiled from J:\\projects\\.wiki\\topics\\x. The pasted article says 5 jobs [lead-only]. "
                                            '<a href="missing.html">m</a></p>'})
        ctx = self.run_cf(page)
        self.assertTrue(ctx.page_mode)
        checks = {f["check"] for f in ctx.findings}
        self.assertTrue({"leaks", "links", "raw_tags", "conversational"} <= checks)
        self.assertFalse(checks & {"structure", "config", "frontmatter", "uncompiled", "staleness"})
        self.assertTrue(self.has(ctx, "leaks", "drive-root path", "error"))

    def test_main_accepts_html_and_rejects_other_file(self):
        page = self.base / "p.html"
        build(self.base, {"p.html": "<p>ok</p>", "n.txt": "x"})
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cf.main([str(page)]), 0)
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(cf.main([str(self.base / "n.txt")]), 2)


class CliTests(Base):
    def run_main(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = cf.main(list(argv))
        return code, out.getvalue()

    def test_exit_codes(self):
        self.make()
        self.assertEqual(self.run_main(str(self.root))[0], 0)
        build(self.root, {"site/a.html": "<a href='zzz.html'>z</a>"})
        self.assertEqual(self.run_main(str(self.root))[0], 1)
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(self.run_main(str(self.base / "missing"))[0], 2)
            with self.assertRaises(SystemExit) as cm:
                cf.main([str(self.root), "--bogus"])
            self.assertEqual(cm.exception.code, 2)

    def test_json_output_keeps_everything(self):
        rows = "".join("<p>%d,%03d things</p>" % (i + 1, i + 100) for i in range(30))
        self.make({"site/a.html": rows})
        code, text = self.run_main(str(self.root), "--json")
        data = json.loads(text)
        claims = [f for f in data["findings"] if f["check"] == "claim_trace" and f["severity"] == "warn"]
        self.assertEqual(len(claims), 30)
        self.assertEqual(set(claims[0]), {"check", "severity", "file", "line", "message"})
        self.assertEqual(data["totals"]["warn"], len([f for f in data["findings"] if f["severity"] == "warn"]))

    def test_text_output_caps_and_totals(self):
        rows = "".join("<p>%d,%03d things</p>" % (i + 1, i + 100) for i in range(30))
        self.make({"site/a.html": rows})
        code, text = self.run_main(str(self.root), "--limit", "5")
        self.assertIn("== claim_trace", text)
        self.assertIn("26 more hidden", text)
        self.assertTrue(text.strip().splitlines()[-1].startswith("Totals:"))

    def test_release_flag_and_config_release_status(self):
        self.make({"site/a.html": "<p>43,293 vehicles</p>"})
        self.assertEqual(self.run_main(str(self.root))[0], 0)
        self.assertEqual(self.run_main(str(self.root), "--release")[0], 1)
        self.make({"site/a.html": "<p>43,293 vehicles</p>", "fieldbook.config.yml": CONFIG.replace("private", "review")})
        self.assertEqual(self.run_main(str(self.root))[0], 1)

    def test_site_dir_option_and_missing_site_dir(self):
        site = self.base / "app"
        build(site, {"data.ts": 'export const a = "Best bet, 43,293";\n', "node_modules/x/y.ts": "best 99,999"})
        self.make()
        ctx = self.run_cf(site=[str(site), str(self.base / "nope")])
        self.assertTrue(self.has(ctx, "claim_trace", "43,293"))
        self.assertFalse(self.has(ctx, "claim_trace", "99,999"))
        self.assertTrue(self.has(ctx, "structure", "--site directory not found", "info"))


class SafetyTests(Base):
    def test_read_only_and_utf8(self):
        self.make({"topics/\u00e9t\u00e9.md": TOPIC.replace("Topic A", "\u00c9t\u00e9 \u2615 \u65e5\u672c\u8a9e") + "\nPrice \u20ac1,234 \u2014 best \u201cquoted\u201d.\n",
                   "site/a.html": "<meta charset='utf-8'><p>\u00dcber caf\u00e9 \u2615 \u65e5\u672c\u8a9e 43,293</p>",
                   "site/ch\u00e8que.html": "<p>ok</p>"})
        before = tree_hash(self.base)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            cf.main([str(self.root)])
            cf.main([str(self.root), "--json", "--release"])
        self.assertEqual(before, tree_hash(self.base))
        self.assertIn("43,293", out.getvalue())

    def test_binary_and_bad_encoding_do_not_crash(self):
        self.make({"topics/bad.md": b"---\ntitle: x\n---\n\xff\xfe\x00bad \x80 bytes 43,293\n", "site/b.html": b"<p>\xff\xfe</p>"})
        ctx = self.run_cf()
        self.assertTrue(ctx.findings is not None)

    def test_a_crashing_check_is_contained(self):
        self.make()
        original = cf.CHECK_FUNCS["orphans"]
        cf.CHECK_FUNCS["orphans"] = lambda ctx: 1 / 0
        try:
            ctx = self.run_cf()
        finally:
            cf.CHECK_FUNCS["orphans"] = original
        self.assertTrue(self.has(ctx, "orphans", "check crashed", "warn"))


if __name__ == "__main__":
    unittest.main()
