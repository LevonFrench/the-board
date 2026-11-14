---
name: studio-godot-platform-ui
description: "Use when a Godot 4.x project needs UI, input or platform delivery work: Control nodes, containers, anchors, Theme resources, safe areas, focus and 5-way or controller navigation, touch input (InputEventScreenTouch, InputEventScreenDrag, finger ownership, multitouch, pinch, MagnifyGesture, long press), duplicate events from mouse emulation, touch cancelled by backgrounding, Android or iOS or macOS export presets, target API level, 16 KiB page size, Xcode and signing handoffs, Web export (WebAssembly, WebGL 2, Compatibility renderer, single-thread), LG webOS TV IPK packaging, Magic Remote, Back key, suspend and resume, profiling on real devices in Godot 4.x. It does not own gameplay logic (studio-godot-gameplay-code) or rendering-cost diagnosis (studio-godot-rendering)."
license: MIT
---

# Godot Platform and UI (platform-ui specialist)

This role owns the surface between the game and the device: Control-based UI, input from fingers, remotes and gamepads, and the export path for Android, iOS, macOS, web and LG webOS TV. Expert work here means a build that is judged on the target device, an input recognizer that survives interruption, and a package that matches the platform's current rules. Tags: [primary] is documented in the author's research from official pages; [proposed] is the author's own design contract; [inference] is the author's reasoning; [general] is not in the author's research and must be checked. Coverage gap: the author's research has almost nothing on Control layout and theming, so those parts are short and mostly [general].

## Stance (the expert delta)

- Touch is a contract, not a stream of events. Track fingers by index in a dictionary, lock roles at acquisition, and never silently replace a released finger with another. [proposed]
- An OS-cancelled touch never scores. Loss of focus, backgrounding, scene exit and orientation change clear captured IDs and pause, then require deliberate reacquisition. Do not wait for releases that may never arrive. [proposed]
- `_input` runs before GUI input. Acquire gameplay touches after GUI consumption, then make sure the recognizer still gets release and cancel when a finger leaves its target. Turn off mouse emulation in the gameplay path or actions fire twice. [primary]
- Drag `pressure` documents stylus pressure, not finger force. Derive squeeze from movement, in one coordinate space. Use viewport positions for UI and 3D mapping. [primary]
- A TV is not a touch device. Retail LG webOS needs Magic Remote pointer plus 5-way focus plus a controller path, and every action needs a remote equivalent. [primary]
- Each platform is its own target with its own gates. A desktop build or desktop Chrome proves little about a phone or a TV. Recheck store requirements at release because they change.
- Stay on stable for the baseline. Try a preview only in an isolated copy for a named benefit, and stop at any automatic migration prompt. [inference]

## Establish first

- Godot version from `config/features` in project.godot or `godot --version`. Export templates must match it exactly.
- Renderer per platform. Android and iOS use Mobile in the author's plan; web and webOS use Compatibility.
- Orientation (portrait or landscape), input devices (touch, mouse, remote, gamepad, keyboard), oldest supported device.
- `export_presets.cfg`, package or bundle identity, icons, and which build host is available. iOS and DMG packaging need macOS and Xcode.
- Which Control scenes exist, whether a Theme resource is shared, and how the project handles focus.
- Whether the work is account-bound (signing identities, store accounts, licences). This role prepares the build and leaves those operations to the owner.

## Workflow

1. Write the target matrix: platform, oldest device or firmware, renderer, input set, package type. Mark each cell tested or unverified.
2. UI layout: use container nodes and anchor presets rather than hand-placed rectangles, keep one Theme resource on the root Control, and set focus neighbours for controller and remote use. [docs]
3. Input: build one recognizer per gesture, fed by ScreenTouch and ScreenDrag, that outputs one normalized control state per simulation tick. A stationary pair keeps its state without new drag events. [proposed]
4. Give buttons, sliders and gesture contacts separate owners, and consume each event once. Keep mouse and keyboard as separate adapters for the same gameplay actions. [proposed]
5. Provide a one-finger or button alternative using the same normalized model, plus haptics-off and reduced-motion options. Vibration is optional feedback and Android needs the permission. [proposed]
6. Export per platform with matching templates. Android: SDK and JDK, ARM64, AAB through Gradle, permissions. iOS: Xcode build host, bundle identity, safe areas. macOS: Universal 2 or a deliberate narrower choice, ZIP over a raw folder. [primary]
7. Web and webOS: single-thread Web export first, WebAssembly plus WebGL 2 plus Compatibility. Keep all export filenames consistent. Test first audio playback, persistence and suspend and resume. [primary]
8. Profile on the real device after prolonged play and after standby. Record startup, frame pacing and memory.
9. For TV: handle Back (key 461 with `disableBackHistoryAPI=true` in single-page apps, `platformBack()` for exit), pointer, 5-way focus, and each intended gamepad. [primary]
10. Handle `visibilitychange`: cancel held input, stop unseen clocks and audio, require explicit resume. [primary]

## Numbers

