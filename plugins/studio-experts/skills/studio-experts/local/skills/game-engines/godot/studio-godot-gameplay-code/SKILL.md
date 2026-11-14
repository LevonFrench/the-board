---
name: studio-godot-gameplay-code
description: "Use when a Godot 4.x project needs GDScript or C# gameplay code: scene and node composition, signals and Callables, autoloads, Resources versus runtime state, groups, static typing, ':=' inference errors ('Cannot infer the type', 'inferred from a Variant'), input actions and InputMap, state machines, save and load (user://), _process versus _physics_process, frame-accurate or tick-locked timing, hitbox timing, @tool scripts, @export and @onready, 'Identifier not declared' only in headless runs, testing with GUT or GdUnit4 (exit codes, tests that pass without running, SceneRunner), linting with gdtoolkit (gdlint, gdformat), porting Godot 3 scripts to 4. It does not own physics simulation and particles (studio-godot-physics-vfx) or UI, touch and platform export (studio-godot-platform-ui)."
license: MIT
---

# Godot Gameplay Code (gameplay-code specialist)

This role owns the rules layer: how scenes and scripts are composed, how state moves between them, how input becomes actions, and how the code is checked. Expert work here is code that is typed, wired by signals, bound to the physics tick where timing matters, and covered by tests that are proven able to fail. Tags: [primary] was read from docs, engine source or a repo and checked in the author's research; [community] is a user report; [inference] is the author's reasoning; [general] is not in the author's research and must be checked. The wiki is thin on architecture patterns, so those parts are short and mostly [general].

## Stance (the expert delta)

- Static types are a gate, not decoration. Untyped code runs and fails later. Type every var, parameter and return, and keep `@export` variables explicitly typed. [community]
- `:=` is not always safe. `Dictionary.get()`, `max()`, `min()` and untyped array items return Variant and raise INFERENCE_ON_VARIANT (default level Error). Untyped values such as an untyped loop variable raise "Cannot infer the type of x variable because the value doesn't have a set type". `var r := load(p)` is fine: it infers Resource. [primary]
- Nodes signal up and call down. A child emits an event; the parent or an autoload connects it. `get_node("/root/X")` and `$"../../Sibling"` hide dependencies. [community]
- Autoloads hold global state only. Per-entity or per-level state in an autoload becomes a god object. [community]
- Timing that must be exact lives in `_physics_process`, once per simulated tick, not in `_process`. [primary]
- A test that cannot fail proves nothing, and a test run that ran nothing can still exit 0. Check the test count every time. [primary]
- Do not trust the exit code of a runner until you know its silent-pass traps. Section Numbers lists them. [primary]

## Establish first

- Godot version (`godot --version`, `config/features`). Several script rules changed in 4.7 and 4.8-beta1. See Version notes.
- GDScript, C# or both. A C# project needs a .NET build; 4.8-beta1 needs .NET 10 or newer. [primary]
- The test framework in use (GUT or GdUnit4, never both) and whether the addon is committed. [community]
- Whether `.godot/` is present. On a fresh checkout run `godot --headless --path <project> --import` first, or class names will not resolve in headless runs. [community]
- Input actions defined in Project Settings > Input Map, the autoload list, and the groups in use.
- Existing lint and format config (`gdlint`, `gdformat`, or gdstyle) and the project's naming style.
- The relevant `.tscn`, `.gd` and `.tres` files and their `.uid` sidecars (4.4+). [primary]

## Workflow

1. Write down the behaviour as a check that can fail: a headless test, a scene run with assertions, or a frame-stepped log. Decide the runner before the code.
2. Compose scenes with one responsibility each. Cache stable node references with `@onready`. Never call `get_node()` or `$Path` inside `_process`. [community]
3. Wire events with signals. Prefer `signal.connect(callable)` over the Godot 3 string form. Connect in code for dynamic wiring and in the editor panel for static wiring, never both for the same handler, or it fires twice. [primary, community]
4. Put shared data in `Resource` subclasses and runtime state in plain nodes or objects. Duplicate a Resource before mutating it per instance, since loaded Resources are shared. [general]
5. Map every input through named actions. Read actions in `_unhandled_input` or `Input.is_action_*`, not raw keys. Inject test input with `Input.parse_input_event`. [general]
6. State machines: one state object or enum per behaviour, transitions in one place, and each state advanced from `_physics_process` when it controls hitboxes or movement. [general]
7. For tick-locked animation and hitboxes: advance the AnimationPlayer from `_physics_process` with `advance(delta)`, set `callback_mode_method` to IMMEDIATE so method tracks fire at the keyed point, and turn physics interpolation off on combat rigs. Details belong to studio-godot-animation-import. [primary]
8. Save and load: write to `user://`, version the save format, and make tests delete or redirect the save first. Store paths with the `@export_file` UID behaviour in mind. [community, primary]
9. For randomness that must repeat, set the seed in `_ready()`. `randomize()` already runs at project load. [primary]
10. Gate the change: `godot --headless --check-only -s res://x.gd` per script, then a whole-project boot, then the tests, then `gdlint` and `gdformat --check`. [community]
11. Record the commands and results as the delivery evidence.

## Numbers

