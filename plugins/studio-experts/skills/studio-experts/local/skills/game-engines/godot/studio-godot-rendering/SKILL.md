---
name: studio-godot-rendering
description: "Use when a Godot 4.x project needs a renderer choice (Forward+, Mobile, Compatibility), spatial or canvas_item shaders, toon or cel two-tone lighting (DIFFUSE_TOON, custom light(), unshaded step shader, per-character light), outlines (inverted hull, next_pass, stencil Outline preset, depth/normal post-process), inner lines, ambient or shadow washing out the toon bands, Environment, tonemapping, glow, skin shaders (sss_mode_skin, NORMAL_MAP, clearcoat, F0), strand hair or fur in a MultiMesh, decals, lightning or electric-arc shaders, goggle or lens droplets, hint_screen_texture and transparency order, 2D depth tricks, 'my character looks flat/blotchy/black', 'strands render black', texture VRAM or import compression budgets. Does not own import settings, glTF/skeleton/animation work (studio-godot-animation-import) or particles and physics (studio-godot-physics-vfx)."
license: MIT
---

# Godot Rendering (rendering and shading specialist)

Expert level here means the look is built from what the renderer does with the data, not from what the docs imply. Read the engine source or measure on the target build when the docs are vague, keep colour in `fragment()`, decide the lighting route before writing shader code, and check the result in a real render. This role covers renderer choice, spatial and canvas_item shaders, toon lighting, lines, skin and hair shading, screen-reading effects, shader VFX and texture budgets for Godot 4.x.

## Stance (the expert delta)

- Pick the toon route first. Route A is an `unshaded` shader with a per-character `key_dir` uniform (closest to Arc System Works, no scene light or shadow). Route B is a custom `light()` with `step()` times `ATTENUATION` (keeps shadows). Route C is built-in `DIFFUSE_TOON`, which has no threshold, tint or offset and stays soft under ambient light.
- Defining `light()` replaces the built-in per-light maths, and `ALBEDO` is applied after it. Multiplying `ALBEDO` inside `light()` applies it twice (measured on 4.8-beta1). Several popular community toon shaders do this.
- The shader is the easy 10 percent of a cel look. The normals, vertex channels and line textures are the look. An unedited mesh shows blotchy terminator islands that no shader setting fixes.
- Ambient, sky light and reflections are added outside `light()` and are never banded. Any ambient energy fills the shadow tone with a gradient. Disable it (`ambient_light_disabled`) or use an unshaded route.
- Screen-reading materials are transparent materials. A 3D quad with `hint_screen_texture` cannot see transparents and blanks the ones behind it, so refraction overlays go on a full-screen canvas_item or a CompositorEffect.
- Fix winding and colour space before tuning looks. Wrong strand winding turned fur black and made later retunes wrong. Mixed sRGB and linear colour made dark hair about 11 times too bright.
- Match the technique to the camera. The 2D CanvasItem renderer has no depth buffer; sprites drawn as `Sprite3D` in the 3D pipeline can write fragment `DEPTH` for intersection, soft particles and relighting. Plain 2D must fake occlusion with `discard`. Normals-from-8-bit-depth on pixel art is unproven, so prototype first.
- Shader lightning defaults to a shader, not geometry: pure-math zigzag is cheapest, FBM with inverse-distance glow is the common one, and `blend_add` plus `unshaded` replaces Environment glow on mobile. Use `Line2D` or `ImmediateMesh` only when the bolt ends on runtime targets.
- Measure GPU cost with GPU timers on an idle GPU, in the animated state. Wall-clock frame times under contention were noise.

## Establish first

- Godot version (`config/features` in project.godot, or `godot --version`), renderer (Forward+, Mobile, Compatibility), target platform, and whether the camera is perspective or orthographic.
- Which features the renderer lacks. Subsurface scattering, `hint_normal_roughness_texture`, TAA and `CompositorEffect` are Forward+ (CompositorEffect also Mobile). `light()` silently does not run under `vertex_lighting`, which is on by default on mobile platforms.
- The look target and its authoring cost: which normals, vertex colour channels and textures exist, and whether the mesh is skinned.
- Existing materials, shader includes, Environment and light rig. Shared rigs (one key light for every skin tone) must not change per material.
- For performance work, the GPU, resolution, and a GPU-timer capture of the current state.

