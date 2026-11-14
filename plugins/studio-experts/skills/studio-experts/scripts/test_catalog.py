"""Offline pack/retrieval checks; no engines, vendor imports, or external writes."""
import ast
import importlib.util
import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("studio_catalog", HERE / "catalog.py")
catalog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalog)

# A copy without the pinned upstream files still has the local family. A copy that fetched them unpatched
# has no local patches to check. The lock says which copy this is; nothing is skipped when both are present.
LOCK = json.loads((HERE.parent / "references/source-lock.json").read_text(encoding="utf-8"))
HAS_VENDOR = (HERE.parent / "vendor/skills").is_dir()
needs_vendor = unittest.skipUnless(HAS_VENDOR, "the pinned upstream files are absent: run scripts/fetch_pinned_upstream.py")
needs_patches = unittest.skipUnless(HAS_VENDOR and LOCK.get("local_patches"), "this copy carries no local patches to upstream files")


class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = catalog.load_roles()

    @needs_vendor
    def test_all_roles_and_integrity(self):
        result = catalog.verify()
        self.assertTrue(result["ok"], result["errors"])
        self.assertEqual(result["roles"], 64)

    @needs_patches
    def test_unity_license_helpers_stay_blocked(self):
        """A fold-in must keep this local patch: read the source, since vendor code is never imported here."""
        path = HERE.parent / "vendor/skills/game-engines/unity/scenario-unity-expert/scripts/ut_env.py"
        functions = {n.name: n for n in ast.parse(path.read_text(encoding="utf-8")).body if isinstance(n, ast.FunctionDef)}
        for name in ("license_ok", "preflight"):
            body = [n for n in functions[name].body if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant))]
            self.assertIsInstance(body[0], ast.Raise, name)

    @needs_patches
    def test_vendored_text_names_no_vendor_install_route(self):
        for path in (HERE.parent / "vendor").rglob("*.md"):
            text = path.read_text(encoding="utf-8")
            for phrase in ("skill_get", "npx skills", "asset_download"):
                self.assertNotIn(phrase, text, path)

    @needs_vendor
    def test_family_is_hard_boundary_even_when_other_app_mentioned(self):
        result = catalog.retrieve(self.data, ["unity"], "Maya FBX feet slide retarget root motion")
        self.assertEqual(result["candidate_count"], 13)
        self.assertTrue(all(r["family"] == "unity" for r in result["candidates"] + result["leads"]))
        self.assertEqual(result["candidates"][0]["name"], "scenario-unity-animation")

    @needs_vendor
    def test_domain_retrieval(self):
        cases = [
            ("maya", "rubbery elbow skinning weights corrective shoulder pinching", "deformation"),
            ("blender", "UV seams cage normal bake baking texel density", "uv-baking"),
            ("unreal", "Sequencer camera cuts trailer first frames movie render", "cinematics"),
            ("zbrush", "watertight resin printable thickness manifold", "pose-print"),
            ("unity", "Brotli WebGL browser headers compressed loading", "web"),
        ]
        for family, query, role in cases:
            with self.subTest(family=family):
                found = catalog.retrieve(self.data, [family], query)["candidates"][:3]
                self.assertIn(f"scenario-{family}-{role}", [r["name"] for r in found])

    def test_local_godot_family_retrieval(self):
        cases = [
            ("Jolt soft body particles seek fixed seed replay", "physics-vfx"),
            ("toon two-tone shader outline inner lines", "rendering"),
            ("glTF import skeleton retarget AnimationTree stepped", "animation-import"),
            ("touch gestures Android export safe area", "platform-ui"),
            ("GDScript signals autoload typed static unit tests", "gameplay-code"),
        ]
        for query, role in cases:
            with self.subTest(role=role):
                found = catalog.retrieve(self.data, ["godot"], query)["candidates"][:2]
                self.assertIn(f"studio-godot-{role}", [r["name"] for r in found])
        leads = catalog.retrieve(self.data, ["godot"])["leads"]
        self.assertEqual([r["name"] for r in leads], ["studio-godot-expert"])

    @needs_vendor
    def test_inflected_symptoms_remain_discoverable(self):
        result = catalog.retrieve(self.data, ["maya"], "rubbery elbows shoulder collapse skeleton controls correct")
        self.assertEqual(result["candidates"][0]["name"], "scenario-maya-deformation")

    @needs_vendor
    def test_pipeline_keeps_both_leads_without_unrelated_families(self):
        result = catalog.retrieve(self.data, ["maya", "unreal"], "skeletal FBX export import")
        self.assertEqual({r["family"] for r in result["leads"]}, {"maya", "unreal"})
        self.assertEqual(result["candidate_count"], 19)

    @needs_vendor
    def test_no_query_is_complete_catalog(self):
        result = catalog.retrieve(self.data)
        self.assertEqual(len(result["leads"]), 6)
        self.assertEqual(len(result["candidates"]), 58)
        self.assertTrue(all(r["retrieval_score"] == 0 for r in result["candidates"]))

    @needs_vendor
    def test_no_match_is_explicit_not_fake_winner(self):
        result = catalog.retrieve(self.data, ["maya"], "xyzzynothingmatches")
        self.assertTrue(any("No matching" in n for n in result["notices"]))
        self.assertEqual(len(result["candidates"]), 10)
        self.assertTrue(all(r["retrieval_score"] == 0 for r in result["candidates"]))

    @needs_vendor
    def test_limit_warns_and_does_not_hide_lead(self):
        result = catalog.retrieve(self.data, ["blender"], "hair", 1)
        self.assertEqual(len(result["leads"]), 1)
        self.assertEqual(len(result["candidates"]), 1)
        self.assertEqual(result["candidate_count"], 13)
        self.assertTrue(any("truncated" in n for n in result["notices"]))

    def test_paths_resolve_inside_pack(self):
        for row in self.data["roles"]:
            self.assertTrue(catalog.contained(row["path"]).is_file())
        with self.assertRaises(ValueError):
            catalog.contained("../outside.txt")

    @needs_patches
    def test_prohibited_helpers_fail_without_importing_vendor(self):
        path = catalog.ROOT / "vendor/skills/game-engines/unity/scenario-unity-expert/scripts/ut_env.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ("license_ok", "preflight")]
        self.assertEqual(len(functions), 2)
        # Compile just the patched standalone function definitions; no vendor imports or other code.
        for node in functions:
            self.assertIsInstance(node.body[-1], ast.Raise)
            self.assertFalse(any(isinstance(n, ast.Call) and not
                                (isinstance(n.func, ast.Name) and n.func.id == "RuntimeError")
                                for n in ast.walk(node)))
        namespace = {"DEFAULT_VERSION": "unused"}
        exec(compile(ast.Module(body=functions, type_ignores=[]), "<patched-functions-only>", "exec"), namespace)
        for name in ("license_ok", "preflight"):
            with self.assertRaisesRegex(RuntimeError, "disabled"):
                namespace[name]()


if __name__ == "__main__":
    unittest.main(verbosity=2)
