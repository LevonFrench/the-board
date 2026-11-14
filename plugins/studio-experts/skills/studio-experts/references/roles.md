# Complete role catalog

Generated from the pinned upstream frontmatter; the Godot section from the local role files. Read the selected SKILL.md before assigning it.


## Unity

Upstream Unity 6000.3.21f1 / URP 17.3 on macOS: author reports live tests. Local Windows runner unverified; prefer installed Unity tools. License helpers blocked.


### scenario-unity-2d

Use when building a 2D game in Unity 6.3 URP: pixel-art or HD sprite import and PPU, sprite atlases, Tilemaps, Rule Tiles and reskins, the 2D Renderer and 2D lights with normal maps, 2D animation, a platformer or top-down controller ("make a platformer controller that feels good", coyote time, jump buffer, one-way platforms, spikes), Pixel Perfect Camera, a follow or room camera, hit stop and screen shake; or when pixel art looks blurry or shimmers, tiles show seams, 2D lights do nothing or cost too much, the jump feels floaty, or the camera loses the player when falling.


### scenario-unity-animation

Use when a Unity 6.3 task involves character animation or cameras: Mixamo or mocap humanoid import and retargeting, Animator Controllers, blend trees, layers and avatar masks, root motion, foot sliding, IK and Animation Rigging, Playables, Timeline cutscenes, custom tracks and markers, Cinemachine 3 cameras, camera jitter, flipping blends or cameras hitting walls; or when clips import with no animation, a character T-poses, an idle drifts, feet slide or the head misses its aim target.


### scenario-unity-architecture

Use when structuring Unity 6.3 C# code: ScriptableObject data vs runtime state, events and services, inventory, health, save and load, Input System actions and key rebinding, async with Awaitable, assembly definitions, Enter Play Mode and domain reload, .meta files, Git, Smart Merge and LFS. Also when 'my save works in the Editor but not in the build', statics keep values on the second Play, events fire twice or never, an await runs after its object died, rebinds are lost on relaunch, a renamed class loses its data, a scene merge breaks.


### scenario-unity-expert

