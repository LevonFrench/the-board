# Specialist picker

## Decide in this order

1. **Outcome and permission:** identify review, plan, implementation or diagnosis. Split a compound request
   into observable deliverables. Track owner-confirmed decisions separately from proposals.
2. **Application ownership:** the explicit target and actual project outrank keywords. A Unity game with
   an FBX exported from Maya does not automatically require Maya work. Determine where the defect first
   appears. An asset that is correct in its source app but broken after import starts with the destination
   specialist. Add the source specialist only when source/export evidence warrants it or a source change
   is explicitly requested. Generic FBX/OBJ/USD/PNG files do not identify an authoring application.
3. **Available evidence:** read scene/code/asset metadata and supplied captures. Distinguish symptoms from
   causes. List the cheapest discriminating checks before recruiting every possible discipline.
4. **Candidate coverage:** enumerate the relevant family with catalog.py, not just the top search hit.
   Read role boundaries below and the full role catalog. Translate colloquial symptoms into candidates
   ("rubbery elbow" → deformation; "feet skate" → animation/root motion; "muddy shot" → lighting/lookdev).
5. **Primary owner:** choose the specialist whose deliverable directly resolves each workstream. Add a
   supporting specialist only for a distinct dependency or independent acceptance check. A coverage
   matrix must assign each deliverable exactly one accountable owner; helpers can support multiple owners.
6. **Execution readiness:** independently label expertise fit and execution capability. A missing editor
   does not prevent source review; an excellent role match does not prove its bridge works. Check actual
   app/version/OS/tool schemas without touching account or licensing state. State what remains unverified.
7. **Challenge:** broad reviews and consequential implementations get one explicit skeptic/acceptance lens,
   usually assigned to the coordinator or a non-author specialist. It challenges claims against evidence,
   budget, user intent and reversibility. Do not invent a nonexistent upstream skeptic role. A tiny fix
   does not need another agent just to meet this rule.
8. **Stop expanding:** remove duplicate lenses and unrelated families. If a needed discipline is absent
   (e.g. deep audio production, game economy, narrative, accessibility research, backend security), name
   the gap and use an existing appropriate skill/expert if available. Do not relabel a rendering specialist
   as an audio engineer. If the application is truly ambiguous, ask one targeted question and continue
   application-neutral inspection while waiting.

## Decision record

For substantial work, put this in the brief or review summary; for a narrow fix state it briefly:

| Deliverable / symptom | Evidence and owning app | Primary specialist | Support and distinct reason | Dependencies | Acceptance check |
|---|---|---|---|---|---|

Also record mode, explicit exclusions, execution channel, version mismatch, confidence (high/medium/low
with a reason), and unresolved facts. Confidence is qualitative reasoning, never the catalog's text score.
Explain rejected plausible alternatives when they materially affect the choice.

## Domain boundaries

### Unity

- **architecture** owns data, state lifetime, events, saves, input bindings and assemblies; **gameplay** owns
  movement, physics, AI, combat, pooling, multiplayer behavior and in-engine audio integration.
- **animation** owns imported clips, Avatar/retargeting, root motion, IK, Animator, Timeline and Cinemachine.
  Foot sliding may need gameplay support to compare actual velocity; do not assume the source rig is broken.
- **2d** owns sprites, pixels, atlases, Tilemaps and 2D Renderer specifics; **world-building** owns terrain,
  modular levels, spatial readability and streaming. Navigation mechanics belong to gameplay.
- **ui** owns Canvas/UITK layout, fonts, navigation and UI rendering; add architecture for persistent settings,
  mobile for safe-area/platform constraints, or performance only when measured rebuild cost is part of scope.
- **shaders** owns shader code/variants/Render Graph; **rendering-lighting** owns pipeline, lights, probes and
  image formation; **vfx** owns timed effects and particle systems. Pink particles start at VFX/shader evidence,
  not a whole-project rendering rewrite.
- **performance** owns measurements and bottleneck diagnosis, with the implicated domain supporting;
  **mobile** owns Android/iOS constraints; **web** owns browser platform/load/deployment behavior.
- **pipeline-automation** owns imports, generated assets, editor tools, Addressables and builds. It does not
  authorize sign-in, activation, deployment, or rewriting package versions.

### Unreal

- **gameplay** covers C++/Blueprint, input, AI, GAS, replication, saves and UMG/Common UI (there is no separate
  Unreal UI role here). Escalate missing design/accessibility expertise honestly.
- **animation** owns skeletons, retargeting, Control Rig, AnimBP and motion systems; **cinematics** owns
  Sequencer, shot continuity, camera cuts and movie output. Distinguish shot animation from gameplay motion.
- **world-building** owns World Partition, landscape, foliage, PCG and HLOD; **materials** owns surface
  graphs/textures; **lighting-rendering** owns exposure, Lumen, shadows and rendered image quality.
