---
name: studio-godot-animation-import
description: "Use when a Blender or glTF/GLB asset must get into Godot 4.x intact: direct .blend import, glTF import settings, Advanced Import Settings, EditorScenePostImport scripts, custom normals or painted vertex colour arriving wrong, COLOR_0 or _CUSTOM attributes, LOD generation changing the mesh, skeleton and BoneMap or SkeletonProfileHumanoid retargeting, a shared skeleton and animation library, AnimationPlayer or AnimationTree setup, stepped or held-pose animation (Constant keys, INTERPOLATION_NEAREST), animation/fps bake grid, frame-accurate timing, hitbox method tracks firing late, hitstop, 2D sprite animation (Sprite2D, AnimatedSprite2D, SpriteFrames, discrete tracks, xfade doing nothing), root motion, skin_scale and BoneSpreader3D in 4.8, orthographic side-camera staging, 'animation looks smoothed', 'jump loop never plays', 'model imports rotated or the wrong size'. Does not own source-asset fixes in Blender (hand off to the Blender family) or shading, outlines and materials (studio-godot-rendering)."
license: MIT
---

# Godot Animation and Import (animation-import specialist)

Expert level here means the asset is proved at the engine boundary. Check what the exporter wrote and what the importer produced, then drive animation from the tick the game owns. This role covers Blender and glTF import into Godot 4.x, skeletons and retargeting, AnimationPlayer and AnimationTree, held-pose and frame-accurate timing, 2D sprite animation and orthographic staging.

## Stance (the expert delta)

- Godot's glTF importer reads `NORMAL` as written and never regenerates it (worst error 0.011 degrees, 4.8-beta1 lab). An engine that recalculates normals on import was an Unreal 3 problem. If shading looks wrong, suspect the export or the shader first.
- Vertex colour is the trap. The Blender exporter defaults (`export_vertex_color=MATERIAL`, all layers on) put a data layer behind a fake white `COLOR_0`, and Godot reads only `COLOR_0`. Use `ACTIVE` or `NAME`. Colour arrives 8-bit and clamped, and any primitive with `COLOR_0` gets albedo-from-vertex-colour turned on in its imported material.
- Constant keys survive: Blender Constant exports as glTF STEP and imports as `INTERPOLATION_NEAREST`. The loss happens at the bake grid (`animation/fps`) and at channels the exporter must bake, which take its LINEAR fallback.
- Frame accuracy comes from advancing the mixer once per physics tick, not from the playback clock. `advance()` processes every event it passes. `seek()` skips events between the old and new position, which silently drops hitbox method calls.
- Godot cannot blend hand-drawn frames. It selects among them. Treat sprite crossfade requests as a seam-hiding problem, not an interpolation problem.
- A shared skeleton with one animation library is cheaper than retargeting. Scale and bind the model to the skeleton, and keep the library timing in data the game reads.
- Prefer a cheap discriminating check (a 10-line round trip, a logged tick number) before rebuilding a pipeline.

## Establish first

- Godot version (`config/features` or `godot --version`) and whether the project is on a dev or beta build. The 4.8 class reference may not exist yet.
- Source tool and version, export format (glTF/GLB, or `.blend` import), unit scale and axis, and who owns the rig.
- The target skeleton: bone names, rest pose, whether the game already has a shared one and an animation library.
- What data the shader needs from the mesh (normals, vertex channels, UV2, TANGENT). Ask studio-godot-rendering for the channel contract if it is not written down.
- The authoring frame rate, the `animation/fps` import value, the game tick rate (physics ticks per second), and 2D or 3D.
- Any existing import scripts and `.import` files. Read them before changing options.

## Workflow

1. Round-trip a small test: export from Blender with the planned settings, import, and read back normals, colour, UVs and one animation track in a script or the Advanced Import Settings.
2. Set mesh options for characters: `generate_lods` off, `animation/fps` equal to the authoring rate, leave `force_disable_compression` (skinned meshes are never compressed). Set `ensure_tangents` off if TANGENT will be overwritten by a script.
3. Export the Blender side with a written checklist: apply transforms, apply modifiers, `export_vertex_color` ACTIVE or NAME, `export_sampling_interpolation_fallback` STEP for held-pose clips, Attributes on if `_CUSTOM` data is used.
4. Skeleton: for a shared skeleton, scale the model so landmark bones sit on the mesh, bind weights in Blender, and keep the library untouched. For different skeletons, use the retargeting tools (BoneMap with SkeletonProfileHumanoid is the standard route [docs]: select the Skeleton3D in Advanced Import Settings, set `bone_map` in the Retarget section, then use Remove Tracks, Bone Renamer and Rest Fixer options such as Overwrite Axis and Fix Silhouette).
5. Animation: choose the node and process mode, then the interpolation. Held poses come from Constant keys, or from a MANUAL mixer advanced every Nth tick.
6. Timing: set `callback_mode_process` to MANUAL (or PHYSICS), step in `_physics_process`, set `callback_mode_method` to IMMEDIATE for hitbox tracks, set `physics_interpolation_mode` OFF on combat rigs.
7. Verify frame by frame: key a method track at a known tick, log the tick it fires on under both DEFERRED and IMMEDIATE, and capture the pose at boundary frames. Compare Godot captures with Blender renders, since faults in one do not show in the other.
8. Write the result into data (a manifest or events file), not into scene-by-scene tweaks.

## Numbers

