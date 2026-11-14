# Compatibility and execution boundaries

This is a pinned local collection, not a claim that six applications or their bridges are installed.
Review and planning need source evidence; live execution additionally needs a suitable installed app
and an available, inspected channel. No Scenario cloud MCP is required. Some app workflows use their own
local bridge, CLI or editor Python; do not confuse those with Scenario's service or auto-install them.
This pack also does not supply a local generative image/video/audio model runtime. Previs and animation
roles cannot substitute for a requested text-to-video generator; report that capability gap explicitly.

| Family | Upstream target / reported evidence | Local use |
|---|---|---|
| Unity | 6000.3.21f1, URP 17.3, macOS Apple Silicon; author reports live checks | Existing Unity CLI/tools preferred. Python runner imports fcntl and assumes macOS; not Windows-ready. |
| Blender | 5.2.1; author reports headless suites | Use actual installed version and supported bpy APIs; sculpt/live GUI operations require separate proof. Current 5.2.3 and 5.3 Beta deltas, MCP limits and the MCP security boundary: [blender-agent-notes.md](blender-agent-notes.md). |
| Maya | 2027; offline mocked tests only | In-app API paths remain unverified until a bounded live test on the actual version. |
| Unreal | 5.8, macOS; offline mocked tests only | Engine APIs, MCP and C++ builds are not established by those offline tests. |
| ZBrush | 2026.2.1, macOS bridge demonstrated; full suite incomplete | Inspect bridge/platform assumptions; one driver, bounded operations, verify after timeout before retrying. |
| Godot | Local family (2026-10-28), not upstream; facts measured on 4.7.2 and 4.8-beta1 in the author's research | Read project.godot `config/features` and `godot --version`. Headless CLI first; an editor MCP server only when the user runs one. Never open a second editor on the same project. |

These are upstream claims, not tests performed on this user's machine. Family README.md files retain
their original evidence details. References to the author's tests/projects/archive directories often
point to files not distributed here. Do not report them as locally available proof.

## Before execution

1. Read project instructions and actual app-version metadata. Inspect targeted executable/source paths
   only; do not scan user account, license, credential or entitlement stores. Reuse a running editor
   through the available supported tool, with one driver per session.
2. Inspect the chosen helper and callees for platform-specific paths, fcntl, ps, open, osascript,
   screencapture, shell quoting, subprocess commands, automatic package changes, app shutdown and side
   effects. If unsupported, use existing native tools or write a scoped adapter; label the helper unverified.
3. Unity launches must carry -disable-assembly-updater. Never authorize automatic file updates/migrations
   in any engine/DCC prompt. Do not launch a second editor against an already-open project.
4. Stop at any account, login, license, activation or entitlement flow. Never inspect local license files,
   tokens or account caches; never repair or bypass enforcement. Ordinary internal launch checks are left
   alone. Report a blocker and continue code-only tasks where possible.
5. Start with a bounded representative operation on an authorized working copy; inspect the result before
   scaling up. Only report runtime/visual validation that actually occurred.

## Known blocked upstream paths

Unity ut_env.license_ok reads license state. ut_env.preflight calls it. Neither is patched in the pinned upstream
files this copy fetches, so never call them. Do not recreate
those checks, call equivalent utilities, or follow upstream sign-in/activation advice. The rest of ut_env
remains macOS-specific and is not a supported Windows runner.

The catalog tool never imports vendor helpers, scans projects, opens applications, calls networks or
starts services. Its integrity verifier reads only files listed in source-lock.json.

## Updates

The source-lock records the exact upstream commit, the hashes of the upstream files this copy fetches (files)
and the hashes of this copy's own files (local_files). Keep the upstream MIT license and family README files. Updating the skill is an explicit
maintenance task: acquire a new pinned source, review changes, preserve
family directory relationships, regenerate roles/catalog/lock, run validation and the catalog tests. The regeneration tooling is not included in this copy.
Do not use npx skills update on these nested reference copies.
