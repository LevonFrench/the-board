---
name: studio-godot-physics-vfx
description: "Use when a Godot 4.x project needs physics or particle-effect work: Jolt vs GodotPhysics, collision layers and masks, CharacterBody3D vs RigidBody3D, SoftBody3D, physics tick rate, deterministic replay or a seekable timeline, GPUParticles3D vs CPUParticles3D, use_fixed_seed, request_particles_process, emit_particle not working, particle collision (HeightField, SDF, collider limits), goo, pus, blood or fluid sims, splatter, wet maps, Decal nodes as splats or weathering, 'physics step too slow', 'particles differ on replay' in Godot 4.x. It does not own shader-only effects (studio-godot-rendering) or gameplay rules (studio-godot-gameplay-code)."
license: MIT
---

# Godot Physics and VFX (physics-vfx specialist)

This role owns what moves, collides, lands and leaves a mark: the physics engine choice and its limits, particle systems and their replay behaviour, small fluid and goo simulations, and decals or splat maps as the record of what landed. The work is judged by cost per step and by whether a replay shows the same thing twice. Tags: [primary] means the author's research marks it as read from docs or engine source or measured locally; [inference] is the author's own reasoning; [general] is not in the author's research and must be checked.

## Stance (the expert delta)

- Determinism is a claim about a whole chain, and the author's research only supports a narrow one: same machine, same binary, same inputs, same step count. A CPU goo sim gave identical SHA-256 state hashes across runs and across 4.7.1, 4.7.2 and 4.8-dev4. No source promises GPU bit-identity across vendors or drivers. Never promise more.
- GPU particles are flight-only. They cannot report landings (no readback, no collision signal), their sub-emitters use unordered atomics and are skipped by seek requests, and seeking freezes collider poses. Anything that must deposit, split or stick lives in a CPU sim.
- Jolt is the default for new projects since 4.6, but existing projects keep their setting, and Godot's SoftBody3D wrapper builds edge constraints only. It cannot rewind and exposes no per-vertex contacts. Do not design around volume, skinning or bend constraints Godot does not expose.
- Measure before choosing a tier. At 320 particles a GDScript step cost 1.44 to 1.57 ms and about 70 percent was the height function. A compute round trip costs about 0.6 ms fixed, so compute does not pay at that size.
- Split hero particles from the surface record. Noita, Portal 2 and The Last of Us keep a small expressive airborne layer and store landed liquid in a grid, paint map or mask.
- Every effect needs a Compatibility path if a web build exists. Compute, CompositorEffect, SDF particle collision and `emit_particle` do not work there.
- A fixed timestep with a render-side interpolation is the baseline for anything replayed. Changing dt changes the result.

## Establish first

- Godot version (`config/features` in project.godot or `godot --version`). Most figures here are 4.7.2-stable.
- Physics engine in use (Jolt or GodotPhysics), found in project settings, and the physics tick rate. Existing projects may still be on the old engine. The key is `physics/3d/physics_engine` (values DEFAULT, GodotPhysics3D, Jolt Physics) [docs].
- Renderer per platform: Forward+, Mobile or Compatibility. Web and webOS use Compatibility.
- Is replay, rewind or scrubbing required? If yes, list every state array that must enter a snapshot.
- Which particles must land, stick, split or leave a mark, and which are only seen in flight.
- Particle counts, collider counts, decal counts, and the target hardware. A debug editor binary runs GDScript 1.3 to 1.9 times slower than an export, so benchmark both.
- Read the scenes that hold GPUParticles3D, SoftBody3D, Decal and Area3D nodes, and any script that instances particle nodes at runtime.

## Workflow

1. Classify each effect: flight-only, lands and deposits, must survive replay, cosmetic. Pick the tier with the verdict table in Numbers.
2. Fix the clocks. Choose a physics tick and a sim dt, write them down, and keep live play and replay on the same dt. A sim run at 1/120 internally diverged when stepped with 1/90.
3. For seekable particles: `use_fixed_seed = true`, store `seed` per attempt, `speed_scale = 0`, `interpolate = false`, `fixed_fps` set explicitly, then `restart(true)` and `request_particles_process(t)` with t a multiple of 1/fixed_fps. [inference from source]
4. For CPU sims: use packed arrays, hoist constants out of loops, keep iteration order fixed, and add sleep for settled particles and a grid or texture lookup for height queries.
5. For deposits: write landings from the CPU sim into a UV splat or wet map, or a few Decals. Keep every renderer a pure function of snapshot data, never of `TIME`.
6. For collision layers and masks: name each layer in project settings, give each body one layer that says what it is and a mask that says what it scans. [docs]
7. Run the per-step benchmark in an export build on target hardware and record mean and peak against the tick budget.
8. Hash the sim state after N steps across two runs and two processes. Add every new state array to the snapshot and re-hash.
9. Hand the look of the result to rendering with the buffers or maps it will read.

## Numbers

