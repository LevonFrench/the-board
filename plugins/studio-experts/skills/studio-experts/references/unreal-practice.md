# Unreal practice notes (Unreal Engine 5.9)

Lessons that held when agents built, packaged and tested Unreal Engine 5.9 projects on Windows in November 2026. This file is a local addition, outside the pinned upstream pack and its source lock. Where it disagrees with a vendored Unreal file, this file wins: the vendored procedures were written for 5.8.

Every item was run by a working session unless it is marked **read** (taken from engine source or a tool's files) or **assumed**. None was re-run for these notes, so treat an item as a strong lead and check it on your engine version before you build on it.

## 1. Accepting work

- **Accept a change only from the assembled build.** A worker's stills or a side project's result show that the work exists, not that the game has it. An acceptance line names a file date in the game's content folder, or a shot from the assembled or packaged build.
- **List every screen a player sees and name one shot for each.** A screen that a test flag skips is written down as a gap, and the harness needs a way to hold on that screen and capture it. A menu that a smoke flag skipped shipped broken.
- **Read the packaged build's log, not only its exit reason.** Look for shader compile errors, missing packages and warnings on first load.
- **Check what is in the package.** List the archive, compare its text files with their sources, record its size and hash, and use a clean stage for anything you hand over. A stale copy of a README went out in several archives.
- **Judge motion across the whole cycle.** A shield passed at the end frame and touched the shin at 3 of 9 stride phases. One wrist read 13 degrees in one run and 44 in the next. A pass on a moving subject needs samples across the cycle or several runs.
- **Judge from the real game camera at game distance.** Effects tuned by particle counts were invisible in play, and parts hung below a unit hid behind others from a steep overhead camera. Check a lighting change on every camera of every map: one fog setting read as mist on one map and as a white veil on another.

## 2. One engine tree, many sessions

UnrealBuildTool holds one lock for the whole engine tree, and more than builds need it.

- **A build queues behind another session's build.** `Build.bat` prints "already running, waiting" and then builds with `-WaitMutex`. Queue in the background; never race or stop the other build.
- **RunUAT fails at once if another build starts first:** "Result: Failed (ConflictingInstance)", exit 10. Rerun it. It is not a code error.
- **Every editor or `-game` start also waits on the lock.** It runs the build tool's platform check (`-Mode=ValidatePlatforms`) before the first frame and stalls at "Completed SDK detection" behind another build, until `-NoProgressTimeout` ends it with exit 125. Take the build slot before a launch as well as before a build. `UE_SKIP_UBT_SDK_SETUP=1` in the run's environment skipped the check for proof runs. `-Multiprocess` also skips it (**read**).
- **Queue time counts against a wall-clock timeout.** Start a timeout only once the slot is held.
- **Detect other builds by process name** (UnrealBuildTool, dotnet, UnrealEditor, UnrealPak) and project path. Matching command lines also matches other sessions' monitors.
- **End a timed-out run with its whole process tree,** or a queued `Build.bat` is left behind. Never stop a process another session started.
- **A build that hangs with idle compiler processes** after earlier builds were killed went through with `-NoUBA` (cause **assumed**).
- **After a crashed `-game` run, check that no game process is alive before building.** The next link failed with LNK1104 on the module DLL, and a clean rebuild fixed it.
- **A launch can hang at RHI init under load.** Read the log for where it stopped and rerun unchanged before changing anything.
- **A runner must count its own earlier runs as busy,** or a second batch starts a second editor beside the first.
- **A new project compiles every global shader on its first launch.** Copying a sibling project's local derived data cache and pointing `-DDC` at it skipped that.

## 3. Only the packaged build shows these

- **A `UObject` from `LoadObject` kept in a plain static or namespace pointer is not held by the garbage collector.** The packaged game crashed once a collection ran. Call `AddToRoot()` or hold it in a `UPROPERTY`.
- **Assets loaded only by path** (`LoadObject`, soft paths) are missing unless their folder is in `+DirectoriesToAlwaysCook`.
- **A material using the camera vector in World Position Offset** compiled in the editor and failed in the package.
- **Cooked meshes drop CPU-readable vertex data** unless the mesh has Allow CPU Access. An uncooked `-game` run keeps it.
- **`BuildCookRun` ignores the project's prerequisites setting.** Pass `-prereqs` to stage the runtime installers.
- **A Development package opens a TCP listener at its first frame** (the trace control server), which raises a Windows Firewall prompt for each new executable path. No launch switch turns it off; Shipping builds do not have it. Run such packages from one fixed folder, and never change a firewall entry.
- **A normal exit that logs "Exiting." and then dies** (exit 777003) exited cleanly with `GLog->Flush()` followed by `RequestExitWithStatus(true, code)`. Cause not found.
- **`-ResultFile=<path>` arms the engine result file without `-AgentMode`.** `-AgentMode` forces `-RenderOffScreen`, so a run someone is meant to watch must not use it.
- **Module builds treat C4458** (a local hides a class member) as an error.

## 4. Cost at run time

- **Create nothing at the moment of a gameplay event.** Spawning debris, a cable, a light and first-use effects on a break cost 230 to 250 ms. Creating everything beforehand and only detaching the existing mesh cost 5 to 7.6 ms.
- **An uncooked `-game` run compiles each Niagara system and decal material on first use** (a hitch of 200 ms or more, and the effect stays inactive for up to 4 s). Spawn each one once out of sight early in the run. Wait at least two frames after an event before a shot or a measurement.
- **`AddForce` and `AddForceAtPosition` wake a physics body on every call, even with zero force** (**read**, and measured). A per-tick force on one end of a sleeping chain keeps the chain awake. Skip the call when the body sleeps or the force is near zero.
- **A torn rope of physics segments may never sleep.** Give that state a hard timeout that hands it to a cheap one.
- **Small thrown debris tunnels through the floor** without continuous collision detection (`SetUseCCD(true)`).
- **A bounding-box proxy decides how a thrown flat part lands.** For a plate that must lie flat, give it thin collision of its own.
- **A body dropped from a character must ignore that character's collision,** or the character pins it upright.
- **A ground decal also projects onto debris that falls into its box.** Call `SetReceivesDecals(false)` on debris.

## 5. Tunables as loose data

Ship values that may need changing as loose data files with a staging rule. Log `file=ok|missing|bad` on load, and fall back to the current behaviour when the file is bad. Twice the fastest safe fix late in a project was one value in such a file, checked from a packaged shot, with no compile.

## 6. Scripts that change assets

- **Refuse to save outside the project.** Assert that the package path starts with `/Game/` before any save. A script that fixed material flags once saved an engine plugin material. To change an engine parent, copy it into the project and reparent. A dry run prints the parent material paths first.
- **Do not delete and recreate an asset that an earlier editor session saved.** It crashed the editor twice, and `delete_asset` returned True while leaving the file. Build under a new name, or rebuild in place: `delete_all_material_expressions` then `create_material_expression` and `connect_material_expressions` keeps every reference.
- **`recompile_material` fails in a commandlet,** which has no renderer. Catch it and save; the game compiles the material at first use.
- **An importer that writes a records file must merge with the existing records.**
- **An Interchange glTF import** makes `StaticMeshes`, `SkeletalMeshes`, `Materials` and `Textures` folders, and the Skeleton lands in `SkeletalMeshes`, so pick assets by class. Imported static meshes have no collision and skeletal meshes have no physics asset. `create_physics_asset` merges small bones, so apply forces to the last bone that has a body.
- **`SetAllBodiesBelowSimulatePhysics(bone, true, bIncludeSelf=true)` frees the root-most body too,** and the chain falls off its mount. Pass `false` to keep it as the anchor.
- **An import that mirrors an axis flips face winding.** Reverse each polygon before any inside test. Before trusting a fit check between two assets, print each one's bounds in the shared frame.
- **Check a "same geometry" claim with a geometry diff** (vertex counts, then positions, normals and UVs), not file hashes.
- **Windows paths in `.uproject` JSON need doubled backslashes.**

## 7. Captures

- **A high-resolution screenshot stalls one frame while physics advances one clamped step,** so two shots 0.3 s apart showed the same pose. Time shots of physics motion on accumulated physics time, or shoot when the subject's screen position is where you want it.
- **To capture a fast mechanic, slow the world** (time dilation near 0.04) and shoot at set times after the event. Reset it afterwards.
- **`FScreenshotRequest` can stall for minutes** behind device detection when other sessions use the automation tool, and `FViewport::ReadPixels` gave black frames. A scene capture component into a render target works. Keep it capturing for about a second first, or the frame is under-exposed. Its readback costs 250 to 350 ms, so keep it out of measured windows.
- **Unhide what you hid a few ticks after the last screenshot.** The shot renders later than the request.
- **An off-screen game is silent by default** (`UnfocusedVolumeMultiplier` is 0). Pass `-ini:Engine:[Audio]:UnfocusedVolumeMultiplier=1.0` to record sound.
- **Check `r.DefaultFeature.AutoExposure.ExtendDefaultLuminanceRange` before writing exposure numbers.** At 0, the brightness limits are luminance, not EV100.
- **A point light made with `NewObject` uses unitless intensity** (**read**). Unitless to candela is times 16 / 10000.
- **Clearance checks between meshes must sample the surfaces.** A box has vertices only at its corners.

## 8. Measuring

- **Frame times are real only on a quiet machine.** One build read 8 to 12 ms alone and 17 to 29 ms beside other sessions' engine processes. Record how many other engine processes ran at the start and end of a measured run, compare a phase against a baseline inside one run, and log wall time from launch to exit. A run whose launch and exit were slow is machine load: rerun it.
- **Measure a feature's cooked size from the shader library too.** One effects feature's shaders were twice the size of its packages. Count the shaders no other map uses.
- **To size one asset folder fast, cook it alone in a side copy of the project:** `UnrealEditor-Cmd <project> -run=cook -targetplatform=Windows -NoDefaultMaps -unversioned -COOKDIR=<folder>`.
- **Texture size is usually the biggest lever.** Capping textures at 1K took one generated unit from 79 to 29 MB cooked. A Nanite keep fraction below about 30% saved little more.

## 9. Niagara: failures with no log line

- **A User parameter the system does not declare is ignored,** with no warning. Check the declared parameters before setting one.
- **A GPU system can spawn inactive in `-game`** after an in-place retune, with a clean editor compile. Log `IsActive()` right after spawn, and keep a CPU twin of any short-lived effect.
- **A system mixing one lightweight emitter with stateful ones stayed inactive.** Give the lightweight burst its own system.
- **The Collision module in GPU depth-buffer mode kills occluded and off-screen particles by default,** so a scene capture or an object in front kills them. Turn both kills off and let off-screen particles live after a bounce. Find this with per-emitter particle counts, not screenshots alone.
- **`SpawnSystemAtLocation` makes the component absolute,** so a later attach does not make it follow. Use `SpawnSystemAttached`.
- **The DirectionalBurst template aims its velocity cone along local +X,** not +Z, and brings two size modules that override a written size change. Read the visible inputs back after writing them.
- **Niagara light renderers are not in the Lumen scene** (**read**). For a flash that should show in reflections, spawn a short-lived point light and cap the count.
- **What read at 18 to 22 m on a tactical camera:** a 40 to 60 cm bright core for 50 to 70 ms with 30 to 40 short sparks and a brief light. A 15 cm core did not. Lingering things (a ground glow, smoke still there 2.5 s later) carry a hit at distance.

## 10. Editor Python and the editor's MCP server

- **The server's Python tool returns a return value, not printed output.** Log with `unreal.log` and read the editor log for your own marker line.
- **A blocked or slow tool response is not a receipt.** Read state back after every call. GPU emitter edits can compile for over two minutes, so give the client a long timeout.
- **Windows PowerShell 5.1 writes UTF-8 with a byte-order mark,** and a Python file with one fails to run. Write scripts without it.
- **Each extra editor or `-game` process needs its own server port** (**read**).
- **`-ExecutePythonScript` in a visible editor quits when the script returns,** unless the script calls `unreal.EditorPythonScripting.set_keep_python_script_alive(True)`.
- **`FParse::Value` stops at a comma.** Pass `bShouldStopOnSeparator = false`, or separate list items with another character.
- **An editor started with `-log` froze when its console window was clicked into select mode.** Start unattended editors without `-log`.
- **An editor started by an agent once relaunched itself.** Check for a second instance of your own project before starting another.

## 11. Audio

- **`MetaSoundBuilderSubsystem` is an engine subsystem; `MetaSoundEditorSubsystem`, which owns `build_to_asset`, is an editor subsystem.** Rebuilding under the same name fails unattended even after a delete in the same run. Build only when missing, or use a new name.
- **Runtime-created submix effect presets run on default settings** in a game build. Call `SetSettings` again after the submix is registered.
- **The default attenuation's reverb send bypasses a limiter on a child submix.** Turn the send off or route reverb through the mix.
- **A dynamics processor keyed from an audio bus stayed silent** (cause not found). Keying from a submix works.
- **For a pitch bend on a playing sound,** drive a MetaSound float input into the wave player's pitch shift. The engine pitch multiplier is clamped.
- **Handing a cue from one Quartz clock to another:** queue the cue on the stopped new clock, start that clock from the old one on a bar, and stop the old clock after the cue starts. Check bar alignment in a recording.

## 12. Generated meshes

Generating a whole unit and splitting it failed. Generating each assembly from a four-view sheet worked, and the number of views mattered more than the service (**read**). Hosted meshes arrived turned 90 degrees, at 100 thousand to 1.5 million triangles, some with 4096 textures. A prep step should check yaw from side renders, decimate while keeping UVs, cap textures, and weld open edges before filling holes.
