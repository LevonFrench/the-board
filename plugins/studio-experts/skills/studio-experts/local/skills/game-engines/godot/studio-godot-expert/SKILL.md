---
name: studio-godot-expert
description: "Use when an agent must drive Godot 4.x for any task and needs to pick how: headless CLI (godot --headless --import, --check-only, --script, --quit-after, --export-release), the user's running editor through an MCP server or editor plugin, or the GDScript language server (port 6005) and debug adapter (6006). Also for: detecting the project version, 'Identifier not declared' only in headless runs, a test run that exits 0 with nothing run, empty screenshots under --headless, rendering a Godot scene for review, hand-editing .tscn or .tres files, uid:// and ext_resource ids, choosing or trusting a Godot MCP server (read-only mode, exec tools, telemetry), Godot 3 code or tutorials on Godot 4, upgrade breaks from 4.4 to 4.8-beta, and whether an agent may file issues or PRs on godotengine. Routes to the five other studio-godot roles. It does not own the specialist work itself (rendering, animation-import, physics-vfx, platform-ui, gameplay-code)."
license: MIT
---

# Godot Expert (family lead and router)

This role is the protocol every Godot 4.x task starts from: which channel to drive the engine through, how to know the version, how to verify without fooling yourself, how to edit scene files without corrupting them, and which specialist takes the work. Tags: [primary] was read from docs, engine source or a repo and checked in the author's research; [community] is a user report; [inference] is the author's reasoning; [general] is not in the author's research and must be checked.

## Stance (the expert delta)

