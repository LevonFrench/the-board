"""Tests for scripts/build_reader.py. Temp fixtures only; nothing outside a temp dir is written."""
import contextlib
import hashlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_reader as br  # noqa: E402


def md(text, **kw):
    return br.Markdown(**kw).render(text)


def run(*argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = br.run([str(a) for a in argv])
    return code, out.getvalue()


def write(root, rel, text, binary=False):
    f = Path(root) / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    if binary:
        f.write_bytes(text)
    else:
        f.write_text(text, encoding="utf-8", newline="\n")
    return f


def make_fieldbook(root, **extra):
    cfg = 'subject: "Test Town \u2014 market Fieldbook"\nrelease_status: private\n' + extra.pop("cfg", "")
    write(root, "fieldbook.config.yml", cfg)
    write(root, "README.md", "# Test Town Fieldbook: start here\n\nRead [alpha](topics/alpha.md) first.\n"
                             "See the [ledger](source-ledger.md#sources).\n")
    write(root, "topics/alpha.md", "---\ntitle: Alpha topic\nstatus: draft\nupdated: 2026-10-01\n"
                                   "sources: 12\nconfidence: Medium\n---\n\n# Alpha topic\n\n"
                                   "**Bottom line.** Alpha is fine [inference].\n\n## Details\n\nText.\n")
    write(root, "topics/beta.md", "---\ntitle: Beta topic\nupdated: 2026-10-05\nsources: [S1, S2, S3]\n---\n\n"
                                  "# Beta topic\n\nBeta body.\n")
    write(root, "source-ledger.md", "# Source ledger\n\n## Sources\n\nA list.\n")
    write(root, "gap-register.md", "# Gap register\n\n| ID | Question | Status |\n|---|---|---|\n"
                                   "| G-1 | Is it zoned? | open |\n")
    for rel, text in extra.items():
        write(root, rel.replace("__", "/"), text)


class Tmp(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.root = Path(self._t.name) / "fb"
        self.root.mkdir()
        self.addCleanup(self._t.cleanup)

    def page(self, rel):
        return (self.root / rel).read_text(encoding="utf-8")


class RendererTests(unittest.TestCase):
    def test_headings_and_github_slugs(self):
        r = br.Markdown()
        out = r.render("# Hello, World!\n\n## Q&A: 50% off\n\n## Q&A: 50% off\n\n### caf\u00e9 \u2014 menu")
        self.assertIn('<h1 id="hello-world">', out)
        self.assertIn('id="qa-50-off"', out)
        self.assertIn('id="qa-50-off-1"', out)
        self.assertIn('id="caf\u00e9--menu"', out)

    def test_setext_and_paragraph_breaks(self):
        out = md("Title\n=====\n\nline one\nline two  \nline three\\\nfour")
        self.assertIn("<h1", out)
        self.assertIn("line one\nline two<br>\nline three<br>\nfour", out)

    def test_inline_styles(self):
        out = md("**bold** and *it* and _it2_ and `co<de>` and ~~gone~~ and a_b_c and 2 * 3 * 4")
        self.assertIn("<strong>bold</strong>", out)
        self.assertIn("<em>it</em>", out)
        self.assertIn("<em>it2</em>", out)
        self.assertIn("<code>co&lt;de&gt;</code>", out)
        self.assertIn("<del>gone</del>", out)
        self.assertIn("a_b_c", out)
        self.assertIn("2 * 3 * 4", out)

    def test_nested_emphasis(self):
        self.assertIn("<em><strong>x</strong></em>", md("***x***"))
        self.assertIn("<em>a <strong>b</strong></em>", md("*a **b***"))

    def test_links_images_autolinks(self):
        out = md('[site](https://example.com/a_(b) "T") ![alt *x*](pic.png) <https://e.org/x> '
                 'and https://bare.example/path. [rel](a/b.md#c)')
        self.assertIn('<a href="https://example.com/a_(b)" title="T" target="_blank" rel="noopener noreferrer">site</a>', out)
        self.assertIn('<img src="pic.png" alt="alt x">', out)
        self.assertIn('<a href="https://e.org/x" target="_blank" rel="noopener noreferrer">https://e.org/x</a>', out)
        self.assertIn('href="https://bare.example/path"', out)
        self.assertIn('href="a/b.md#c"', out)

    def test_lists_nested_ordered_and_tasks(self):
        out = md("- a\n  - a1\n  - a2\n- b\n\n3. three\n4. four\n   1. sub\n\n- [ ] todo\n- [x] done")
        self.assertIn("<ul>\n<li>a\n<ul>\n<li>a1</li>\n<li>a2</li>\n</ul></li>\n<li>b</li>\n</ul>", out)
        self.assertIn('<ol start="3">', out)
        self.assertIn("<ol>\n<li>sub</li>\n</ol>", out)
        self.assertIn('<li class="task"><input type="checkbox" disabled> todo</li>', out)
        self.assertIn('<input type="checkbox" disabled checked> done', out)

    def test_loose_list_and_lazy_continuation(self):
        out = md("- one\ncontinued\n\n- two")
        self.assertIn("<li><p>one\ncontinued</p></li>", out)

    def test_table_alignment_and_escaped_pipe(self):
        out = md("| L | C | R |\n|:--|:-:|--:|\n| a \\| b | `x` | **3** |\n| only |")
        self.assertIn('<th scope="col" class="al-c">C</th>', out)
        self.assertIn('<th scope="col" class="al-r">R</th>', out)
        self.assertIn("<td>a | b</td>", out)
        self.assertIn('<td class="al-r"><strong>3</strong></td>', out)
        self.assertIn('<td class="al-c"></td>', out)
        self.assertIn('<div class="scroll"', out)

    def test_blockquote_fence_hr(self):
        out = md("> quoted\n> more\n\n```python\nif a < b:\n    pass\n```\n\n---\n\n~~~\nraw\n~~~")
        self.assertIn("<blockquote>\n<p>quoted\nmore</p>\n</blockquote>", out)
        self.assertIn('<pre><code class="language-python">if a &lt; b:\n    pass\n</code></pre>', out)
        self.assertIn("<hr>", out)
        self.assertIn("<pre><code>raw\n</code></pre>", out)

    def test_fence_keeps_markdown_literal(self):
        out = md("```\n# not a heading\n[inference]\n```")
        self.assertNotIn("<h1", out)
        self.assertNotIn("chip", out)

    def test_html_escaped_as_text(self):
        out = md('<script>alert(1)</script>\n\n<div onclick="x">hi</div> <img src=x onerror=y>\n\n<!-- hidden -->\n\nA & B "q"')
        self.assertNotIn("<script", out)
        self.assertNotIn("<div", out)
        self.assertNotIn("<img", out)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", out)
        self.assertIn("A &amp; B &quot;q&quot;", out)
        self.assertNotIn("hidden", out)

    def test_entities_decode_then_escape(self):
        self.assertIn("a &amp; b", md("a &amp; b"))
        self.assertIn("&lt;", md("&lt;"))

    def test_javascript_links_rejected(self):
        for dest in ("javascript:alert(1)", "JavaScript:alert(1)", "java\tscript:alert(1)", "data:text/html,x",
                     "vbscript:x"):
            out = md(f"[click](<{dest}>)")
            self.assertNotIn("href", out, dest)
            self.assertIn("click", out)
        self.assertNotIn("href", md("[x](javascript:alert(1))"))
        self.assertNotIn("<img", md("![x](javascript:alert(1))"))

    def test_chip_with_qualifier(self):
        for src in ("[inference / arithmetic]", "[inference, from the notes]", "[lead-only; sources conflict]",
                    "[arithmetic from sketch dimensions]", "[inference: 1,120 sq ft x rate]"):
            out = md(f"x {src} y")
            self.assertIn('class="chip chip-', out)
            self.assertIn(" chip-long", out)
            self.assertNotIn("[", out, src)
        self.assertIn("[unknownish thing]", md("[unknownish thing]"))
        self.assertIn("[inferences]", md("[inferences]"))
        self.assertIn('<a href="a.md">unknown rooms</a>', md("[unknown rooms](a.md)"))

    def test_chip_vocabulary_and_non_chips(self):
        for label in br.CHIPS:
            out = md(f"A claim [{label}] here.")
            self.assertIn(f'<span class="chip chip-{br.CHIPS[label][0]}">{label}</span>', out)
            self.assertNotIn(f"[{label}]", out)
        out = md("see [Angi] and [x](a.md) and **[inference]** and `[lead-only]` and `[other]`")
        self.assertIn("[Angi]", out)
        self.assertIn("<strong><span class=\"chip chip-warn\">inference</span></strong>", out)
        self.assertIn('chip-weak">lead-only</span>', out)
        self.assertIn("<code>[other]</code>", out)
        self.assertIn('chip-primary">external-primary</span>', md("[External-Primary]"))


class FrontmatterTests(unittest.TestCase):
    def test_split(self):
        meta, body = br.split_frontmatter("---\ntitle: T\nsources: 5\n---\n\n# H\n")
        self.assertEqual(meta["title"], "T")
        self.assertEqual(meta["sources"], 5)
        self.assertEqual(body, "# H\n")
        self.assertEqual(br.split_frontmatter("---\n\nnot frontmatter, no close"), ({}, "---\n\nnot frontmatter, no close"))

    def test_fallback_parser(self):
        text = ('title: "A: B"\nsources: [S1, "S 2"]\nopen_questions:\n  - one\n  - two\nreader:\n  accent: "#112233"\n'
                '  topics: [x, y]\nflag: true\nupdated: 2026-10-01\n')
        got = br.mini_yaml(text)
        self.assertEqual(got["title"], "A: B")
        self.assertEqual(got["sources"], ["S1", "S 2"])
        self.assertEqual(got["open_questions"], ["one", "two"])
        self.assertEqual(got["reader"], {"accent": "#112233", "topics": ["x", "y"]})
        self.assertIs(got["flag"], True)
        self.assertEqual(got["updated"], "2026-10-01")

    def test_build_works_without_pyyaml(self):
        saved = br.yaml
        br.yaml = None
        self.addCleanup(setattr, br, "yaml", saved)
        with tempfile.TemporaryDirectory() as t:
            root = Path(t) / "fb"
            make_fieldbook(root, cfg='reader:\n  title: Plain Title\n  topics: [beta, alpha]\n')
            code, _ = run(root)
            self.assertEqual(code, 0)
            self.assertIn("Plain Title", (root / "site/index.html").read_text(encoding="utf-8"))


class BuildTests(Tmp):
    def test_page_set_and_nav(self):
        make_fieldbook(self.root, local_evidence_inventory="x")
        write(self.root, "refresh-backlog.md", "# Refresh backlog\n")
        write(self.root, "evidence/notes.md", "# Notes\n")
        code, out = run(self.root)
        self.assertEqual(code, 0, out)
        names = sorted(p.name for p in (self.root / "site").iterdir())
        self.assertEqual(names, ["alpha.html", "beta.html", "gap-register.html", "index.html", "notes.html",
                                 "refresh-backlog.html", "source-ledger.html", "styles.css"])
        for n in names:
            if n.endswith(".html"):
                page = self.page("site/" + n)
                for target in ("alpha", "beta", "gap-register", "source-ledger", "refresh-backlog", "notes"):
                    self.assertIn(f'href="{target}.html"', page, (n, target))
                self.assertIn('<meta name="generator" content="fieldbook-build_reader">', page)
                self.assertNotIn("<script", page)
        root = self.page("index.html")
        self.assertIn('http-equiv="refresh" content="0; url=site/index.html"', root)
        self.assertIn('<a href="site/index.html">', root)
        self.assertIn(br.GENERATOR_META, root)

    def test_title_from_subject_and_reader_config(self):
        make_fieldbook(self.root)
        run(self.root)
        self.assertIn("<title>Test Town Fieldbook</title>", self.page("site/index.html"))
        with tempfile.TemporaryDirectory() as t:
            other = Path(t) / "fb"
            make_fieldbook(other, cfg='reader:\n  title: My Reader\n  footer: Custom footer\n  accent: "#336699"\n'
                                      '  topics: [beta, alpha]\n')
            self.assertEqual(run(other)[0], 0)
            index = (other / "site/index.html").read_text(encoding="utf-8")
            self.assertIn("<title>My Reader</title>", index)
            self.assertIn("Custom footer", index)
            self.assertLess(index.index("Beta topic"), index.index("Alpha topic"))
            self.assertIn("#336699", (other / "site/styles.css").read_text(encoding="utf-8"))

    def test_index_orientation_private_and_date(self):
        make_fieldbook(self.root)
        run(self.root)
        index = self.page("site/index.html")
        self.assertIn('<span class="badge">Private</span>', index)
        self.assertIn("Private Fieldbook", index)
        self.assertIn("2026-10-05", index)
        self.assertIn("Test Town", index)
        self.assertIn('id="fb-legend"', index)
        self.assertIn('id="fb-next"', index)
        self.assertIn("G-1", index)
        for label in br.CHIPS:
            self.assertIn(f">{label}</span>", index)
        self.assertIn('name="robots"', index)

    def test_public_fieldbook_not_marked_private(self):
        make_fieldbook(self.root)
        write(self.root, "fieldbook.config.yml", "subject: Open thing\nrelease_status: public\n")
        run(self.root)
        index = self.page("site/index.html")
        self.assertNotIn("Private Fieldbook", index)
        self.assertNotIn('name="robots"', index)

    def test_sources_integer_and_list(self):
        make_fieldbook(self.root)
        run(self.root)
        self.assertIn("<b>12</b> sources", self.page("site/alpha.html"))
        self.assertIn("<b>3</b> sources", self.page("site/beta.html"))
        self.assertNotIn("Sources: 12", self.page("site/alpha.html"))
        self.assertEqual(br.Reader.sources_label(1), "<b>1</b> source")
        self.assertEqual(br.Reader.sources_label("40"), "<b>40</b> sources")
        self.assertEqual(br.Reader.sources_label(None), "")

    def test_meta_box_contents(self):
        make_fieldbook(self.root)
        write(self.root, "topics/alpha.md", "---\ntitle: Alpha\nstatus: ok\nupdated: 2026-10-01\nsources: 2\n"
                                            "confidence: " + "very " * 40 + "high\nopen_questions: [Q one, Q two]\n---\n\n# Alpha\n\nBody\n")
        run(self.root)
        page = self.page("site/alpha.html")
        self.assertIn("<b>Status</b> ok", page)
        self.assertIn("<b>Updated</b> 2026-10-01", page)
        self.assertIn("2 open questions", page)
        self.assertIn("<li>Q one</li>", page)
        self.assertIn("<details><summary><b>Confidence</b>", page)
        self.assertLess(page.index("</h1>"), page.index('class="meta"'))

    def test_page_without_h1_gets_title_and_meta(self):
        make_fieldbook(self.root)
        write(self.root, "topics/beta.md", "---\ntitle: Beta title\nstatus: draft\nsources: 4\n---\n\n## Only h2\n\ntext\n")
        run(self.root)
        page = self.page("site/beta.html")
        self.assertIn("<h1>Beta title</h1>", page)
        self.assertIn("<b>4</b> sources", page)
        self.assertIn('<h2 id="only-h2">', page)

    def test_link_rewriting(self):
        make_fieldbook(self.root)
        write(self.root, "evidence/shot.png", b"\x89PNG fake", binary=True)
        write(self.root, "research_notes/n.md", "# note\n")
        write(self.root, "topics/alpha.md",
              "# Alpha\n\n[b](beta.md) [l](../source-ledger.md#sources) [r](../README.md) [cfg](../fieldbook.config.yml) "
              "[py](x.py) [n](../research_notes/n.md) [out](../../outside.md) [img](../evidence/shot.png) "
              "[miss](../evidence/gone.png) [abs](/etc/passwd) [self](#details)\n\n## Details\n\n"
              "![shot](../evidence/shot.png)\n")
        code, out = run(self.root)
        page = self.page("site/alpha.html")
        self.assertIn('href="beta.html"', page)
        self.assertIn('href="source-ledger.html#sources"', page)
        self.assertIn('href="index.html"', page)
        self.assertIn('href="../evidence/shot.png"', page)
        self.assertIn('src="../evidence/shot.png"', page)
        self.assertIn('href="#details"', page)
        for dead in ("fieldbook.config.yml", "x.py", "research_notes", "outside.md", "gone.png", "/etc/passwd"):
            self.assertNotIn(f'href="{dead}', page)
            self.assertNotIn(dead + '"', page.split("<main")[1])
            self.assertIn(dead.split("/")[-1], out)
        self.assertIn("not a reader file", out)
        self.assertIn("leaves the Fieldbook", out)
        self.assertIn("missing target", out)
        self.assertEqual(code, 0, out)

    def test_broken_anchor_fails_self_check(self):
        make_fieldbook(self.root)
        write(self.root, "topics/alpha.md", "# Alpha\n\n[x](beta.md#nope) [y](#also-nope)\n")
        code, out = run(self.root)
        self.assertEqual(code, 1)
        self.assertIn("missing anchor beta.html#nope", out)
        self.assertIn("missing anchor #also-nope", out)
        self.assertIn("2 broken", out)

    def test_check_outputs_reports_missing_file(self):
        problems, checked = br.check_outputs({"site/a.html": '<a href="gone.html">x</a><img src="../nope.png">'}, self.root)
        self.assertEqual(len(problems), 2)
        self.assertEqual(checked, 2)

    def test_byte_identical_rerun(self):
        make_fieldbook(self.root)
        write(self.root, "topics/alpha.md", "# Alpha\n\nText \u00e9 \u2014 \u6771\u4eac\n")
        run(self.root)

        def digest():
            files = [self.root / "index.html"] + sorted((self.root / "site").iterdir())
            return {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in files}

        first = digest()
        run(self.root)
        self.assertEqual(first, digest())

    def test_refuses_to_overwrite_foreign_html(self):
        make_fieldbook(self.root)
        write(self.root, "site/index.html", "<html>hand made</html>")
        write(self.root, "index.html", "<html>hand made root</html>")
        code, out = run(self.root)
        self.assertEqual(code, 2)
        self.assertIn("REFUSED", out)
        self.assertIn("site/index.html", out)
        self.assertIn("index.html", out)
        self.assertEqual(self.page("site/index.html"), "<html>hand made</html>")
        self.assertFalse((self.root / "site/alpha.html").exists())
        code, out = run(self.root, "--force")
        self.assertEqual(code, 0, out)
        self.assertIn(br.GENERATOR_META, self.page("site/index.html"))

    def test_overwrites_own_pages_and_never_deletes(self):
        make_fieldbook(self.root)
        run(self.root)
        write(self.root, "site/stale.html", "<html>" + br.GENERATOR_META + "old</html>")
        (self.root / "topics/beta.md").unlink()
        code, out = run(self.root)
        self.assertEqual(code, 0)
        self.assertTrue((self.root / "site/beta.html").exists())
        self.assertTrue((self.root / "site/stale.html").exists())
        self.assertIn("left in place", out)

    def test_dry_run_writes_nothing(self):
        make_fieldbook(self.root)
        before = sorted(str(p) for p in self.root.rglob("*"))
        code, out = run(self.root, "--dry-run")
        self.assertEqual(code, 0)
        self.assertEqual(before, sorted(str(p) for p in self.root.rglob("*")))
        self.assertIn("would write", out)
        self.assertIn("site/alpha.html", out)

    def test_dry_run_still_fails_on_problems(self):
        make_fieldbook(self.root)
        write(self.root, "topics/alpha.md", "# Alpha\n\n[x](beta.md#nope)\n")
        self.assertEqual(run(self.root, "--dry-run")[0], 1)

    def test_absolute_path_scrubbing(self):
        make_fieldbook(self.root)
        write(self.root, "topics/alpha.md",
              "# Alpha\n\nLink [bad](file:///C:/Users/x/a.txt) and [drive](C:\\Users\\x\\a.txt) and "
              "[unc](\\\\server\\share\\a.txt).\n")
        code, out = run(self.root)
        page = self.page("site/alpha.html")
        self.assertEqual(code, 1, out)
        self.assertNotIn("file:/", page)
        self.assertNotIn("C:\\", page)
        self.assertNotIn("\\\\server", page)
        self.assertNotIn('href="file', page)
        self.assertIn("link to local path dropped", out)

    def test_path_in_code_text_replaced_without_failing(self):
        make_fieldbook(self.root)
        write(self.root, "topics/alpha.md",
              "# Alpha\n\nRoot is `J:\\projects\\sites\\Thing` and `file:///x/y` here.\n\n```\ncd C:\\work\\dir\nls\n```\n")
        code, out = run(self.root)
        page = self.page("site/alpha.html")
        self.assertEqual(code, 0, out)
        self.assertEqual(page.count("[local path removed]"), 3)
        for bad in ("J:\\", "C:\\", "file:///", "projects"):
            self.assertNotIn(bad, page.split("<main")[1])
        self.assertIn("\nls\n", page)

    def test_path_in_prose_replaced_and_fails(self):
        make_fieldbook(self.root)
        write(self.root, "topics/alpha.md", "# Alpha\n\nSaved at D:\\data\\file.csv, then moved.\n")
        code, out = run(self.root)
        page = self.page("site/alpha.html")
        self.assertEqual(code, 1)
        self.assertIn("[local path removed], then moved.", page)
        self.assertNotIn("D:\\", page)

    def test_prose_with_ordinary_colons_not_scrubbed(self):
        make_fieldbook(self.root)
        write(self.root, "topics/alpha.md", "# Alpha\n\nSee profile: yes. Time 5:30. Note a:b and https://x.org/a:/b.\n")
        code, out = run(self.root)
        self.assertEqual(code, 0, out)
        self.assertNotIn("local path removed", self.page("site/alpha.html"))

    def test_utf8_roundtrip(self):
        make_fieldbook(self.root)
        write(self.root, "topics/alpha.md", "---\ntitle: Caf\u00e9 \u2014 \u6771\u4eac\n---\n\n# Caf\u00e9 \u2014 \u6771\u4eac\n\n"
                                            "na\u00efve \u201cquotes\u201d \u2192 \U0001F600\n\n| \u00e5 | \u00df |\n|---|---|\n| \u00fc | \u4e2d |\n")
        raw = (self.root / "topics/alpha.md").read_bytes()
        (self.root / "topics/alpha.md").write_bytes(b"\xef\xbb\xbf" + raw.replace(b"\n", b"\r\n"))
        code, _ = run(self.root)
        self.assertEqual(code, 0)
        data = (self.root / "site/alpha.html").read_bytes()
        text = data.decode("utf-8")
        for s in ("Caf\u00e9 \u2014 \u6771\u4eac", "na\u00efve \u201cquotes\u201d \u2192 \U0001F600", "<td>\u4e2d</td>"):
            self.assertIn(s, text)
        self.assertNotIn(b"\r\n", data)
        self.assertNotIn("\ufeff", text)

    def test_bad_arguments(self):
        self.assertEqual(run(self.root / "missing")[0], 3)
        self.assertEqual(run(self.root, "--single-file", "../x.html")[0], 3)
        self.assertEqual(run(self.root, "--single-file", "x.txt")[0], 3)
        self.assertEqual(run(self.root, "--single-file", "/abs/x.html")[0], 3)

    def test_slug_collisions(self):
        make_fieldbook(self.root)
        write(self.root, "topics/guidance.md", "# Topic named guidance\n")
        write(self.root, "guidance.md", "# Guidance log\n")
        write(self.root, "evidence/guidance.md", "# evidence copy\n")
        code, _ = run(self.root)
        self.assertEqual(code, 0)
        self.assertTrue((self.root / "site/topic-guidance.html").exists())
        self.assertTrue((self.root / "site/guidance.html").exists())

    def test_headings_unique_and_gap_register_alias(self):
        make_fieldbook(self.root)
        (self.root / "gap-register.md").unlink()
        write(self.root, "evidence/gap-backlog.md", "# Gap backlog\n\n- First gap\n- Second gap\n")
        write(self.root, "topics/alpha.md", "# Alpha\n\n[g](../evidence/gap-backlog.md)\n")
        code, out = run(self.root)
        self.assertEqual(code, 0, out)
        self.assertIn('href="gap-register.html"', self.page("site/alpha.html"))
        self.assertIn("First gap", self.page("site/index.html"))


class WikiArticleTests(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.addCleanup(self._t.cleanup)
        self.hub = Path(self._t.name) / "topic"
        self.root = self.hub / "output" / "fb"
        write(self.hub, "wiki/topics/game.md",
              "---\ntitle: The Game\n---\n\n# The Game\n\nSee [[other|Other]] ([Other](other.md)), "
              "[[other]] and [raw](../../raw/x.md).\n\n## Trap table\n\nData.\n")
        write(self.hub, "wiki/topics/other.md", "# Other\n\nBack to [the game](game.md#trap-table).\n")
        write(self.hub, "wiki/topics/unlisted.md", "# Unlisted\n")
        write(self.hub, "raw/x.md", "raw\n")

    def book(self, entries, roots='["../../wiki"]'):
        make_fieldbook(self.root, cfg=f"source_roots: {roots}\nreader:\n  wiki_articles: {entries}\n",
                       topics__gamma_md="")
        write(self.root, "topics/gamma.md", "# Gamma\n\nFrom [the table](../../../wiki/topics/game.md#trap-table) "
                                           "and [unlisted](../../../wiki/topics/unlisted.md).\n")

    def test_articles_render_without_a_copy_and_links_resolve(self):
        self.book('["../../wiki/topics/game.md", "../../wiki/topics/other.md"]')
        code, out = run(self.root)
        self.assertEqual(code, 0, out)
        game = (self.root / "site/game.html").read_text(encoding="utf-8")
        self.assertNotIn("[[", game)
        self.assertIn('href="other.html"', game)
        self.assertIn("Full data page", game)
        self.assertNotIn("../../raw", game)
        self.assertIn('href="game.html#trap-table"', (self.root / "site/other.html").read_text(encoding="utf-8"))
        gamma = (self.root / "site/gamma.html").read_text(encoding="utf-8")
        self.assertIn('href="game.html#trap-table"', gamma)
        self.assertNotIn("unlisted", [p.stem for p in (self.root / "site").glob("*.html")])
        self.assertNotIn('href="unlisted.html"', gamma)
        self.assertIn('id="fb-data"', (self.root / "site/index.html").read_text(encoding="utf-8"))
        self.assertFalse((self.root / "topics/game.md").exists())

    def test_label_override_names_a_nav_entry(self):
        make_fieldbook(self.root, cfg='source_roots: ["../../wiki"]\nreader:\n  labels: {game: "G1"}\n  wiki_articles: ["../../wiki/topics/game.md"]\n')
        code, out = run(self.root)
        self.assertEqual(code, 0, out)
        self.assertIn('>G1</a>', (self.root / "site/index.html").read_text(encoding="utf-8"))

    def test_single_file_keeps_them_too(self):
        self.book('["../../wiki/topics/game.md", "../../wiki/topics/other.md"]')
        code, out = run(self.root, "--single-file", "book.html")
        self.assertEqual(code, 0, out)
        page = (self.root / "book.html").read_text(encoding="utf-8")
        self.assertIn('href="#game--trap-table"', page)

    def test_entry_outside_a_source_root_fails_loudly(self):
        for entry, roots in (('["../../raw/x.md"]', '["../../wiki"]'), ('["../../wiki/topics/none.md"]', '["../../wiki"]'),
                             ('["../../wiki/topics/game.md"]', '[]')):
            with self.subTest(entry=entry, roots=roots):
                self.book(entry, roots)
                code, out = run(self.root, "--dry-run")
                self.assertEqual(code, 1, out)
                self.assertIn("not a Markdown file inside a declared source root", out)


class RepairRoundTests(Tmp):
    def test_book_with_no_topics_has_no_dead_jump_links(self):
        write(self.root, "fieldbook.config.yml", "subject: Empty\nrelease_status: private\n")
        write(self.root, "guidance.md", "# Guidance\n\nNot built yet.\n")
        code, out = run(self.root)
        self.assertEqual(code, 0, out)
        page = self.page("site/index.html")
        self.assertNotIn('href="#fb-topics"', page)
        self.assertNotIn('href="#fb-start"', page)
        self.assertIn('href="#fb-legend"', page)

    def test_on_hold_and_markdown_kb_refuse(self):
        for cfg, phrase in (("status: on-hold\n", "on-hold"), ("status: on_hold\n", "on-hold"),
                            ("output_mode: markdown-kb\n", "Markdown only")):
            with tempfile.TemporaryDirectory() as t:
                root = Path(t) / "fb"
                make_fieldbook(root, cfg=cfg)
                before = sorted(p.name for p in root.rglob("*"))
                code, out = run(root)
                self.assertEqual(code, 2, cfg)
                self.assertIn("REFUSED", out)
                self.assertIn(phrase, out)
                self.assertEqual(before, sorted(p.name for p in root.rglob("*")))
                self.assertEqual(run(root, "--dry-run")[0], 2)
                self.assertEqual(run(root, "--force")[0], 0)
                self.assertTrue((root / "site/index.html").exists())

    def test_internal_pages_default_by_mode(self):
        make_fieldbook(self.root)
        write(self.root, "guidance.md", "# Guidance log\n\n## 2026-10-01\n\nsteer\n")
        write(self.root, "local-evidence-inventory.md", "# Inventory\n")
        write(self.root, "topics/alpha.md", "# Alpha\n\n[g](../guidance.md) [i](../local-evidence-inventory.md)\n")
        code, out = run(self.root)
        self.assertEqual(code, 0, out)
        self.assertTrue((self.root / "site/guidance.html").exists())
        self.assertIn('href="guidance.html"', self.page("site/index.html"))
        self.assertNotIn("left out", out)

    def test_internal_pages_left_out_for_single_file_review_public(self):
        make_fieldbook(self.root)
        write(self.root, "guidance.md", "# Guidance log\n")
        write(self.root, "local-evidence-inventory.md", "# Inventory\n")
        write(self.root, "topics/alpha.md", "# Alpha\n\n[g](../guidance.md) [i](../local-evidence-inventory.md)\n")
        code, out = run(self.root, "--single-file", "reader.html")
        doc = self.page("reader.html")
        self.assertEqual(code, 0, out)
        self.assertIn("left out as internal", out)
        self.assertIn("guidance.md", out)
        self.assertNotIn("page-guidance", doc)
        self.assertNotIn("page-local-evidence-inventory", doc)
        self.assertNotIn("Guidance log", doc)
        self.assertIn("0 broken", out)
        for status in ("review", "public"):
            write(self.root, "fieldbook.config.yml", f"subject: S\nrelease_status: {status}\n")
            code, out = run(self.root)
            self.assertEqual(code, 0, out)
            self.assertIn("left out as internal", out)
            self.assertNotIn('href="guidance.html"', self.page("site/index.html"))
            self.assertIn("0 broken", out)

    def test_include_internal_overrides(self):
        make_fieldbook(self.root, cfg="reader:\n  include_internal: true\n")
        write(self.root, "guidance.md", "# Guidance log\n")
        code, out = run(self.root, "--single-file", "reader.html")
        self.assertEqual(code, 0, out)
        self.assertIn("page-guidance", self.page("reader.html"))
        write(self.root, "fieldbook.config.yml", "subject: S\nrelease_status: private\nreader:\n  include_internal: false\n")
        code, out = run(self.root)
        self.assertIn("left out as internal", out)
        self.assertFalse((self.root / "site/guidance.html").exists())

    def test_hand_written_css_refused(self):
        make_fieldbook(self.root)
        write(self.root, "site/styles.css", "body { color: red; }")
        code, out = run(self.root)
        self.assertEqual(code, 2)
        self.assertIn("site/styles.css", out)
        self.assertFalse((self.root / "site/index.html").exists())
        self.assertEqual(run(self.root, "--force")[0], 0)
        self.assertIn(br.CSS_MARK, self.page("site/styles.css"))
        self.assertEqual(run(self.root)[0], 0)

    def test_output_dir_junction_outside_root_refused(self):
        make_fieldbook(self.root)
        outside = Path(self._t.name) / "outside"
        outside.mkdir()
        link = self.root / "site"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except (OSError, NotImplementedError):
            import subprocess
            res = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(outside)], capture_output=True)
            if res.returncode != 0:
                self.skipTest("cannot create a symlink or junction here")
        code, out = run(self.root, "--force")
        self.assertEqual(code, 2)
        self.assertIn("outside the Fieldbook root", out)
        self.assertEqual(list(outside.iterdir()), [])

    def test_newest_source_shown(self):
        make_fieldbook(self.root, cfg='reader:\n  newest_source: "2026-10-27 (county record)"\n')
        run(self.root)
        self.assertIn("<b>Newest source</b> 2026-10-27 (county record)", self.page("site/index.html"))

    def test_bare_secondary_unverified_primary_are_plain_text(self):
        out = md("a [secondary] b [unverified] c [primary]")
        self.assertNotIn("chip", out)
        self.assertIn("[secondary] b [unverified] c [primary]", out)

    def test_single_file_dotdot_link_dropped(self):
        make_fieldbook(self.root)
        write(self.root, "evidence/x.pdf", b"%PDF", binary=True)
        write(self.root, "topics/alpha.md", "# Alpha\n\n[doc](../evidence/x.pdf)\n")
        code, out = run(self.root, "--single-file", "out/reader.html")
        doc = self.page("out/reader.html")
        self.assertEqual(code, 0, out)
        self.assertNotIn("x.pdf", doc)
        self.assertIn("outside the single file's folder", out)
        run(self.root, "--single-file", "reader.html")
        self.assertIn('href="evidence/x.pdf"', self.page("reader.html"))

    def test_slug_collision_case_folded(self):
        make_fieldbook(self.root)
        write(self.root, "evidence/Alpha.md", "# Evidence alpha\n")
        write(self.root, "evidence/GAP-REGISTER.md", "# Upper gap\n")
        code, out = run(self.root)
        self.assertEqual(code, 0, out)
        names = [p.name.lower() for p in (self.root / "site").iterdir()]
        self.assertEqual(len(names), len(set(names)))
        self.assertTrue((self.root / "site/evidence-Alpha.html").exists())
        self.assertTrue((self.root / "site/evidence-GAP-REGISTER.html").exists())


class SingleFileTests(Tmp):
    PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 64

    def make(self, **kw):
        make_fieldbook(self.root, **kw)
        write(self.root, "evidence/shot.png", self.PNG, binary=True)
        write(self.root, "evidence/big.png", self.PNG + b"1" * 5000, binary=True)
        write(self.root, "topics/alpha.md",
              "# Alpha\n\n[beta](beta.md) [beta2](beta.md#beta-topic) [d](#details) [home](../README.md#test-town-fieldbook-start-here)\n\n"
              "## Details\n\n![shot](../evidence/shot.png)\n\n![big](../evidence/big.png)\n\n[raw](../evidence/shot.png)\n")
        write(self.root, "topics/beta.md", "# Beta topic\n\n## Details\n\nBeta.\n")

    def test_single_file_only_writes_one_file(self):
        self.make()
        before = {str(p) for p in self.root.rglob("*")}
        code, out = run(self.root, "--single-file", "out/reader.html")
        self.assertEqual(code, 0, out)
        after = {str(p) for p in self.root.rglob("*")}
        self.assertEqual({Path(p).relative_to(self.root).as_posix() for p in after - before}, {"out", "out/reader.html"})

    def test_single_file_structure(self):
        self.make()
        run(self.root, "--single-file", "reader.html")
        doc = self.page("reader.html")
        self.assertEqual(doc.count("<h1"), 1)
        self.assertIn("<style>", doc)
        self.assertNotIn("<link", doc)
        self.assertNotIn("<script", doc)
        self.assertNotIn("http-equiv", doc)
        self.assertIn(br.GENERATOR_META, doc)
        self.assertIn('aria-label="Contents"', doc)
        for slug in ("index", "alpha", "beta", "source-ledger", "gap-register"):
            self.assertIn(f'<section class="page" id="page-{slug}">', doc)
            self.assertIn(f'href="#page-{slug}"', doc)
        self.assertIn("Private", doc)

    def test_anchor_prefixes_prevent_collisions(self):
        self.make()
        run(self.root, "--single-file", "reader.html")
        doc = self.page("reader.html")
        self.assertIn('id="alpha--details"', doc)
        self.assertIn('id="beta--details"', doc)
        self.assertIn('href="#page-beta"', doc)
        self.assertIn('href="#beta--beta-topic"', doc)
        self.assertIn('href="#alpha--details"', doc)
        self.assertIn('href="#index--test-town-fieldbook-start-here"', doc)
        collector = br.Collector()
        collector.feed(doc)
        self.assertEqual(collector.dup_ids, [])

    def test_images_embedded_and_large_noted(self):
        self.make()
        saved = br.IMAGE_LIMIT
        br.IMAGE_LIMIT = 1000
        self.addCleanup(setattr, br, "IMAGE_LIMIT", saved)
        code, out = run(self.root, "--single-file", "reader.html")
        doc = self.page("reader.html")
        self.assertEqual(code, 0, out)
        self.assertIn('<img src="data:image/png;base64,', doc)
        self.assertEqual(doc.count("<img"), 1)
        self.assertIn("[image not embedded: big.png", doc)
        self.assertIn("image over 2 MB", out)
        self.assertIn('href="evidence/shot.png"', doc)

    def test_config_output_mode_selects_single_file(self):
        self.make(cfg="output_mode: single-file\nsingle_file: book.html\n")
        code, out = run(self.root)
        self.assertEqual(code, 0, out)
        self.assertTrue((self.root / "book.html").exists())
        self.assertFalse((self.root / "site").exists())
        self.assertFalse((self.root / "index.html").exists())

    def test_single_file_is_byte_identical_and_refuses_foreign(self):
        self.make()
        run(self.root, "--single-file", "reader.html")
        first = (self.root / "reader.html").read_bytes()
        run(self.root, "--single-file", "reader.html")
        self.assertEqual(first, (self.root / "reader.html").read_bytes())
        write(self.root, "mine.html", "<html>mine</html>")
        code, out = run(self.root, "--single-file", "mine.html")
        self.assertEqual(code, 2)
        self.assertEqual(self.page("mine.html"), "<html>mine</html>")
        self.assertEqual(run(self.root, "--single-file", "mine.html", "--force")[0], 0)

    def test_single_file_scrubs_paths_and_checks_anchors(self):
        self.make()
        write(self.root, "topics/beta.md", "# Beta topic\n\nRoot `C:\\secret\\dir`. [x](#nowhere)\n")
        code, out = run(self.root, "--single-file", "reader.html")
        doc = self.page("reader.html")
        self.assertEqual(code, 1)
        self.assertNotIn("C:\\", doc)
        self.assertIn("missing anchor #beta--nowhere", out)

    def test_single_file_dry_run(self):
        self.make()
        code, out = run(self.root, "--single-file", "reader.html", "--dry-run")
        self.assertEqual(code, 0)
        self.assertFalse((self.root / "reader.html").exists())
        self.assertIn("reader.html", out)


class HelperTests(unittest.TestCase):
    def test_slugify(self):
        self.assertEqual(br.slugify("Hello, World!"), "hello-world")
        self.assertEqual(br.slugify("  A  B "), "a--b")
        self.assertEqual(br.slugify("snake_case-and-dash"), "snake_case-and-dash")

    def test_short_label(self):
        self.assertEqual(br.short_label("Flooring: refinish, carpet or replace"), "Flooring")
        self.assertEqual(br.short_label("Short"), "Short")

    def test_derive_title(self):
        with tempfile.TemporaryDirectory() as t:
            r = br.Reader(t)
            r.subject = "12 Oak Street, Town \u2014 renovation notes"
            self.assertEqual(r.derive_title(""), "12 Oak Street, Town Fieldbook")
            r.subject = "Local delivery market Fieldbook"
            self.assertEqual(r.derive_title(""), "Local delivery market Fieldbook")

    def test_scrub_paths_units(self):
        doc, n_code, n_text = br.scrub_paths("<p>see C:\\a\\b.txt.</p><code>run D:\\x\\y --flag</code>")
        self.assertEqual((n_code, n_text), (1, 1))
        self.assertEqual(doc, "<p>see [local path removed].</p><code>run [local path removed]</code>")


if __name__ == "__main__":
    unittest.main()