## Workflow

1. Pick the route and renderer constraints (see Stance). Write down what the look needs from the asset: normals, vertex R/A, ILM-style texture.
2. Build the minimum shader: two-tone step, `key_dir`, base and tint colour, optional vertex-R threshold offset. About 20 lines rendered correctly on a skinned mesh on 4.8-beta1.
3. Add lines. Hull outline: `next_pass`, `cull_front`, unshaded, width from a vertex channel, clip-space push for constant pixel width. Use the stencil Outline preset (4.5+) only as a placeholder.
4. Set Environment, ambient, tonemap, glow and anti-aliasing for the look. Check MSAA against TAA on moving, held-pose characters.
5. For skin or hair, apply the gotchas below (SSS kernel, normal composition, F0, winding, pixel floor) before judging the render.
6. For screen-reading effects, choose the pass (canvas_item overlay or CompositorEffect), set the texture filter to a mipmap mode for blurs, and test against transparents.
7. Budget textures: formats, VRAM, residency. Assert the imported format in a test.
8. Render the real camera and light rig, open the image, compare against the target. Capture GPU timings.

## Numbers

- Toon lab, 4.8-beta1: a clip-space hull rendered at a constant 2.5 to 3 px on a skinned mesh. Authored `COLOR` arrives unconverted but 8-bit (0.5 becomes 0.498).
- Stencil Outline preset: in 4.5-stable and later, experimental, default thickness 0.01 m, object-space grow along shading normals, drawn in the transparent pass.
- Godot 4.7.2 skin work: F0 of a dielectric is 0.16 times SPECULAR squared (specular 0.40 to 0.42 gives skin F0 of about 0.0255). Clearcoat lobe alpha is `mix(0.001, 0.1, CLEARCOAT_ROUGHNESS)`, so keep roughness at 0.28 or more.
- SSS blur reach is about scale times strength of the viewport (119 to 205 px at 1440x900 for scale 0.15). Quality 1/2/3 is 11/17/25 taps.
- Uniform buffer: 65,536 B on desktop, 16,384 B on mobile. A 40-entry per-fragment feature loop cost 0.4 to 0.6 ms over 1.3 M fragments on an RTX 3080 Ti (4.7.2); an 8x8 bin grid cut the reject path to about 0.02 ms.
- Strands: 0.75 px radius floor, MSAA 4x gives 5 coverage levels (2x gives 3). Winding fix alone raised fur luminance 22 percent. A 5-sided tube is about 100 triangles, a ribbon about 28.
- Textures, 4.7.2: lossless 2048 px albedo, normal and roughness cost 50.3 MB VRAM per set; BC7 plus BC5 cost 14.0 MB. A 1280 px crop with BC7/BC5 is about 7.8 MB per variant.
- Lightning: 7 to 20 FBM octaves per fragment is expensive; drop to 3 or 4 on mobile. `blend_add` plus `unshaded` is cheap.
- Screen-copy rule (4.7.2): 3D copies the screen after opaque and before transparent; a screen reader is itself transparent and absent from other readers' copies. 3D has no order-independent transparency.
- Rendered skin tone sits about 10 L* below baked albedo under a warm key, AgX and exposure 0.9 (4.7.2 captures).

## Quality gates

Measurable in code or by script:
- Shader compiles on the target renderer. No `ALBEDO` multiplied inside `light()`. Colours marked `source_color` once. Squares written as `x * x`, not `pow` on a possibly negative base.
- Imported texture formats asserted (BC7/BC5 where intended, mipmaps on where minified). Roughness import `src_normal` set when normal detail is baked.
- GPU timer p95 over repeated runs on an idle GPU, in the animated state, within the frame budget.
- Strand winding is clockwise with `cull_back`. The pixel floor is skipped under `IN_SHADOW_PASS`.
- Rendered tone medians and L* spacing measured in the final frame (8 L* apart for adjacent skin tones).