- 1,439 to 1,573 us mean, 1,970 to 3,737 us peak: GDScript goop step at 320 particles, 8,333 us tick (1/120 s), editor binary, Ryzen 9 5900X, 4.7.2. Height query 2.44 us per call, normal 9.66 us.
- Cost per particle per step: stuck to a finger 0.25 us, airborne 1.1 to 1.2 us, deposited 9 to 10 us (4.7.2).
- Same kernel, GDScript vs C# vs Rust: 20.5x and 7.5x at 320 particles, 24.9x and 13.6x at 10,000 (4.7.2, Rust scalar single-thread). Move to C# or native beyond about 1,000 to 1,500 live particles. [inference]
- `PackedVector3Array` 172 to 178 ns per particle; typed Array +15 percent; untyped +27 to 33 percent. Three PackedFloat32Arrays were slower (4.7.2).
- Local RenderingDevice dispatch plus sync about 0.5 to 0.6 ms even at 320 elements; main RD dispatch record 14 to 20 us; blocking `buffer_get_data` 0.56 ms at 5 KB, 2.55 ms at 6.4 MB (4.7.2, RTX 3080 Ti).
- GPU particle limits in 4.7.2 source: 32 colliders, 32 attractors, one HeightField per system. Extra colliders are silently skipped. Default `fixed_fps` is 30 on GPUParticles3D and 0 on CPUParticles3D.
- A seek runs ceil(t x fixed_fps) steps in one frame. Large values can crash the GPU.
- Snapshot: 25,664 bytes per frame at 320 particles; re-simulating to step 360 took 684.8 ms, too slow to scrub, so keep snapshots.
- Decals: default cap 512 clustered elements in view; source caps each type separately. Cost scales with screen coverage first.
- Clavet-style neighbour step in GDScript: 5 to 8 ms per substep at 320 particles, 20 to 27 ms at 1,000.
- A 2048 x 2048 RGBA16F splat map is about 32 MiB; update cost 0.1 to 0.3 ms is an estimate. [inference]

## Quality gates

Measurable in code:
- State hash identical across two runs and two processes after N steps, with dt equal to the replay dt.
- Step mean and peak inside the budget on the export build, on target hardware, with the worst-case particle count.
- Seek test: frame f reached by `restart(true)` plus `request_particles_process(f / fps)` matches playing to f, on the same machine.
- No script-instanced GPUParticles3D that depends on `emit_particle` on 4.7.x.
- Collider, attractor and decal counts stay under the engine limits above.
- Every state array appears in capture and restore.

Needs a render or play:
- Landed deposits appear where the CPU sim says they landed, and drying or fading reads right when scrubbed backward.
- Fast particles do not tunnel through colliders at the chosen `fixed_fps`.
- Decal opacity, blend and overlap look right in a real capture. Cleanup previews show full alpha.
- The web or Compatibility build shows the same effect set, or a deliberate fallback.

## Common mistakes

- Using `emit_particle` on runtime-instanced GPUParticles3D on 4.7.x -> pre-place the node and use `restart()` or an `explosiveness = 1` burst (issue #120574).
- Expecting a landing signal from GPU particles -> run a CPU sim for anything that deposits.
- Sub-emitters for satellite drops in a replayed effect -> keep satellites in the CPU sim.
- `amount_ratio < 1` in a replayed effect -> keep it at 1 (random discard, issue #104276).
- Seeking with moving colliders and expecting past poses -> not possible; every step sees the pose at the request.
- Reading `TIME` in a replayed shader or particle process -> drive from replay time.
- Treating CPUParticles3D as a 1-to-1 fallback (a Godot 3 habit) -> in 4 it has no collision, sub-emitters, trails or attractors.
- Using SoftBody3D pressure on an open mesh -> it flies around; and issue #123661 grows a pressured body after a `process_mode` toggle.
- Assuming SoftBody3D stiffness is tick-independent -> compliance derives from the tick rate and `simulation_precision`.
- Shipping a third-party compute fluid unpatched -> one third-party SPH addon failed on 4.7.2 with a push-constant mismatch and was non-deterministic.
- Hundreds of tiny splats as Decals -> a UV splat map or MultiMesh quads; Decals take no custom shader or height.
- Godot 3 `KinematicBody` with `move_and_slide(velocity)` -> CharacterBody3D sets its `velocity` property and calls `move_and_slide()`. [docs]
- Planning on Bullet or the old default -> check the engine setting; new 4.6+ projects use Jolt.

## Handoffs

- studio-godot-rendering takes the look: SSFR, Beer-Lambert thickness colour, wet-skin shading, SSS limits, CompositorEffect. It receives snapshot buffers, the splat or wet map, and the list of Compatibility gaps.
- studio-godot-gameplay-code takes rules: what a pop scores, how input maps to force, round flow. It receives the fixed dt, the state contract and the cancel and reset behaviour.
- studio-godot-platform-ui takes export builds, web and device profiling. It receives the benchmark scene and the budgets.
- Blender takes source-asset fixes: collision proxy meshes, skin UV islands, decal source art. Decal PNGs need straight alpha with RGB dilated into transparent pixels.

## Version notes

- 4.4: GPU particle `use_fixed_seed`, `seed`, `restart(keep_seed)`, `request_particles_process` (PR #92089); Jolt experimental (PR #99895).
- 4.6: Jolt is the default for new projects. The 4.7.2 SoftBody3D XML still says GodotPhysics3D (doc lag).
- 4.7: `process_time_residual` argument (PR #109142); particles stop at timescale 0 (GH-109911); DrawableTexture2D and `texture_blit` added, Compatibility support UNKNOWN.
- 4.7 to 4.7.2: Jolt 5.5.0 bundled. `emit_particle` broken from 4.7-dev3 (issue #120574, milestone 4.8). Master bundles Jolt 5.6.0; the author's 4.8 survey (not included) puts that bump in 4.8-dev2.
- Open at 2026-10-01: #111885 seeks skip sub-emitters, #118802 collision events dropped unless `fixed_fps = 30` (tested 4.6.2), #120170 new GPUParticles3D broken until scene reload.
- 4.8-dev4: Decals in the Compatibility renderer (PR #118070): 64 per frame soft cap, 8 per surface hard cap. Beta only, treat as unstable.

## References

Written from the author's research notes, which are not included.

