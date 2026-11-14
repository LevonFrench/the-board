# Blender agent notes (local overlay, 2026-10-28)

Local addition, not part of the pinned upstream pack. It adds what the vendored Blender roles lack:
the MCP channel as Claude Code and Codex see it, security limits, and Blender changes after the pack
was pinned (5.2.3, 5.3 Beta). Where it conflicts with a vendored Blender file, this file wins; the
vendored `scenario-blender-expert/references/blender-5.2-deltas.md` and `bpy-reliability.md` stay the
main API references. Evidence and sources: the author's research notes (not included). Hot facts (MCP servers, open PRs and issues) need a re-check after 2026-11-27.

## 1. Know the channel before the first call

| | mcp-for-blender (community) | blender_mcp (Blender Lab, official) |
|---|---|---|
| Start | `uvx mcp-for-blender`; add-on via `uvx mcp-for-blender install-addon` | `.mcpb` bundle, `uv run --directory <dir> blender-mcp`; Claude Desktop connector |
| Blender | 3.0+ claimed | 5.1.0 minimum (manifest) |
| Tools | `execute_blender_code`, `look` (`max_size` 200..2000, default 768), `generate_3d`, `search_assets`, `import_asset`, `get_scene_info`, `get_addon_status` | `execute_blender_code`, `get_python_api_docs`, `search_api_docs`, `search_manual_docs`, object/blend-file summaries, window/area screenshots, `render_viewport_to_path`; `_for_cli` variants use `BLENDER_PATH` |
| Env | `BLENDER_HOST`, `BLENDER_PORT` | `BLENDER_MCP_HOST`, `BLENDER_MCP_PORT` |
| Socket timeout | 180 s | 300 s |

- Both default to port 9876. Two MCP add-ons enabled in one Blender clash (a reported cause of 4-5
  minute silent hangs): keep one, or move one to 9877 on both sides.
- The PyPI name `blender-mcp` is the Lab server; the community repo was renamed from `blender-mcp`, so
  old instructions mix the two up. Tool names differ; check which tools exist before planning.
- Version-exact API lookups: the Lab server's `get_python_api_docs`, or `T.bl_rna.properties.keys()`.

## 2. Claude Code and Codex limits

- Claude Code: `MCP_TIMEOUT` 30 s (server startup), `MAX_MCP_OUTPUT_TOKENS` 25,000 (images count),
  `CLAUDE_CODE_MCP_TOOL_IDLE_TIMEOUT` 30 min stdio / 5 min connectors, `MCP_TOOL_TIMEOUT` ~28 h. The
  server's 180 s socket timeout is the usual limiter: long renders and bakes go headless.
- `claude mcp add --env K=V <name>` fails ("Invalid environment variable format"): put another flag such
  as `--transport stdio` between the last `--env` and the name.