- A green exit code is weak evidence. `--check-only` parses one script and does not load its dependencies. GUT exits 0 when its class names are not imported. GdUnit4 exits 0 when it finds no tests. Always check that the thing you meant to test actually ran. [primary]
- `--headless` renders nothing. Viewport textures come back empty and `save_png` logs an error. Visual claims need a real render (Xvfb with a GPU, Movie Maker, or the user's editor). [primary]
- One driver per project. Two editors fight over the LSP port and any plugin port, and an agent that kills "the godot process" can kill the user's session. Stop only what you started. [primary, community]
- Prefer the editor's own path for scene edits. Disk-writing tools skip the undo stack and can leave a running editor out of date. Hand edits are a last resort and need a git checkpoint first. [primary]
- Every MCP server with exec or eval tools is remote code execution as the editor user. Pick by auth, bind address and read-only mode before features. [primary]
- Do not trust remembered Godot 3 code, or any tutorial older than 4.4, without a version check. Breaks land in every minor release.
- Autonomous agents are banned from contributing to godotengine. Use on your own game is unrestricted. [primary]

## Establish first

- Version: `godot --version`, and `config/features` in `project.godot` (a line like `config/features=PackedStringArray("4.7", "Forward Plus")`) [general]. The stable baseline is 4.7.2-stable (2026-08-18). 4.8-beta1 (2026-10-15) is a prerelease in godotengine/godot-builds, not in godotengine/godot. There is no RC and no 4.8 stable date. [primary]
- Which binary: on Windows use the `*_console.exe` build so output can be read. Export templates must match the editor version exactly. [primary]
- Is the user's editor already running on this project (ports 6005, 6006, any MCP port)? If yes, use it. Never start a second one.
- Git state. Commit or stash before any agent session that writes files.
- The project's tests, linter and renderer. Do not assume GUT, GdUnit4 or gdtoolkit exist.
- Whether the task touches engine contribution, the Asset Store, or a published tool. See Common mistakes.

## Workflow

### Execution channels

| Channel | Use for | Rules |
|---|---|---|
| Headless CLI `godot --headless --path <project> ...` | import, parse checks, SceneTree scripts, tests, exports, long logic runs with `--fixed-fps` and `--quit-after` | `--path` needs a `project.godot`. Wrap in a timeout. Use an absolute `--log-file`. Run `--import` first on a fresh checkout. |
| The user's running editor through an MCP server or editor plugin | scene tree edits, inspector properties, script writes, play, screenshots, debugger log | Needs the editor open on the project. One server, one driver. See MCP safety. |
| GDScript LSP 6005 and DAP 6006 | diagnostics, symbols, hover, breakpoints | A Godot instance must be running on the project. Ports are editor settings (Network > Language Server, Network > Debug Adapter) or `--lsp-port` and `--dap-port`. Confirm on 4.8-beta, whose announcement says nothing about them. [primary] |
| Runtime bridge into the running game | live state, input injection, in-game screenshots | Game must run. Prefer a bridge that uses Godot's debugger protocol over one that injects an autoload. [primary] |
| Xvfb plus a GPU, or `--write-movie` | real renders for review | Not `--headless`. See Headless verification. |

### Capability matrix

| Action | Headless CLI | Editor via plugin | LSP/DAP |
|---|---|---|---|
| Parse one script | yes (`--check-only -s`) | yes | yes (diagnostics) |
| Import and reimport | yes (`--import`) | yes | no |
| Edit a live scene with undo | no | server-dependent | no |
| Run game and read state | script only | yes, with runtime bridge | breakpoints only |
| Screenshots | no | yes | no |
| Export | yes | yes | no |

### The expert loop

1. Establish the brief: version, target platform, renderer, budgets, what "done" looks like in a check that can fail.
2. Plan stages. Name the specialist for each (see Handoffs). One deliverable at a time.
3. Build one stage with the smallest change.
4. Gate it: import clean, parse clean, boot clean, test with a non-zero test count, then a render or play check where the claim is visual or about feel.
5. Fix before advancing. Two rounds failing the same check with no new hypothesis means stop and report options.
6. Deliver with evidence: command lines, exit codes, log excerpts, captures, and what was not verified.

### Headless verification

1. `godot --headless --path <project> --import`. It implies `--editor --quit`. Export commands imply it too. [primary]
2. A missing `.godot/global_script_class_cache.cfg` can show as "Identifier not declared" (expressions) or "Could not find type" (type hints) in headless runs while the editor is fine. The symptom is community-reported; the cache path and the `--import` remedy match the source. [community]
3. `godot --headless --path <project> --check-only -s res://x.gd` exits 0 if the script is valid, else 1 (a script that fails to load also exits 1). [primary]
4. Boot the main scene with `--quit-after <n>` and grep the log for `SCRIPT ERROR` and `ERROR:`. The docs list no exit codes for `--import` or `--export-*`, so read the log. [primary]
5. For visuals on a box with no GPU: official Linux build, `Xvfb :99 -screen 0 1280x720x24`, `DISPLAY=:99`, Vulkan Forward+, `--fixed-fps 60 --audio-driver Dummy --script res://shot.gd`. A SceneTree script saves `get_viewport().get_texture().get_image().save_png(...)`. Proven on 4.8-beta1 with Ubuntu 24.04, driver 580 and one rented GPU only. Set `GODOT_SILENCE_ROOT_WARNING=1` as root. [primary]
6. `--write-movie` forces `--fixed-fps` and needs rendering; `--quit-after` sets the frame count. Software rendering (llvmpipe) managed roughly 5 to 10 fps in one kit's docs. [primary]
7. Debugger runs: `-d` with closed stdin and a script error before the main loop exists crashes with a null MainLoop (issue #124904, open, seen on 4.7.2 and 4.8.beta1). Drop `-d` in CI. The workaround is untested. [community]

### Editing scenes and resources safely

1. Prefer the editor (or a server that routes through it) for open scenes. In 4.7+ open scenes without unsaved changes reload by themselves; on 4.6 `EditorInterface.get_unsaved_scenes()` does not exist, so a changed open scene needs a manual reload. [primary]
2. If you must edit `.tscn` or `.tres` text: git checkpoint, edit, then load the scene headless and check the log. Keep each `ext_resource` id unique and keep `uid` and `path` together. [general]
3. Since 4.4 scripts and shaders have `.uid` sidecar files. Commit them. `load_steps` is deprecated and not written from 4.6; ignore it if present. [primary]
4. `@export_file` stores `uid://` paths from 4.4. `@export_file_path` (4.5) keeps `res://`. [primary]
5. Tool scripts, autoloads and addons run inside the editor process. Ask for approval before writing them. [primary]

### MCP server safety

- Census as of 2026-10-28: no server is verified on 4.8-beta1. First choice NPGameDev/godot-mcp-toolkit (1.1.1, declares 4.2 to 4.7, Node 22+, loopback, session token); second hi-godot/godot-ai (v4.3.1, targets 4.7+); minimal-godot-mcp for LSP diagnostics. Avoid Coding-Solo (stale, no live editor) and servers with unauthenticated sockets. [primary, inference]
- Read-only: `GODOT_MCP_READ_ONLY=1` in the `.mcp.json` env hides every mutating tool in the toolkit. Use it for inspection. `GODOT_MCP_RUNTIME=0` keeps a headless script run off the runtime channel. [primary]
- godot-ai sends telemetry by default; set `GODOT_AI_DISABLE_TELEMETRY=true`. [primary]
- Install into a copy or a branch first. Some servers write autoloads into `project.godot` and leave them behind after a crash. [primary]
- Claude Code asks once to approve a project `.mcp.json` server. A Windows dock may write `cmd /c npx`; do not commit that over a macOS entry. [primary]
- Smoke test after install: list the scene tree, edit one property, run the main scene, read the error log. [inference]

## Numbers

- LSP 6005, DAP 6006 by default. Recommended custom range 1024 to 49151. [primary]
- Server ports seen: toolkit 6550 to 6560, godot-ai 8000 and 9500, tomyud1 6505, beckettlab 8770. A second harness must pick its own ports. [primary]
- GdUnit4 v6.2.2 exit codes: 0 pass, 100 failure or argument error, 101 orphan nodes only, 103 headless refused, 104 version unsupported, 105 script errors at discovery. GUT v9.7.1 exits 1 on failure. [primary]
- `releases[0]` of godotengine/godot is 3.6.3-stable (2026-08-22), not the latest 4.x. Use `/releases/latest`. [primary]
- Milestones 2026-10-28: 4.8 has 329 open and 2430 closed issues. [primary]

## Quality gates

Measurable in code:
- `--import` completes and the log has no new errors.
- `--check-only` exits 0 for every changed script, plus a whole-project load, since one script check skips dependencies.
- A boot with `--quit-after` leaves no `SCRIPT ERROR` lines.
- Test runs report a non-zero test count. A scenario or test is shown to fail when the behaviour is broken.
- Only one editor and one driver touched the project; `git diff` of scene and resource files was read.

Needs a render or play:
- Any claim about look, framing or UI is backed by a real capture, not a headless run.
- Any claim about feel or timing is backed by a played or frame-stepped run.
- On a Windows or macOS desktop with a GPU, no Xvfb is needed: run the project without `--headless`, e.g. `--write-movie <out>.png --fixed-fps 60 --quit-after <frames>`; a window opens while it renders. [general]
- CI and build automation (headless import, tests, exports in a pipeline) belong to this lead; gameplay-code owns the test content, platform-ui the export presets and device checks.
- Xvfb or datacentre-GPU captures are not the player's display path. Recheck colour and vsync effects on real hardware.

## Common mistakes

- Trusting exit 0 -> read the log and the test count.
- `pkill -f <project-name>` to stop a game -> stop only the process you started, by PID. [community]
- Starting a second editor with `--lsp-port` while the user's is open -> probe the port first.
- Assuming Godot 3 habits: `yield` is `await`, `instance()` is `instantiate()`, `connect("sig", obj, "m")` is `sig.connect(callable)`, `KinematicBody` is `CharacterBody3D`, `Spatial` is `Node3D`, `update()` is `queue_redraw()`, the Tween node is gone (`create_tween()`). [primary]
- Using a 4.7-era MCP server claim as 4.8 evidence -> toolkit says "not blocked", not tested.
- Opening an issue, PR or proposal on godotengine with an agent -> the user writes it. Autonomous agent use already earns an auto-ban; the proposals rule forbids AI-written proposals; planned rules cover human-authored code, disclosure and no AI-written communication. Maintainers have asked a reporter whether AI wrote an issue (#124853, closed by the reporter, unconfirmed crash). [primary]
- Selling or sharing assets on the Godot Asset Store without disclosure -> the AI-usage field is mandatory there. The Asset Library has no AI rule. [primary]
- Stating `Variant.to<Type>()` as GDScript -> it is a C++ API. [primary]

## Handoffs

| Work | Role | What crosses |
|---|---|---|
| Renderer choice, shaders, toon, outlines, skin, hair, decal look | studio-godot-rendering | version, renderer, capture method, target platforms |
| glTF or .blend import, skeleton, AnimationPlayer or Tree, frame timing, hitbox tracks | studio-godot-animation-import | version, source asset paths, tick rate |
| Physics engine, collisions, particles, replay determinism | studio-godot-physics-vfx | fixed dt, state contract, export-build benchmark rules |
| Control UI, touch, remote, exports for Android, iOS, web, webOS | studio-godot-platform-ui | version, target matrix, export templates |
| GDScript or C# gameplay, signals, autoloads, saves, tests, lint | studio-godot-gameplay-code | version, test runner, verification commands from this role |
| Source mesh, rig or texture defects | Blender family | asset path, the failing import log |

The owner takes signing, store accounts, engine contributions and anything that sends a message in their name.

## Version notes

- Godot 3 to 4: renames above; `randomize()` runs automatically at load; `call_group()` is immediate by default; tool scripts need `@tool`. [primary]
- 4.4: `.uid` files; `@export_file` stores `uid://` (GH-97912). 4.5: `@export_file_path`.
- 4.6: Jolt and D3D12 (Windows) are defaults for new projects only; glow default blend Screen; no `load_steps` written.
- 4.7: an override of a typed-return method needs an explicit return (`return null`, GH-115763); `is_class` takes StringName; `AudioStreamPlayer` default `area_mask` is 0; new projects default to `canvas_items` stretch.
- 4.8-beta1 (prerelease, feature freeze): scripts cannot inherit their own inner classes (GH-121171); strings as comments are disallowed (GH-121833); main screens are EditorDocks (GH-113051); `PhysicsDirectSpaceState*.intersect_ray_into` and siblings fill typed result objects (GH-113970); Jolt 5.6.0; .NET 10 for C#. A server audit notes `str_to_var` no longer deserialises objects by default. [primary]
- Open 4.8 regressions on 2026-10-28: #124861 (`@export` Dictionary node refs become nil with Editable Children off), #124859 (Metal black viewport on macOS VMs), #124904 (null MainLoop crash). Statuses move; recheck.
- No 4.8 upgrade page existed in godot-docs on 2026-10-28, so the 4.8 list above comes from the beta announcement and merged PRs and may change before stable.

## References

Written from the author's research notes, which are not included.

