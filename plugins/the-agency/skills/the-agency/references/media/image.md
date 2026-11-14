# Image craft

What an image worker cannot guess. Process, handoffs and shared rules are in the [Media contract](../media.md). Scripted checks: `python scripts/media_check.py` with `preflight`, `probe`, `audio` and `job`. `probe --width --height` checks size.

## Decision order
1. Brief: purpose and destination, subject list, aspect and exact size, alpha, literal text strings, final count, who picks.
2. Engine and workflow: one engine per set, so the look cannot split. Record runtime, workflow, LoRA and strength.
3. Style: one frozen style block, plus one identity block per subject.
4. Dialect check, then preflight and a one-image canary after any engine update.
5. Batch with seeds fixed in the card, sorted by engine and LoRA so models do not swap. One retry, then skip and report. The operator runs the card's post scripts.
6. Scripted checks, then a reviewer who did not make the prompts reads at full size.
7. The owner picks and judges the look. Workers propose.

## Model for the job
- Fast turnaround sheets, many seeds: MOSS-Image with its 4-step LoRA. Do not mix that LoRA with 25 to 50 step settings; the output overcooks. Text is good on short strings and garbles long lines.
- Short readable on-image text, multi-reference edits, transparent output: Qwen-Image 2.1. The INT8 build has weak fingers, does not take character LoRAs, and ignores the negative prompt at CFG 1 (community reports). Local edit and alpha runs are unverified.
- Style exploration and LoRA portraits: Krea 2. Turbo is a testing tool, not the pick for maximum consistency across a final set.
- Photoreal prompt adherence: FLUX. It converges on one default face, and seeds do not diversify identity, so write identity out.
- Anime and cel: SDXL-family checkpoints with tags. Pixel sprites: a sprite LoRA, then a deterministic pixelize step.
- Texture on a mesh, tiling surfaces: a texture workflow or a CC0 library. AI-estimated maps are estimates to check.
- Sizes: multiples of 32 for Qwen-Image and 16 for Krea 2 and FLUX. Smaller canvases render faster when memory is tight.

## Prompt dialects
- Qwen-Image, Krea 2, MOSS-Image: natural sentences. No weight syntax such as `(word:1.3)`.
- Negative text only where the branch is live. Inert at CFG 1, absent in FLUX. Put the wanted state in the positive prompt: "exactly two arms".
- Tag models (NoobAI, WAI-Illustrious) want booru tags and have a real negative field.
- Quote literal text in double quotes. Final typography is better added in a compositor.
- Anatomy fixes go in the positive prompt: a four-armed figure needed "exactly two arms". "Feet together" welded the boots, so the second pass set the legs apart.

## Consistency
- Frozen style block, then per-subject identity block, then the scene. Final prompt is those three in that order.
- Fixed seed list in the card (for example four seeds). Same engine, same size across the set.
- Condition every image on the same anchor, not on its predecessor. Drift compounds down a chain. This is inference from published work.
- Colours are fixed in post. Hex codes in prompts drift: in a first pass one card in eight landed near its assigned accent, and "magenta" came back gold. Recolour with a script that fills from the corners and writes the exact value.
- A set scorer using embeddings is a report only. Its threshold is calibrated on the first accepted set and needs a model that must be present.

## Limits prompts cannot fix
- The format decides some things. A model that fills a sheet panel with a T-pose kept arm span at 0.86 to 0.93 of height whatever the prompt said. Change the layout or the model.
- Small design devices such as a smile, a mask seam or a glove size failed the same way. Test each on the canary and report it before the batch.

## Edits, in order of cost
1. New seed, or a targeted prompt change.
2. Prompted edit, with a mask: unedited areas drift without one.
3. Hand-paint a small flat fix.
Upscales blend with the source. One recorded pass, on 1080p video frames, gave 3.1x sharpness and invented plaster texture raw; a blend of about 35 percent enhanced output measured far better. Set the PSNR and sharpness band per job.

## What needs eyes
Scripts: `probe` for size and `job` for hashes. Project scripts, where they exist, for mode, alpha, count, not blank or flat, margins, colour samples, grayscale separation, person and face counts, upscale metrics. Eyes: limbs, fingers, hands, welded feet, views agreeing, design intent, text spelling, waxy skin, wrong objects, invented texture.
A reviewer reads every candidate at full size, all views. A contact sheet is a screening aid only. Agent viewers can downscale large images, so read crops of about 1,500 px at 100 percent for hands, faces, text and edges. Cut-outs: composite on black, white and mid grey; a halo shows on one of them. Tiling surfaces: view a 2x2 tile and the half-offset image. A first review that leaned on the contact sheet passed a broken design; a full-size read and the owner found it. A lane-scale strip cropped at a fixed third cut off a hand; crop from detected gaps.
Colour collisions show up only by sampling: a new "old gold" matched an existing character's mustard.
