# Video craft

What a video worker cannot guess. Process, handoffs and shared rules are in the [Media contract](../media.md). Scripted checks: `python scripts/media_check.py` with `preflight`, `probe`, `audio` and `job`.

## Decision order
1. Brief from the owner: purpose, delivery size and rate, total length, audio authority, source stills, cloud permission (default none). The owner's go covers one queue and names its shots, a frame count and an hour cap.
2. Shot list: one purpose, one action, entry and exit state, camera, legal frame count.
3. Look: anchors are reviewed before any motion render.
4. Draft one canary shot in the cheapest lane that answers the question. Record seed, graph and model names.
5. Final: step count, size, continuation, optional detail pass.
6. Scripted checks, then a reviewer who did not render.
7. Encode: conform to the delivery rate, trim inside the filter chain, mux the master audio once, hash, write the job record. Spec: H.264, yuv420p, limited range, the BT.709 matrix applied in the scaler as well as tagged (`scale=out_color_matrix=bt709:out_range=tv,format=yuv420p`), faststart. In a local test ffmpeg left to itself made RGB input 4:4:4 and moved a red from 192,32,32 to 205,47,28 when read as BT.709. Name the crop or pad from the native canvas to the delivery aspect. The owner confirms hue on a phone and a monitor.

## Frame grid and canvas
- MiniMax H3 lengths sit on a 5 + 17k frame grid at 24 fps, with a documented range of about 124 to 362 frames (4 to 15 s). 22, 39, 56, 73, 90 and 107 are on the grid but below that range and unproven. Round up with `5 + 17*ceil((ceil(sec*24) - 5)/17)`. A 5 s clip is 124 frames. Check with `probe --frame-grid 17,5`.
- Native canvas is 1344x768, sizes in multiples of 32. A 1.0 MP target overshoots to 1376x768. Larger canvases render slower and add no detail. Small canvases have been used for icon and pack work, so check the size against the brief.
- Musical length is stored apart from render length. A 73-frame clip is 3.04 s, not eight beats at 124 BPM (3.87 s).
- H3 is native 24 fps. Prefer 24 or 23.976, and name the method for any other rate. 23.976 is a 0.1 percent retime, so say whether the audio takes the same factor or the drift is accepted. 25 or 30 by frame repeat and drop has uneven cadence, so tell the owner. Do not interpolate faces without the owner's go.
- Extension nodes want constant 24 fps input, bridge contexts of 39 + 51k frames and targets of 5 + 17k. Documented upstream, not verified by a run.
- One sprite-pipeline note blamed a 5-frame render for a nearly static result and suggested 22 frames as a floor. Nothing accepted at that length is recorded, so test a short move on the canary.

## Prompts
- Plain sentences in shot-list order: subject, the one action, camera, entry and exit state. Say what appears.
- There is no negative branch. A ban list names the unwanted thing and invites it. A `Limits:` block acts as soft guidance only.
- Text, logos and exact geometry go to a compositor, never to the model.
- Never prompt a sync the model cannot hear. In one overnight batch no song was connected to the model, so its audio had nothing to match.

## Long clips, modes, anchors
- Split long clips. Two clips of about 180 frames are expected to cost less than one of 360 (a projection; no local pair was timed). The runtime's own limits override this number.
- Sort the queue by mode: text-to-video and first/last-frame first, reference-to-video after. Model swaps cost more than renders, and one paid batch lost hours to them.
- First frame: the anchor is stretched to the canvas, not letterboxed. Cut it to the canvas aspect first (community guide, treat as a cheap rule).
- Second anchor: text-to-image second anchors failed continuity review 3 times in 4, so one project moved to the last frame of the first clip (no outcome recorded yet).
- Park a shot the image model cannot draw after a few tries (a camera seen from behind took five). The owner decides.

## Audio
- Plates are silent. Music sync is real only when the master audio is muxed once onto the finished picture. Check with `audio` and `probe --audio forbidden|required`.
- Raw promotion has stripped audio streams, and a pull has overwritten re-muxed files. Hash after each hop.

## Traps
- ffmpeg: `-frames:v` truncated a filter-expanded plate to 180 of 450 frames. Hashing decoded frames cannot show duplicates; use `mpdecimate`. `tile` with many inputs crashed on Windows, so build the contact sheet last and small.
- `execution_cached` true means sampling was skipped. A fast canary can be cached, so read it before trusting a timing.
- Time is whatever the receipt says. Slow healthy renders were killed as hung three times. Judge stalls by log progress and GPU use.
- Reused work must match on content hash. Matching on shot id rendered 27 shots from old prompts.
- Detail pass: one raw pass gave 3.1x sharpness, invented plaster texture and a 1.59x flicker proxy. A blend of about 35 percent enhanced output over the source measured far better (1.25x flicker, 37.7 dB). Start from the blend. The notes disagree on its direction, so check it on the job.

## Acceptance
Exact: size, rate, frame count on the grid, duration within one frame of frames/rate, full decode exits 0, audio stream as the contract says, sha256 on the record.
Proposals, calibrate on the project's first accepted clips: no freeze of 0.5 s or more in a motion shot; unique-frame ratio of 0.9 or more outside planned holds; flicker proxy at most 1.3x and PSNR at least 37 dB for a finishing pass; no frame-difference spike at chunk or continuation seams; mean luma and chroma compared across 5 frames either side of each cut and first against last frame of a chained clip, with the worst three on the owner's sheet. Grading is the owner's. A static-clip floor is not established; a clean flicker score can come from a still clip.
Type on screen: at most 3 flashes in a second, contrast 4.5:1, inside the title-safe area.
Needs eyes: identity, anatomy, one action finished, camera as prompted, no boiling texture. Sampled frames cannot prove motion. A decode pass is not editorial acceptance. In one frame-sampled review of 227 turbo clips, 171 went back.