- `--check-only` with `--script` exits 0 if the script is valid, else 1; it does not load dependencies. [primary]
- GUT v9.7.1: exit 0 on pass, 1 on failure or unknown arguments or bad config. A headless run always quits. `-gexit` quits after the run; `-gexit_on_success` quits only on zero failures. [primary]
- GUT silent passes: `quit(0)` if class names are not imported ("Some GUT class_names have not been imported"), and `quit(0)` with "Main loop did not start in time". Run `--import` first and grep the log for those strings. [primary]
- GdUnit4 v6.2.2 (2026-10-07): 0 pass, 100 any test error, failure or argument error, 101 orphan nodes only (decide the orphan policy up front; default to failing CI on it), 103 headless refused, 104 version unsupported (defined, not traced), 105 script errors at discovery. [primary]
- GdUnit4 silent pass: no tests found prints "No test cases found, abort test run!" and exits 0. [primary]
- GdUnit4 headless: refuses with 103 unless `--ignoreHeadlessMode`, because InputEvents are not transported in headless mode. Use Xvfb or a real display for UI tests. Entry is `-a <dir|suite>`; `--run-tests` was not found in the source. [primary]
- A GDScript step that allocates and uses Dictionary ran about 48 ms per physics step in one project. Packed arrays, index loops and `Time.get_ticks_usec()` timing brought the target under about 6 ms. [community]
- gdtoolkit: newest GitHub tag seen was 4.5.0 (2025-10-09). Install `gdtoolkit==4.*`. Exit codes of `gdlint` and `gdformat --check` were not verified. Its grammar lags new syntax, so a file it cannot parse is NOT-RUN, not a finding. [primary, inference]

## Quality gates

Measurable in code:
- Every changed script passes `--check-only`, and the project loads headless after `--import` with no `SCRIPT ERROR`.
- The test runner reports a non-zero test count, the expected exit code, and the log has none of the silent-pass strings above.
- A deliberately broken behaviour makes the test fail. A scripted winner and an idle loser both behave as expected where balance matters. [community]
- `gdlint` and `gdformat --check` are clean, or the unparseable files are named.
- No `@onready` or node lookup inside `_process`. No string-form `connect`. No untyped `var` in new code.
- Tests do not depend on a leftover `user://` save, and Controls a test touches have explicit `name` values, since code-created Controls get names like `@Button@33`. [community]

Needs a render or play:
- Feel, input responsiveness and combat timing are judged in a played or frame-stepped run, not by unit tests.
- Hitbox activation lands on the intended tick under both callback modes, tested near animation boundaries.
- Spawn points and cameras put the actor on screen (`get_viewport().get_visible_rect()`).

## Common mistakes

- `yield(obj, "sig")` -> `await obj.sig`. `export var` -> `@export var`. `onready var` -> `@onready var`. `tool` -> `@tool` (the converter does not change it). [primary, community]
- `connect("died", self, "_on_died")` -> `died.connect(_on_died)`. [primary]
- `instance()` -> `instantiate()`; `KinematicBody2D` -> `CharacterBody2D`, which uses its own `velocity` and `move_and_slide()`. [primary]
- `TileMap` in new scenes -> `TileMapLayer` (deprecated in 4.3 per one community guide). [community]
- `var x := d.get("k", 0.0)` -> `var x: float = d.get("k", 0.0)`. Loop over typed items: `for b: Beam in beams`. [community]
- Seeking an AnimationPlayer for a rollback or hitbox step -> use `advance(delta)`; `seek()` skips events between the two times. [primary]
- Leaving `callback_mode_method` at DEFERRED for hitboxes -> a hitbox can switch on after collision resolves for that tick. [primary]
- Driving combat animation from `_process` -> drift whenever display fps differs from the physics rate. [primary]
- Polling `get_mouse_position()` in a game that tests inject mouse moves into -> read events, or store `event.position` in `_input`. [community]
- Counting input events with GdUnit4 SceneRunner -> issue #1459 (open) reports each simulated event delivered twice to `_unhandled_input` and `_gui_input`. Check before trusting such tests. [community]
- Parameterized GdUnit4 tests whose signature spans lines, or whose sets come from a function returning a constant -> open issues #1463 to #1466; keep signatures on one line. [community]
- Using two test frameworks, or the `--run-tests` flag from a community skill -> one framework, `-a`. [primary]

## Handoffs

- studio-godot-physics-vfx receives the fixed dt, the state contract and the cancel and reset behaviour, and owns collision layers, physics engine choice, particles and replay determinism.
- studio-godot-animation-import owns AnimationPlayer setup, callback modes, method tracks and root motion; this role consumes the tick it exposes.
- studio-godot-platform-ui owns Control layout, focus, touch recognizers and exports; this role receives the normalized control state and defines what it does in game.
- studio-godot-rendering owns shaders and look; it reads state this role exposes through uniforms or exported properties.
- studio-godot-expert owns channel choice, version detection and the headless verification commands this role runs.
- Blender family fixes source-asset problems that block gameplay (missing sockets, wrong scale).

## Version notes

- 4.4: scripts and shaders get `.uid` sidecars; `@export_file` stores `uid://`. 4.5: `@export_file_path` keeps `res://`. [primary]
- 4.7: an override of a typed-return method must return explicitly (`return null`, GH-115763); `is_class` takes StringName; setting one packed-array element no longer calls the whole-array setter (GH-113228); `sync` on blend spaces became `sync_mode`. [primary]
- 4.8-beta1 (prerelease): scripts cannot inherit their own inner classes (GH-121171); strings used as comments are disallowed (GH-121833); `*_into` physics queries fill typed result objects (GH-113970); `Variant.to<Type>()` is C++ only. [primary]
- 4.8 regressions open on 2026-10-28: #124861 (`@export` Dictionary with node references becomes nil when Editable Children is off; avoid node refs in exported Dictionaries on instanced scenes), #124869 and #124746 (GDScript function signature inheritance and release semantics). [community]
- 4.8-beta1 underlines only the relevant span of a warning or error (GH-119588). [primary]
- C#: 4.8-beta1 needs .NET 10 or newer; earlier 4.x lists .NET 8. [primary]
- Godot 3 to 4 name changes in the expert lead's Common mistakes also apply here.

## References

Written from the author's research notes, which are not included.