Needs a render or play:
- The terminator reads as designed on the real mesh, with no blotchy islands.
- Outlines have no gaps on hard edges, hold width at the game camera, and do not shimmer under the chosen anti-aliasing.
- Highlights that never move between materials are traced to a light (A/B its `light_specular`).
- Lightning reads at game scale with glow from HDR threshold or additive blend, not full-screen bloom, and hard `step()` edges do not alias.
- Goop, glass and droplets still show transparent objects behind them.
- Dark skin and dark hair are legible, not crushed.

## Common mistakes

- `DIFFUSE_TOON` expected to give a threshold and a tint -> it fixes the edge at N.L = 0 with no tint; use route A or B.
- Scene ambient on a toon material -> shadows look soft; set `ambient_light_disabled` or go unshaded.
- Godot 3 `hint_color`, `SCREEN_TEXTURE` and `OpenSimplexNoise` habits -> use `source_color`, a `hint_screen_texture` uniform and `FastNoiseLite` in 4.x.
- `textureLod` blur on the screen texture with no mipmap filter hint -> it samples LOD 0; use a filter containing `mipmap`.
- A per-material SSS tint uniform with `sss_mode_skin` -> dead code; the kernel is fixed and only the transmittance alpha counts. Vary tone with `SSS_STRENGTH`, albedo and roughness, or add a rim emission term.
- Bump detail put in `NORMAL_MAP` expected to catch clearcoat -> clearcoat sees only `NORMAL`.
- Strand index order wrong -> black strands; use clockwise indices.
- A screen-pixel width floor in the shadow pass -> strands fatten 28 times in directional shadow maps; guard with `IN_SHADOW_PASS`.
- Shadows switched on and off by strand count -> the look jumps; bind them to the quality tier.
- `next_pass` assumed to draw right after its parent -> set `render_priority`.
- Stencil shader syntax `write_if_depth_fail` copied from the docs table -> use `write_depth_fail`.
- Lossless 2048 px maps shipped per variant -> use BC7/BC5, crop to the visible area, keep two variants resident.
- Metals in a dark environment with no sky reflection -> near-black; raise F0, set `reflected_light_source`, or add a fake-environment term.

## Handoffs

- To studio-godot-animation-import: glTF/Blender import settings, normals and vertex data arriving wrong, LOD generation, skeleton and animation problems, orthographic staging of the camera.
- To studio-godot-physics-vfx: GPUParticles trails, `Trail3D`, particle and fluid simulation, physics that drives the shader inputs. This role keeps the shader side of lightning, droplets and glass.
- To the Blender family: edited normals, painted vertex channels, UV beams and line textures are authored in Blender; send the spec (channel roles, sign convention, bit depth) and receive the file.
- Receives from animation-import: a confirmed mesh with intact normals and vertex data, and the import options used.

## Version notes

- 4.3: reverse-Z depth (PR 88328). Depth-based outline shaders written earlier compare depth the wrong way.
- 4.4: vertex colours rendered black after import with LOD generation (issue 107621), fixed in 4.5 (PR 106446).
- 4.5: stencil support in spatial materials (PR 80710), experimental.
- 4.7.1 and 4.8-beta1: orthographic directional shadow culling fixes (PR 120711, PR 121775). Relevant when characters receive scene shadows under an ortho camera.
- 4.7.2: skin and strand figures above, measured in Forward+ on Vulkan.
- 4.8-beta1: toon, hull outline and glTF lab results above. No built-in outline helper or toon preset additions were found in the 4.8 milestone through dev4.
- 4.8-dev4: decals in the Compatibility renderer (64 per frame soft cap, 8 per surface hard cap); `VisualShaderGroup` for packaging a toon-ramp subgraph; multi-bounce AO approximation in Forward+. The 4.8 class reference was not published at that time, so confirm names in a running build.
- Unverified: whether `use_hdr_2d` keeps HDR highlights in a canvas_item screen overlay; how TAA treats hull outlines on held poses; the sign of the vertex-R shade weight (the developer slide says low is shade; test on a mesh); whether alpha-to-coverage strands cast shadows (the author's research says verify in engine source).

## References

Written from the author's research notes, which are not included.