- Android Google Play target API 36 for new apps and updates, as of the policy date cited 2026-10-02. This is not the minimum OS. [primary]
- Apple upload: Xcode 26 or newer with the iOS 26 SDK; a separate page lists an iOS 13 deployment floor. [primary, recheck]
- Android native libraries must be validated for 16 KiB pages. A desktop build does not show it. [primary]
- LG webOS TV Chromium: webOS TV 6.x 79, TV 22 87, TV 23 94, TV 24 108, TV 25 120, TV 26 132. [primary]
- LG web apps render at HD or FHD, never UHD. `requiredMemory` is a minimum, not a guarantee. [primary]
- Godot 4.8 dev6/dev7: mip-level texture streaming (PR 113429) supports Mobile and Forward+, excludes Compatibility, reduces residency not package size; its Metal coverage was untested. [primary, preview]
- No measured UI or input latency figures exist in the author's research. Latency and power are device measurements to take.

## Quality gates

Measurable in code:
- Export succeeds with matching templates; identity, version and icons are set; target API and ARM64 are as the matrix says.
- Native libraries pass the 16 KiB page check on Android.
- Synthetic ScreenTouch and ScreenDrag sequences drive the recognizer through: reversed contact order, one lift, a cancel, a third finger, crossing fingers. [docs: inject events with `Input.parse_input_event`, which also generates `_input` calls]
- A cancel and a focus loss both clear captured IDs and never produce a score.
- One input event produces one gameplay action (no mouse-emulation duplicate).
- Web export loads in a browser at the Chromium version of the oldest target TV, with zero console errors. A tiny WASM test does not stand in for the full engine.

Needs a render or play:
- Two real fingers on real phones, with thumb and index and with two thumbs, left-handed and small hands.
- Edge swipes, system gestures, home indicator region, background and resume, orientation change.
- Slider drag that continues outside its original rectangle.
- TV: pointer, 5-way focus, OK, Back, each gamepad, disconnect and reconnect, text at couch distance, standby.

## Common mistakes

- Assuming fingers are index 0 and 1 -> use a dictionary of active indices with explicit cancel and ignore rules.
- Testing multitouch with mouse emulation -> use a device; the mouse cannot make two touches.
- Reading `pressure` from ScreenDrag as finger force -> derive from movement.
- Mixing screen deltas and viewport positions -> pick one space per calculation and normalize.
- Using MagnifyGesture as authoritative gameplay -> it gives a scale factor and needs an Android setting; keep it to optional camera zoom. Disable pinch-zoom while a squeeze is active.
- Pixel thresholds for finger travel -> size travel relative to the safe area's short side and tune on real fingers.
- Claiming a 4K TV renders a 4K web app -> LG web apps are HD or FHD.
- Treating desktop Chrome as TV evidence -> test in the installed app environment.
- Letting Back use browser history on TV -> disable it for single-page apps and handle key 461.
- Threaded Web export on a TV first -> start with single-thread; threaded needs shared memory.
- Migrating to a 4.8 preview for generic touch support -> keep 4.7.2 unless a named feature needs it.
- Godot 3 names: `rect_min_size` is now `custom_minimum_size`, `margin_*` became offsets, `add_color_override` became `add_theme_color_override`, and the HTML5 export is now called Web. [docs]
- Fixed hit rectangles on custom HUD after adopting new touch TabBar or PopupMenu -> those controls do not convert custom hit areas.

## Handoffs

- studio-godot-gameplay-code receives the normalized control state and the cancel contract, and owns what the squeeze or hold does in the game.
- studio-godot-rendering receives a device capture and frame data when frame time is the problem, and the renderer matrix per platform. This role keeps platform lifecycle and export.
- studio-godot-physics-vfx receives the fixed-step and replay constraints from the touch contract, and the web and Compatibility limits on compute, CompositorEffect and `emit_particle`.
- Blender takes source-asset fixes for icons, textures and meshes that fail platform limits.
- The owner takes signing, store accounts, notarization and LG submission.

## Version notes

- 4.7.2 is the stable baseline in the author's research. Godot web export docs at 4.7 require WebAssembly and WebGL 2 with Compatibility.
- 4.8-dev1: TextEdit and CodeEdit touch support; joypad touchpad support; Android CPU name detection; ASTC 6x6 and high-quality profiles (PR #115003); SPM for Apple embedded plugins; export-options filtering.
- 4.8-dev2: joypads on unfocused windows ignored by default in new projects only; enforced single main thread (PR #121161).
- 4.8-dev3: Android large-screen orientation; TabBar sizing strategies; visionOS made modular.
- 4.8-dev4: no 4.8 class reference was published at the time (2026-09-01); API names come from merged XML and may change. Scenes saved by 4.8-dev4 may not open in 4.7.2.
- 4.8-dev6: long-press events on iOS and Android (PR 122865); fixes for earlier Metal-startup and Android-upload regressions. 4.8-dev7 (2026-09-29) added mobile AccessKit and touch TabBar and PopupMenu use. No beta existed as of 2026-10-02.
- webOS: Flutter support is limited to TV 26 and later and is a separate SDK, not a Godot route. webOS OSE is a different target.

## References

Written from the author's research notes, which are not included.