Use when an agent drives Unity 6.3 (6000.3) on a Mac for any task: batch mode and -executeMethod jobs, a running editor (the user's GUI editor or a headless one), the Unity CLI and com.unity.pipeline, MCP servers, the Test Framework, command-line builds; when a batch run fails silently, 'Scripts have compiler errors', a capture comes back black or pink, or a result must be proven with numbers and a frame; or when a Unity brief must go to the right scenario-unity-* specialist.


### scenario-unity-gameplay

Use when building or debugging Unity gameplay systems: enemy AI that patrols, chases and attacks, NavMesh baking and agents (AI Navigation 2), feet sliding on agents, state machines or behavior trees, physics projectiles that tunnel, the physics spiral, layers and the collision matrix, CharacterController vs Rigidbody characters, object pooling, 'hundreds of enemies', DOTS, Burst or Jobs decisions, Netcode for GameObjects multiplayer, audio mixers, snapshots, volume sliders and 3D combat sounds.


### scenario-unity-mobile

Use when a Unity 6.3 game targets Android or iOS: phone frame budget, overheating after 20 minutes, 'my game stutters on phones', ASTC or ETC2 textures, audio import, URP mobile settings, touch controls, on-screen joystick, UI under the notch or safe area, slow startup, ANRs, 'Android build fails', AAB, keystore signing, target API 36, Google Play upload, iOS Xcode export or archive, privacy manifest, app size, in-app purchases (IAP 5), rewarded ads (LevelPlay), ad consent.


### scenario-unity-performance

Use when a Unity 6.3 game is slow or stutters: low fps, frame spikes, hitches when entering areas or on first effects, GC spikes, too many draw calls or SetPass calls, CPU vs GPU bound questions, Profiler, Profile Analyzer, Memory Profiler, Frame Debugger or Project Auditor work, GPU Resident Drawer or SRP Batcher setup, LOD and Mesh LOD, shader warm-up and variants, memory or VRAM budgets, IL2CPP and build size, or proving a fix with numbers from a player.


### scenario-unity-pipeline-automation

Use when automating a Unity 6.3 content pipeline or build: importing an art drop (FBX, PNG) with AssetPostprocessor rules and naming conventions, generating prefabs or editing scenes from script with correct Undo and SetDirty, Addressables groups, labels and content builds, content-validation tests, batch-mode, command-line or CI builds (Build Profiles, GameCI, GitHub Actions, Accelerator), editor tools; or when textures import wrong or reimport every run, a scripted edit vanishes, bundles duplicate assets, a batch build ignores its defines, or CI cannot activate Unity.


### scenario-unity-rendering-lighting

Use when setting up URP (or choosing URP vs HDRP), configuring URP assets and quality tiers for PC and phones, lighting a stylized or realistic Unity scene (sun, sky, baked or mixed lightmaps, Shadowmask, Adaptive Probe Volumes, reflection probes), or fixing blurry shadows, light leaks, gray bakes, washed-out images, tonemapping and grading, bloom too expensive on mobile, TAA, STP or MSAA choices, GPU Resident Drawer setup, shader warm-up hitches, or a custom shader that vanished or lost its baked light.


### scenario-unity-shaders

Use when a Unity 6.3 URP task involves shaders: hand-written HLSL, Shader Graph water, toon, dissolve or outline, Custom Function nodes, a renderer feature or full-screen effect on Render Graph, compute shaders, shader variants, keywords, stripping, Shader Build Settings, PSO warm-up, or shader cost; or when a material turns pink or invisible, casts no shadow, ignores extra lights under Forward+, an effect 'does nothing', the game stutters the first time something appears, or builds bloat with variants.


### scenario-unity-ui

Use when building or fixing game UI in Unity 6.3: main menu, settings screen (resolution, quality, volume, key rebinding), HUD, health bar, minimap frame; choosing uGUI or UI Toolkit or mixing both; 'UI scales wrong on phones', portrait to 4K, Canvas Scaler, anchors, layout groups collapsing, sort order, UXML/USS, data binding, TextMeshPro or UI Toolkit fonts missing glyphs, localized menus, gamepad navigation, UI draw calls, canvas rebuild spikes, UI tests, or capturing UI to check it.


### scenario-unity-vfx

Use when making or fixing real-time VFX in Unity 6.3: explosions, fireballs, projectiles with muzzle, trail and impact, spells, slashes, shockwaves, smoke, sparks, Particle System (Shuriken) or VFX Graph ('VFX Graph explosion', 'particles look bad', 'effect kills fps on mobile', 'too much overdraw'), mesh effects with scrolling textures, an uber VFX shader with LUT ramps, Custom Data and custom vertex streams, flipbooks and VFX textures, pink particles after URP upgrade, VFX budgets and readability.


### scenario-unity-web

Use when a Unity 6.3 game must run in a browser: 'export to WebGL', Web build settings or Build Profiles, gzip or Brotli, Decompression Fallback, server headers, 'Unable to parse .framework.js.br', build too big or slow to load, itch.io, CrazyGames or Poki limits, Addressables or AssetBundles on the Web, 'Could not produce class with ID', Task.Run freezing the browser, WebGL 2 vs WebGPU, .jslib and SendMessage interop, a page text field that gets no keystrokes, mobile browsers crashing, HTTPS for sensors, hosting and rollout.


### scenario-unity-world-building

Use when building a Unity 6.3 level or open world: terrain from code or heightmaps, procedural islands, erosion, splat and foliage rules, trees and grass, ProBuilder graybox, level gym, modular kit and prefab placement, set dressing, landmarks and player guidance, the island's edge, spline roads, WFC, fog, additive scene streaming, or a world that hitches, pops in, leaks memory or runs slow on mobile. Keywords: Terrain, TerrainData, ProBuilder, blockout, graybox, modular kit, NavMesh, LoadSceneAsync, open world.


## Unreal

Upstream Unreal 5.8 macOS: offline mocked tests only; in-engine execution unverified.


### scenario-unreal-animation

Use when a UE5 task involves characters in motion: "import FBX from Maya" with a skeleton, "retarget animations", IK Rig, IK Retargeter, feet sinking or floating after retarget, mocap cleanup, Motion Matching, Pose Search, Choosers, GASP, state machine vs motion matching, root motion, offset root bone, foot IK, Control Rig, Animation Blueprint cost, "animation is expensive", budget allocator, URO, MetaHuman LODs, ML Deformer, cloth.


### scenario-unreal-cinematics

Use when making a trailer, cutscene, cinematic or short film in Unreal Engine 5.8 with Sequencer: shot lists, master and shot sequences, cameras, lenses, depth of field, camera cuts, spawnables, character animation in shots, per-shot lighting, Movie Render Graph or Movie Render Queue EXR renders, "render darker than the viewport", "first frames pop", "last frame missing", ACES or OCIO to DaVinci Resolve, the 180-degree rule, Sequencer Python, or reviewing a cut.


### scenario-unreal-expert

Use when an agent drives Unreal Engine 5.8 on a Mac for any task: Editor Python (the unreal module), headless UnrealEditor-Cmd -run=pythonscript jobs, Epic's Unreal MCP server, the Remote Control API, console commands and cvars; when a script breaks on 5.8 (EditorLevelLibrary, Remote Control calls refused, Substrate materials black, MRQ presets); when a level, material, shot or build must be judged by numbers and a screenshot before it is called done; or when a brief must go to the right scenario-unreal-* specialist.


### scenario-unreal-gameplay

Use when building or debugging UE5 gameplay: a character with double jump or dash, abilities with cooldowns, enemy AI that patrols, chases and attacks, a health bar or HUD; choosing Blueprint vs C++, GAS or not, StateTree vs Behavior Tree, EQS or Mass; setting up Enhanced Input, Common UI or UMG; replication, RepNotify, save games, World Partition state; "Blueprints are slow", Tick, casts and hard references; "ability won't activate", "enemy ignores the player"; or writing automated gameplay tests with injected input.


### scenario-unreal-lighting-rendering

Use when lighting or rendering in Unreal Engine 5.8: physical light units and exposure (EV100, lux, lumens), Lumen GI and reflections, MegaLights, virtual shadow maps, sky, fog and clouds, post process and color grading, the path tracer, or Movie Render Graph stills. Triggers: "Lumen is noisy", "MegaLights noise", "the interior is too dark", "light leaks", neon signs, a night or dusk scene, "fireflies", "path tracer vs Lumen", "render a still", EXR settings.


### scenario-unreal-materials

Use when a UE5 task involves materials or textures: a master material and instances for a kit, Substrate or legacy, Blendable vs Adaptive GBuffer, glass, emissive screens, decals, edge wear and dirt, landscape layers and RVT, toon or cel shading, "too many shaders" or shader permutations, static switches, usage flags, texture compression (BC7, normal maps, ORM packing, sRGB), texture memory, or "is this material expensive".


### scenario-unreal-performance

Use when an Unreal Engine 5.8 project misses its frame rate or stutters: "optimize to 60 fps", "we run at 38 fps", CPU or GPU bound, game or render thread too long, hitches, traversal or shader stutter (PSO), GC spikes, camera-cut spikes, Lumen, Nanite, VSM, ray tracing, foliage, crowds or Niagara too expensive, async compute, stat unit, ProfileGPU, Unreal Insights, TraceQuery, snapshothitches, scalability and device profiles, dynamic resolution and TSR, streaming budgets, or proving a fix with before and after captures.


### scenario-unreal-pipeline-automation

Use when importing FBX, USD, OBJ or glTF from Maya, ZBrush or Blender into Unreal Engine 5.8 in bulk or reimporting changed files, writing Editor Python tools, Interchange pipelines or import presets, enforcing naming conventions, assigning material instances by script, setting Nanite, collision and LODs per asset class, writing data validators or automation tests, fixing redirectors, or cooking and packaging from the command line (BuildCookRun, RunUAT, CI, Perforce). Also when a scripted import ignores its settings or names, a Python validator never runs, or a Mac build will not package.


### scenario-unreal-vfx

Use when a UE5 task involves Niagara or Chaos destruction: a Niagara fireball, projectile trail, impact explosion, muzzle flash, spell, smoke, sparks, debris, Niagara fluids or flipbooks; "Niagara is too expensive", stat NiagaraOverview, Effect Types, pooling, Data Channels, lightweight emitters, VFX scalability; judging an effect's readability, value, color, timing, white blowout or strobing; or a wall that shatters, geometry collection fracture, Dataflow, damage thresholds, floating chunks, debris cost, Chaos Visual Debugger.


### scenario-unreal-world-building

Use when building or fixing an Unreal Engine 5 level or open world: World Partition, OFPA, Data Layers, Level Instances, Packed Level Actors, HLOD, landscape size, heightmap import or clipping, edit layers, terrain material rules, foliage and grass, a PCG forest or rock scatter, runtime GPU grass, Nanite and tessellation choices, modular kits, a river or village, streaming pop-in, cells not loading, landscape black spots, "PCG shows nothing in the editor", or a world too heavy to hand to lighting.


## Blender

Upstream Blender 5.2.1: author reports headless suites; local version and live GUI capability require verification.


### scenario-blender-animation

Use when animating characters or objects in Blender through Python, a bouncing ball, walk or run cycle, jump, acting shot, lip sync, eye darts or facial animation, blocking in stepped keys, splining, polish, timing and spacing, arcs, overlap, squash and stretch, graph editor handles, slotted actions or NLA layers, staging a playblast, or when animation looks floaty, stiff, slides, pops, chatters, the subject is too small in frame, or a knee pops and needs an expert review.


### scenario-blender-expert

Use when doing any 3D work in Blender through Python or an MCP bridge, headless or in a live session: modeling, sculpting a character or head, retopology, UV unwrapping, baking, texturing, rigging, animating, previs, geometry nodes, lighting and rendering, grease pencil, or finishing an AI-generated mesh into a production asset. Also before exporting or handing off an asset, to check it is ready for a game engine, a render or a 3D print (floating parts, z-fighting, inside-out normals, unapplied scale, missing UVs). Also when a bpy script fails on Blender 5.x API changes, a brush or sculpt operator fails or crashes headless, or a result has to be judged like a professional 3D artist would.


### scenario-blender-export

Use when exporting a model, character or animation from Blender to a game engine, the web or a 3D printer: FBX, glTF/GLB, USD/USDZ or STL for Unity, Unreal Engine, Godot, Roblox, three.js or Apple AR Quick Look. Also when an export arrives at the wrong scale (100x, 0.01), rotated 90 degrees, facing backwards, with extra leaf bones, without its animation, blend shapes or textures; when an FBX loses its metallic or roughness map; when a generated model needs its real size and its pivot on the floor; when making LODs or collision meshes (UCX_, -colonly) for an engine; when converting a folder of models in batch; or when checking an exported file by re-importing it.


### scenario-blender-geometry-nodes

Use when building or debugging Geometry Nodes, headless or live: procedural modeling, scattering objects on a surface, arrays along a curve, repeat or for-each loops, simulation zones, 5.2 physics (cloth, colliders, forces, effectors), closures, bundles, matrices, node-group assets with gizmos. Also when a GN script links nothing, shows red links, ignores modifier inputs, loses instances in a bounding box, or a simulation resets or jumps.


### scenario-blender-grease-pencil

Use when drawing or animating with Grease Pencil in Blender 5.x from Python: 2D or 2.5D illustration, frame-by-frame animation, a cutout or part-based 2D character, strokes with pressure, filled shapes with holes, in-betweens and interpolation, onion skin, Line Art outlines, strokes on 3D meshes, NPR or hybrid motion graphics. Also when GP code fails (GPENCIL, frame.strokes, grease_pencil_modifiers), fills do not show, colors render dark, or draw brushes will not run from a script.


### scenario-blender-hair

Use when grooming hair or fur in Blender with hair curves, such as a character hairstyle, animal fur, procedural fur in geometry nodes, or hair cards and mesh hair for games. Also covers the Essentials hair node assets (Interpolate, Clump, Curl, Frizz, Noise, Trim), density masks, bald spots, parting lines, strand shading in Cycles or EEVEE, and slow grooms. Use it too when a hair script misbehaves headless, for example stale modifier inputs or curve sculpt brushes that do nothing.


### scenario-blender-hard-surface

Use when modeling hard-surface objects in Blender (sci-fi panels, props, weapons, vehicles, robots, machined or product parts) with booleans and cutters, bevel modifiers, weighted normals, or subdivision with support loops or creases. Also when shading is broken (smears on flat faces, stretching near a cut, pinching), a bevel shrinks or vanishes after a boolean, a boolean empties the mesh or leaves holes, choosing n-gons vs quads, or making a game-ready mid-poly.


### scenario-blender-lighting-rendering

Use when lighting, rendering or compositing in Blender: light a character, product or hero shot, interior at dusk or night, three-point or motivated lighting, sun and sky, HDRI, EEVEE vs Cycles settings, light leaks or noise, flat or muddy renders, subject not standing out, AgX/ACES color management, render passes, EXR, light groups, bloom and vignette in the 5.x compositor, rule of thirds and value checks, toon/NPR looks, or judging a render like a lighter.


### scenario-blender-previs-storyboard

Use when turning a script or story into previs, layout, storyboards or an animatic in Blender: beats to shot list, camera and lens per shot, staging, camera height, 180-degree rule, screen direction, shot sizes, when to cut, camera moves, timing stills in the Video Sequencer, markers bound to cameras, Story Tools, Grease Pencil or 2D/3D hybrid boards. Also when an animatic shows the wrong frame, blocking keys are not stepped, Rigify operators are missing, or viewport render fails headless.


### scenario-blender-retopology

Use when turning a dense sculpt, scan or AI-generated mesh into clean topology in Blender, for animation, subdivision or a game low poly with a triangle budget. Also when choosing between QuadriFlow or voxel remesh and manual retopo, placing loops around eyes, mouth and joints, deciding pole placement, setting up a Shrinkwrap cage, fixing volume loss after subdivision, preparing a low poly for baking, or auditing topology for spirals, 6-poles and triangles. Keywords: retopo, retopology, quad remesh, clean up an AI mesh, edge flow, low poly, bake prep.


### scenario-blender-rigging

Use when rigging a character, creature or prop in Blender through Python: "rig this character", Rigify metarig fitting or generation errors, automatic weights or "Bone Heat Weighting failed", weight painting fixes, clothes that do not follow, IK/FK switch, foot roll, twist bones, drivers and custom properties, corrective shape keys, a stylized face rig, ARKit 52 blend shapes or viseme shape keys for face capture, lip sync or a game engine, a mechanical or hard-surface rig, or testing how a rig deforms.


### scenario-blender-sculpting

Use when sculpting in Blender through Python: sculpt a head, face or bust, a stylized or cartoon character, a creature or a realistic portrait; block out from primitives; cut planes, a jaw or gonial angle, cheekbones; fix a jaw or face that looks like a ball or balloon; stylized hair clumps; eyelids; an expression or smirk; plan remesh or multires resolution; reproduce Clay Strips, Crease, Draw Sharp, Scrape, Grab or mask moves without a tablet; final clay renders; or when a sculpt operator crashes headless.


### scenario-blender-texturing-shading

Use when texturing, shading or look-developing in Blender: building a PBR material from a texture set, displacement, procedural materials, edge wear, dirt, grime, color variation, decals, box or triplanar mapping on meshes without UVs, stylized character skin (subsurface, pores), eyes and cornea, hand-painted stylized textures, texture painting or painting masks headless. Also when a material looks plastic, CG, waxy or blown out, color spaces are wrong, or EEVEE and Cycles disagree.


### scenario-blender-uv-baking

Use when UV unwrapping, placing seams, straightening or packing UVs, setting texel density, laying out UDIMs or mirrored UVs, or baking normal, AO, curvature, ID or displacement maps from a sculpt or high poly onto a low poly or retopo in Blender, including Multires bakes. Also when a bake has black or inverted patches, flat areas, cracks, seams, wavy lines or AO ghosts, bpy.ops.object.bake returns CANCELED, or uv.unwrap silently fails.


## Maya

Upstream Maya 2027: offline mocked tests only; in-app execution unverified.


### scenario-maya-animation

Use when animating a character or prop in Maya through Python: a walk or run cycle, a jump or landing, a heavy lift, throw or punch, an acting or dialogue shot, lip sync, eye darts and blinks, stepped blocking, splining, polish, Graph Editor tangents, animation layers, mocap cleanup or retargeting, game clips and root motion, or reviewing a playblast. Also when motion looks floaty, weightless, mushy, poppy, posey, sliding or chattery, or feet slap or skate.


### scenario-maya-deformation

Use when skinning a character in Maya ("bind skin", "fix the weights", weight painting, Skin Tools or ngSkinTools layers), when deformation looks wrong (pinching, candy-wrapper wrist, collapsing elbow or shoulder, volume loss, clothes poking through), when mirroring, copying or capping skin weights for Unreal or Unity, building blend shapes, corrective shapes or pose space deformation (Pose Editor on IK-driven joints), a face rig with shapes or joints, multiple skinClusters, Delta Mush or the ML Deformer, or running a range-of-motion deformation test.


### scenario-maya-expert

Use when doing any Autodesk Maya task through Python or a bridge, headless or live: maya.cmds or OpenMaya 2.0 scripts, mayapy or maya.standalone batch jobs, a commandPort or MCP connection into a running Maya, "Maya 2027", validating or exporting scenes, or a maya.cmds script that fails after the 2025 to 2027 changes (PySide6, OpenPBR, renamed math nodes, removed flags). Also when a Maya model, rig, shot or render must be judged like a professional before it is called done, or a brief must be routed to the right Maya specialist.


### scenario-maya-fx

Use when a Maya task involves simulation or procedural effects: nCloth or Nucleus (a cape, skirt, flag or garment on an animated character, cloth through the body, jittery or stretchy cloth), nParticles, Bifrost graphs (Aero smoke, dust puff, mist, fire, liquids, MPM cloth, snow, sand, "Bifrost smoke"), MASH scattering or motion graphics, sim caches (nCache, Alembic, OpenVDB, file_cache, USD) or FX delivered to lighting or a game engine (flipbook sprites).


### scenario-maya-groom

Use when grooming hair or fur in Maya with XGen (Interactive Groom splines or legacy descriptions): scalp hair, eyebrows, eyelashes, fur, guides, clumps, noise, parting, density maps, a fill layer, aiStandardHair shading, noisy or flickering hair renders, hair that must move (Linear Wire, nHair, Alembic caches), or a groom for Unreal (groom Alembic, cards). Also when XGen hair looks CG, clumps look uniform, the scalp shows through, or an XGen script fails.


### scenario-maya-lighting-rendering

Use when lighting or rendering in Maya with Arnold: a product hero shot, a character close-up or a sequence (master and shot lighting), key, fill and rim placement, "the Arnold render is noisy" or fireflies, render settings and time budgets, AOVs, light groups and EXRs for Nuke, OIDN or noice denoising, ACES or OCIO color, renders that look flat or too dark, Render Setup layers, batch or command-line renders, or judging a lit frame like a lighting supervisor.


### scenario-maya-lookdev

Use when shading an asset in Maya with Arnold: OpenPBR or aiStandardSurface materials, hooking up Substance Painter or UDIM texture sets, color spaces (sRGB, Raw, ACEScg), a normal map that looks wrong, displacement with black holes or faceting, skin SSS, chrome and metals, glass or crystal, car paint, aiStandardHair, porting Standard Surface to OpenPBR, or a lookdev turntable with chrome and gray balls. Also when textures render washed out, too dark or plastic in Arnold.


### scenario-maya-modeling

Use when modeling in Autodesk Maya, such as hard-surface props, weapons, vehicles, a sci-fi crate, a game-ready or SubD film model, or a character or creature base mesh, or when asked to "clean up this model" or a scene before rigging or UVs. Also for support loops vs bevels vs creases, Smart Bevel, weighted normals, hard edges, pinching or wobbly highlights, a faceted cage, flipped faces, a triangle budget, n-gons, non-manifold geometry, mirroring a half, a low poly from a high poly, or deformation-ready topology.


### scenario-maya-pipeline-scripting

Use when writing or fixing Maya pipeline code in Python: mayapy batch jobs over many scenes, validating and auto-fixing scenes, FBX export for Unreal or Unity (static, skeletal, animation clips, Game Exporter), Alembic or GPU caches, USD export, stages and layers, references and namespaces, PySide6 tool windows, OpenMaya 2.0 plug-ins, or slow playback. Also when an FBX lands with wrong scale, normals, tangents or extra takes, a USD export has one frame or smoothed meshes, or one bad file kills a batch.


### scenario-maya-retopology-uv

Use when turning a dense sculpt, scan, ZBrush export or AI-generated mesh into animation-ready or game-ready topology in Maya without a mouse ("clean up this AI mesh", "retopo this character", Quad Draw, Retopologize), testing it deforms before rigging (bad elbow or wrist bend, lids popping through the eyes), or unwrapping UVs, cutting seams, setting texel density, mip-safe padding, UDIMs, lightmap UVs, stacking mirrored shells, or preparing a low poly and cage for baking. Keywords: edge flow, eye and mouth loops, Unfold3D, bake prep.


### scenario-maya-rigging

Use when rigging a character, creature or prop in Maya: "rig this character", placing or orienting joints, Orient Joint doing nothing, IK/FK switch and matching, pole vector flips or elbow drift, space switching, foot roll, spline IK spine, offsetParentMatrix, blendMatrix or matrix rigging, controls and lockdown for animators, Quick Rig, HumanIK, AdvancedSkeleton or mGear, a game skeleton for Unreal or Unity, or a slow rig (parallel evaluation, profiling, GPU Override not kicking in).


## Zbrush

Upstream ZBrush 2026.2.1 macOS bridge demonstrated; complete live coverage and local Windows channel unverified.


### scenario-zbrush-automation

Use when automating ZBrush 2026: batch processing a folder of OBJ or ZTL files, a ZBrush Python script or ZScript, recording a macro to learn a palette path, the ZBrush -script command line, scripting UV Master, Decimation Master or Multi Map Exporter, exporting every SubTool, GoZ or GoB round trips with Maya or Blender, renaming SubTools, or batch reports. Also when a plugin press never returns, a dialog stalls a batch, one file kills the whole run, or GoZ updates the wrong SubTool.


### scenario-zbrush-character-creature

Use when sculpting a realistic head, face, portrait, body or creature in ZBrush (anatomy, landmarks, proportions, "the face looks off", eyes, lips, jaw), adding skin, pores, wrinkles or reptile and dragon scales with alphas, Surface Noise, layers or morph targets, planning subdivision or HD Geometry for a film close-up, reprojecting detail, sculpting cloth folds or running Dynamics cloth, growing FiberMesh fur or hair, making horns, or judging a character sculpt the way a senior character artist would.


### scenario-zbrush-expert

Use when an agent drives Maxon ZBrush 2026 for any task (sculpt in ZBrush, DynaMesh, ZRemesher, UVs, export, polypaint, posing, 3D print, clean up an AI mesh in ZBrush), when writing ZBrush Python (zbrush.commands) or ZScript, when the ZBrush bridge is not answering, a palette path or set() does nothing, a scripted stroke does not sculpt or a dialog blocks a script, or when a ZBrush result has to be judged the way a professional artist would.


### scenario-zbrush-hard-surface

Use when modeling hard surface in ZBrush 2026 (sci-fi helmet, weapon, prop, armor plates, mechanical parts, kitbash, vents, panel lines, bolts, concept to game asset), when using ZModeler, Dynamic Subdivision and creasing, Live Boolean, Knife, Clip, Slice or Trim curves, IMM, ArrayMesh, NanoMesh or Panel Loops, or when edges look razor sharp, a Make Boolean Mesh fails or leaves holes, planes look wobbly, Mirror And Weld erased an edit, or ZRemesher ruins a hard-surface part.


### scenario-zbrush-paint-render

Use when polypainting in ZBrush (skin color zones, fills, cavity or AO passes, Spotlight), baking polypaint to a texture or vertex color, rendering a ZBrush model with BPR or Redshift, making render passes, a turntable or portfolio shots, or when paint looks like uniform beige or clown makeup, is blurry, is hidden under a texture or in Redshift, or a render is noisy, clipped, orthographic or bruised.


### scenario-zbrush-pose-print

Use when posing a sculpt or preparing it for 3D printing in ZBrush: "pose this character", Transpose Master, TPoseMesh, Gizmo posing with masks, ZSphere rig, Proxy Pose, weapon in the hand, stretching after posing, "3D print this", 1/6 scale statue, miniature, resin or FDM, hollowing, wall thickness, drain holes, keys and pins, cutting into parts, 3D Print Hub, Scale Master, Decimation Master, STL or 3MF, size in millimeters.


### scenario-zbrush-retopology-export

Use when a ZBrush sculpt, scan or AI-generated mesh must become production topology and files (ZRemesher and guides, the 2026 Retopo brush, reprojecting detail with Project All, rebuilding subdivision levels, UV Master or native unwrap, normal and displacement maps with Multi Map Exporter, GoZ, OBJ or FBX export, scale and axes, Decimation Master, "clean up an AI mesh in ZBrush"), or when detail is lost after ZRemesher, a map is upside down or an export arrives at the wrong size.


### scenario-zbrush-sculpting

Use when an agent sculpts organic forms in ZBrush 2026 (sculpt a head, bust or creature in ZBrush from a sphere, ZSpheres or primitives); when blocking primary and secondary forms, choosing DynaMesh, Sculptris Pro or subdivision levels, or setting ClayBuildup, Dam_Standard, Move or TrimDynamic; when using masks, polygroups, Morph Targets or layers; or when scripted strokes miss, do nothing, come out too strong or leave marks, or a re-DynaMesh does nothing or loses polygroups.


### scenario-zbrush-stylized

Use when sculpting a stylized or cartoon character, bust, collectible or toy in ZBrush (Overwatch, Fortnite, Disney look), judging shape language (S and C curves, parallel lines, 70/30, silhouette read at a distance), exaggerating proportions on purpose, keeping stylized planes crisp through subdivision, sculpting stylized hair (chunky clumps, curve tube strands, ClayPolish), or designing a figure for toy production (articulation, wall thickness, scale).


## Godot

Local family written 2026-10-28 from the author's Godot research (measurements on 4.7.2 and 4.8-beta1) and verified research; not an upstream pack and not live-tested as a whole. Latest stable 4.7.2; 4.8 in beta.


### [studio-godot-animation-import](../local/skills/game-engines/godot/studio-godot-animation-import/SKILL.md)

Use when a Blender or glTF/GLB asset must get into Godot 4.x intact: direct .blend import, glTF import settings, Advanced Import Settings, EditorScenePostImport scripts, custom normals or painted vertex colour arriving wrong, COLOR_0 or _CUSTOM attributes, LOD generation changing the mesh, skeleton and BoneMap or SkeletonProfileHumanoid retargeting, a shared skeleton and animation library, AnimationPlayer or AnimationTree setup, stepped or held-pose animation (Constant keys, INTERPOLATION_NEAREST), animation/fps bake grid, frame-accurate timing, hitbox method tracks firing late, hitstop, 2D sprite animation (Sprite2D, AnimatedSprite2D, SpriteFrames, discrete tracks, xfade doing nothing), root motion, skin_scale and BoneSpreader3D in 4.8, orthographic side-camera staging, 'animation looks smoothed', 'jump loop never plays', 'model imports rotated or the wrong size'. Does not own source-asset fixes in Blender (hand off to the Blender family) or shading, outlines and materials (studio-godot-rendering).


### [studio-godot-expert](../local/skills/game-engines/godot/studio-godot-expert/SKILL.md)

Use when an agent must drive Godot 4.x for any task and needs to pick how: headless CLI (godot --headless --import, --check-only, --script, --quit-after, --export-release), the user's running editor through an MCP server or editor plugin, or the GDScript language server (port 6005) and debug adapter (6006). Also for: detecting the project version, 'Identifier not declared' only in headless runs, a test run that exits 0 with nothing run, empty screenshots under --headless, rendering a Godot scene for review, hand-editing .tscn or .tres files, uid:// and ext_resource ids, choosing or trusting a Godot MCP server (read-only mode, exec tools, telemetry), Godot 3 code or tutorials on Godot 4, upgrade breaks from 4.4 to 4.8-beta, and whether an agent may file issues or PRs on godotengine. Routes to the five other studio-godot roles. It does not own the specialist work itself (rendering, animation-import, physics-vfx, platform-ui, gameplay-code).


### [studio-godot-gameplay-code](../local/skills/game-engines/godot/studio-godot-gameplay-code/SKILL.md)

Use when a Godot 4.x project needs GDScript or C# gameplay code: scene and node composition, signals and Callables, autoloads, Resources versus runtime state, groups, static typing, ':=' inference errors ('Cannot infer the type', 'inferred from a Variant'), input actions and InputMap, state machines, save and load (user://), _process versus _physics_process, frame-accurate or tick-locked timing, hitbox timing, @tool scripts, @export and @onready, 'Identifier not declared' only in headless runs, testing with GUT or GdUnit4 (exit codes, tests that pass without running, SceneRunner), linting with gdtoolkit (gdlint, gdformat), porting Godot 3 scripts to 4. It does not own physics simulation and particles (studio-godot-physics-vfx) or UI, touch and platform export (studio-godot-platform-ui).


### [studio-godot-physics-vfx](../local/skills/game-engines/godot/studio-godot-physics-vfx/SKILL.md)

Use when a Godot 4.x project needs physics or particle-effect work: Jolt vs GodotPhysics, collision layers and masks, CharacterBody3D vs RigidBody3D, SoftBody3D, physics tick rate, deterministic replay or a seekable timeline, GPUParticles3D vs CPUParticles3D, use_fixed_seed, request_particles_process, emit_particle not working, particle collision (HeightField, SDF, collider limits), goo, pus, blood or fluid sims, splatter, wet maps, Decal nodes as splats or weathering, 'physics step too slow', 'particles differ on replay' in Godot 4.x. It does not own shader-only effects (studio-godot-rendering) or gameplay rules (studio-godot-gameplay-code).


### [studio-godot-platform-ui](../local/skills/game-engines/godot/studio-godot-platform-ui/SKILL.md)

Use when a Godot 4.x project needs UI, input or platform delivery work: Control nodes, containers, anchors, Theme resources, safe areas, focus and 5-way or controller navigation, touch input (InputEventScreenTouch, InputEventScreenDrag, finger ownership, multitouch, pinch, MagnifyGesture, long press), duplicate events from mouse emulation, touch cancelled by backgrounding, Android or iOS or macOS export presets, target API level, 16 KiB page size, Xcode and signing handoffs, Web export (WebAssembly, WebGL 2, Compatibility renderer, single-thread), LG webOS TV IPK packaging, Magic Remote, Back key, suspend and resume, profiling on real devices in Godot 4.x. It does not own gameplay logic (studio-godot-gameplay-code) or rendering-cost diagnosis (studio-godot-rendering).


### [studio-godot-rendering](../local/skills/game-engines/godot/studio-godot-rendering/SKILL.md)

Use when a Godot 4.x project needs a renderer choice (Forward+, Mobile, Compatibility), spatial or canvas_item shaders, toon or cel two-tone lighting (DIFFUSE_TOON, custom light(), unshaded step shader, per-character light), outlines (inverted hull, next_pass, stencil Outline preset, depth/normal post-process), inner lines, ambient or shadow washing out the toon bands, Environment, tonemapping, glow, skin shaders (sss_mode_skin, NORMAL_MAP, clearcoat, F0), strand hair or fur in a MultiMesh, decals, lightning or electric-arc shaders, goggle or lens droplets, hint_screen_texture and transparency order, 2D depth tricks, 'my character looks flat/blotchy/black', 'strands render black', texture VRAM or import compression budgets. Does not own import settings, glTF/skeleton/animation work (studio-godot-animation-import) or particles and physics (studio-godot-physics-vfx).