- `EINVAL: invalid argument, kqueue` on registration: startup checks block the MCP handshake while
  Blender is slow (fix PR #403 not merged as of 2026-10-28). Start Blender and its MCP server first.
- Windows GUI clients: `spawn uvx ENOENT` means use the full `where uvx` path or `cmd /c uvx ...`;
  `WinError 10013` means a reserved port range (`netsh interface ipv4 show excludedportrange protocol=tcp`).
- Codex: `tool_timeout_sec` defaults to 60 s; raise it per server for looks and generation.

## 3. Security boundary (state it to the user when relevant)

- The community add-on's socket runs any `execute_code` it receives through `exec()` with no
  authentication (issue #404, open, no fix as of 2026-10-28). Keep it on localhost; on shared machines
  treat an enabled add-on as a local code-execution port.
- `generate_3d` image inputs: Hyper3D reads local paths outside the workspace (#405) and Hunyuan3D
  fetches any http(s) URL, including internal addresses (#406). Never pass untrusted paths or URLs.
- `BLENDER_MCP_SAFE_MODE=1` (off by default) is read by the MCP server process (where `claude mcp add --env`
  puts it), not by the Blender add-on; it checks MCP-path scripts with an AST allowlist. It still
  allows bpy render, save/open, import/export and image loads, and does not cover the socket. Never
  describe it as a sandbox. The Lab add-on's `weak_sandbox.py` is not one either.
- Undo does not reverse file writes: save a stage copy before risky edits.

## 4. Blender changes after the pack was pinned

- Current: 5.2 LTS at 5.2.3 (tag 2026-10-21; `pip install bpy` 5.2.3, Python 3.13 only). 5.3 is in
  Beta until 2026-11-04. Read `bpy.app.version` and branch on it.
- Geometry Nodes modifier inputs (5.2+) are keyed by socket identifier, not display name: find it with
  `next(i.identifier for i in ng.interface.items_tree if i.item_type == 'SOCKET' and i.in_out == 'INPUT'
  and i.name == 'Seed')`, then `getattr(mod.properties.inputs, ident).value = 7` and `ob.update_tag()`.
  [inference from the 5.2 notes; confirm on the installed build]
- 5.2.0-5.2.2: `context.temp_override(window=None, screen=None)` crashes Blender (fixed in 5.2.3).
  Never pass `None` for them.
- 5.2.3 auto-run: the option left the warning prompt (the preference remains); `--enable-autoexec` /
  `--disable-autoexec` now hold for the whole session and Recover is never trusted.
- 5.3: prefer `Image.colorspace_settings.interop_id` (`'data'` for non-colour maps,
  `'srgb_rec709_display'` for sRGB) over `name`; never rely on `bpy.data.all_ids` order; new
  `Object/PoseBone.convert_rotation_mode()`, `constraints.new(type, name=...)`,
  `window_manager.undo_stack` (read-only).

## 5. Channel rules (defaults; override only with a stated reason)

Evidence: one creator's Opus 5.5 test on simple props (the author's research notes (not included),
section "MCP vs headless vs computer use"). MCP was about 3x faster on a first build at equal cost, but a
blind judge preferred the headless results in most rounds; computer use cost about 5x and lost. Small
sample, so these are defaults the coordinator may override with a stated reason.

- **Explore live, ship headless.** Iterate over MCP while the owner watches. The deliverable is a
  re-runnable build script (for example `build_<asset>.py`) saved in the project. The acceptance gate is a
  clean headless rebuild from that script, never the live scene state:
  `blender -b --factory-startup --python-exit-code 1 -P build_<asset>.py`
- **Channel by run mode.** Watched interactive session: MCP, one driver per Blender. Unattended,
  overnight or parallel workers: headless only, one Blender process per worker. No shared live scene (agents
  see each other's objects) and no unauthenticated MCP socket. Computer use: never for Blender.
- **One call per stage.** Send a whole stage as one idempotent script that returns a compact result dict.
  In the one reported five-agent run on a shared Blender, it worked only because each agent sent its whole
  job in one call. Each worker's completion report states its MCP calls per stage.
- **Visual acceptance by blind judge.** When builds or iterations compete, a fresh-context judge compares
  review sheets with shuffled labels against a written rubric. On a tie, keep the incumbent (earlier)
  version; with no incumbent (parallel first builds), the owner picks.

### Supporting facts

- Headless: `--python-exit-code 1` must come before `--python`/`-P`. Also check the output file exists
  and is non-zero, and wrap the process in an outer timeout (background runs have hung on audio-device
  shutdown).
- Image budget: Claude bills ceil(w/28) x ceil(h/28) tokens per image (long edge capped at 1568 px, or
  2576 px on Claude 4.7+), and images stay in context. Use one small contact sheet per check
  (`bx_review.py`, or `look` with a modest `max_size`); rendered shading only at checkpoints.
- Community server bounds for beveled curves and text came from control points until PR #407 (open):
  take bounds from the evaluated mesh.