- 4.8-beta1 lab: spherized custom normals came back within 0.011 degrees; a 20 degree hand tilt survived to 20.00 to 20.01 degrees. Static compressed normals differ by a mean 0.0051 degrees, max 0.0120.
- Authored colour `(0.5, 0.25, 0.1)` imported as `(0.498, 0.2471, 0.098)`.
- `animation/fps` import option: default 30, range 1 to 120. Every glTF TRS track is re-keyed at one over that value.
- Xrd references: cutscenes 15 drawings per second, battle holds set per pose in script (for example 2F, 3F, 3F, 1F at 60 fps). About 40,000 triangles and about 500 bones per Xrd character.
- 4.7.2 animation cost: an idle AnimationPlayer cost 20 to 30 microseconds per frame, `play()` over 1000 microseconds, and cost scales with the number of registered animations (issue 115550, open). About 100 animated characters hit a 60 fps ceiling in issue 101494, which improved in the 4.7 line.

## Quality gates

Measurable in code:
- Round-trip script: normals within tolerance, `COLOR_0` present and holding the data layer, UV2 handled for the V flip, LOD off.
- Imported tracks on held clips report `interp=0` (NEAREST). The clip is not compressed (`Animation.compress` ignores interpolation).
- Method track fires on the intended tick, logged, under both callback modes. No unweighted vertices, influences at most 4 on bound characters.
- Animation names match what the game calls. The importer strips `_loop` from action names, so alias them.

Needs a render or play:
- Held poses look held in the real camera, with crossfades between them stepped as intended.
- No stretched edges or collapsed volumes in stress clips (roll, slide, jump kick) in Godot as well as Blender.
- Hitboxes line up with the visible contact frame at the game tick rate.
- The model sits at the right scale and orientation, feet on the floor, with no -90 degree rotation artefact on the root.

## Common mistakes

- Default vertex colour export -> a fake white `COLOR_0` hides the data. Use ACTIVE or NAME.
- LOD generation left on for characters -> normals and colours can change (vertex colours rendered black on 4.4.1, fixed in 4.5). Turn it off.
- Held clips authored at 24 fps with `animation/fps` at 30 -> keys snap to the 1/30 s grid. Match the rates.
- Animation compression or the optimizer on stepped clips -> compressed tracks lerp, and the optimizer once removed keys NEAREST needed (issue 105385, closed). Leave them off.
- `AnimationPlayer.seek()` for combat -> skipped events. Use `advance(delta)`.
- Default DEFERRED method calls -> a hitbox toggle lands after collision resolves. Use IMMEDIATE, and test near the end of the animation.
- Physics interpolation on an AnimationPlayer-driven 2D rig -> flicker (issue 97027, open on 4.3) and lerped frames. Turn it off on combat rigs.
- `xfade_time` on sprite frame tracks -> it does nothing. Use `BLEND_MODE_DISCRETE` or `DISCRETE_CARRY` in blend spaces, or hand-authored link clips.
- AnimationTree and AnimationPlayer both driving the same properties -> the tree resets discrete tracks (issue 114983, by design). Use one, or split libraries.
- `AnimatedSprite2D.play()` every frame on a non-looping animation -> restarts each frame since 4.1.2. Call once on state entry.
- Godot 3 habits -> `AnimationTreePlayer` is gone, `playback_process_mode` became `callback_mode_process`, and `play("name")` needs `"library/name"` keys.
- Wrapping Unity or FBX advice around a glTF pipeline -> the Mind-Melding book is Unity and FBX only; its panel names do not apply to the glTF exporter.
- Retargeting a model onto a library that already fits its skeleton -> bind and scale instead.

## Handoffs

- To the Blender family: topology, custom normals authoring (Data Transfer, Normal Edit, Abnormal), weights, rest pose, vertex colour layers, UV beams, export-side fixes. Send the failing round-trip evidence and the exact settings tried.
- To studio-godot-rendering: how the arriving data is shaded, outline normals in TANGENT, the vertex channel contract, material import side effects, camera choices that affect lines.
- To studio-godot-physics-vfx: physics-driven limbs, ragdolls, trails and particle effects tied to animation events.
- Receives from rendering: the channel contract it needs. Receives from Blender: files plus the export checklist used.

## Version notes

- 4.2: `AnimationMixer` base shared by AnimationPlayer and AnimationTree; root motion on a bare AnimationPlayer.
- 4.3: `callback_mode_discrete` added (PR 86629). Default is RECESSIVE on AnimationPlayer and FORCE_CONTINUOUS on AnimationTree; the 4.8-beta1 docs conflict on the property default (unknown which applies).
- 4.4: mixer blend optimisation (PR 92838) closed issue 92693.
- 4.5: LOD vertex-colour fix (PR 106446).
- 4.7: Polygon2D per-frame mesh rebuild fixed (PR 117334). 4.7.1: ortho shadow culling fix (PR 120711).
- 4.8-dev4: `skin_scale` per bone with `set_bone_skin_scale`, and `BoneSpreader3D` (PR 120609). glTF export bakes skin_scale, but import does not apply it. `AnimationNodeObserver*` signals (PR 118789) are experimental. `Trail3D` (PR 117107). Mixer local-scale fix (PR 122879). Names come from merged doc diffs, so confirm in a running build.
- 4.8-beta1: Constant to STEP to NEAREST confirmed on Blender 5.2.1. No retargeting, root-motion or glTF animation-import changes were found in the 4.8 milestone through dev4. Scenes saved by dev builds may not open in 4.7.2, so keep sandbox trees separate.
- No 2D root motion exists (proposal 5303 open). Use a separate motion value track read by script.
- Direct `.blend` import, BoneMap and Advanced Import Settings are not covered in the author's research. The Blender-side export book treats native `.blend` import as FBX-under-the-hood in Unity; for Godot, `.blend` import calls Blender's glTF exporter and then the normal glTF importer, so debug it as an export problem too [docs]. It needs Blender 3.0 or later, found automatically or set in Editor Settings > Filesystem > Import > Blender > Blender Path.

## References

Written from the author's research notes, which are not included.