- **vfx** owns Niagara and Chaos destruction; **performance** diagnoses budgets and measured costs.
- **pipeline-automation** owns import/reimport, validators, Python tools and packaging. Destination FBX
  import starts here, with animation added for skeleton/clip-specific failures.

### Blender

- **sculpting** owns organic volume/forms; **hard-surface** owns mechanical/prop modeling and shading topology;
  **retopology** owns deformation-ready edge flow and low-poly fidelity, not just decimation counts.
- **uv-baking** owns seams, packing, density, cages and baked maps; **texturing-shading** owns materials and
  color-space interpretation; **lighting-rendering** owns shot lighting, render settings and compositing.
- **rigging** owns controls, weights, IK/FK, drivers and corrective deformation; **animation** owns motion,
  timing, posing over time and playblasts. Use rig tests to distinguish bad weights from bad keys.
- **hair** owns grooming and cards; **geometry-nodes** owns procedural systems and their data dependencies.
- **previs-storyboard** owns shot language/camera/layout/animatics; **grease-pencil** owns GP drawings and
  2D/2.5D stroke animation. Hybrid jobs can justify both with separate deliverables.

### Maya

- **modeling** owns base meshes/hard surface and clean geometry; **retopology-uv** owns dense-to-low topology,
  deformation loops and UVs; **rigging** owns skeletons/controls/constraints; **deformation** owns weights,
  blendshapes, correctives and range-of-motion quality. A pinching elbow primarily belongs to deformation.
- **animation** owns performance/motion/retargeting; **groom** owns XGen hair; **fx** owns cloth, particles,
  Bifrost, MASH and caches. Hair dynamics may need groom plus FX with a cache handoff.
- **lookdev** owns materials/textures/normal/displacement interpretation; **lighting-rendering** owns Arnold,
  lighting, sampling, AOVs and output. Washed-out textures start at lookdev/color pipeline checks.
- **pipeline-scripting** owns export, USD/Alembic/FBX, references, tools and batch validation.

### ZBrush

- **sculpting** owns brush/remesh workflow and form construction; **character-creature** owns anatomy and
  organic likeness; **stylized** owns stylization/shape language. Choose the requested aesthetic, not all
  three by default. Add anatomy support to stylized work only for a concrete structural problem.
- **hard-surface** owns mechanical forms/armor/props; **retopology-export** owns ZRemesher, projection,
  UV/export and production mesh handoffs; **paint-render** owns polypaint and presentation renders.
- **pose-print** owns posing and printable geometry; **automation** owns repeated SubTool operations,
  ZScript/Python, export batches and round-trip tooling. Automation cannot substitute for artistic judgment.

### Godot (local family)

- **gameplay-code** owns GDScript/C# logic, scene composition, signals, autoloads, saves and tests;
  **physics-vfx** owns Jolt bodies, collision, particles, fluids and replay determinism. A character that
  slides through walls starts at physics-vfx; one that ignores input starts at gameplay-code.
- **rendering** owns renderers, shaders, toon lighting, outlines and VRAM budgets; **animation-import**
  owns glTF/.blend import, skeletons, retargeting and AnimationPlayer/AnimationTree timing.
- **platform-ui** owns Control/UI, touch and controller input, exports and on-device profiling.
- The lead (studio-godot-expert) owns the execution channel, version checks, headless verification and CI/build
  automation. Feet that slide after import start at animation-import (root motion, clip timing, import fps).

## Cross-application handoffs

Only recruit both sides when both sides have work. Define source file/version, export format, units,
axis convention, transforms, naming, topology/triangle budget, UVs, map channels and color spaces,
skeleton/root motion, animation ranges, and destination acceptance as relevant. Do not demand every
field for a simple prop. Preserve source identity and record the exact artifact handed over.

Typical staged ownership:
- ZBrush sculpt → Blender retopology/UV-baking → Unity import: sculpt owner finishes form, Blender owner
  creates the deliverable mesh/maps, Unity pipeline owner verifies import. Animation joins only if needed.
- Maya skeletal FBX → Unreal: Maya pipeline owns export when source-side work is requested; Unreal
  pipeline owns import, Unreal animation owns retargeting. Check scale/skeleton settings at the boundary.
- Blender character → Godot: Blender rigging/animation owner exports glTF (or the project imports .blend);
  Godot animation-import owns import settings, BoneMap and clip timing; rendering joins for shading.
- Blender asset looks wrong in Unity: destination rendering/shader/import checks first; Blender shading
  joins if the exported maps/material assumptions are implicated. Never substitute apps without user intent.

## Retrieval limitations

catalog.py searches names, full upstream descriptions and compact aliases. It deliberately retains all
family candidates and does not infer family from casual mentions in task text. Explicit --family filters
are hard boundaries. Empty/unmatched queries expose the catalog and an uncertainty notice, not a fake
winner. For a broad review, omit --query, map all relevant deliverables, and select semantically. Negations
("not a rig issue"), causal evidence, stage and capability are decisions for the coordinator, not bag-of-words.
