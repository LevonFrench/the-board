# Foley and SFX craft

Load for the foley and SFX team, after the [Media contract](../media.md). Job fields are in [job-record.md](job-record.md). Scripted checks: `python scripts/media_check.py` with `preflight`, `probe`, `audio` and `job`. No role here can hear, and sampled frames cannot prove motion. Anything marked "ear" goes to the owner.

## Two sources
- **MiniMax H3 audio.** H3 is one joint video and audio model with its own audio VAE (32 kHz stereo). Audio and picture are denoised together, so sync to that picture is free. The model card lists text, first-last-frame and reference modes. It has no audio-only mode and no video-to-audio mode, and scoring an existing silent clip is not a documented feature. Turbo LoRA audio is "slightly lower" quality per the ComfyUI docs, and speech is weakest at 8 steps and usable from 12. All verified local runs are turbo, so test a clip at 12 or more steps before relying on H3 audio. Content is band-limited near 16 kHz (inference), and taking it from the mp4 adds lossy AAC. No listening record says H3 audio is usable as foley, so the owner hears one clip first.
- **Stable Audio 3** (44.1 kHz stereo; Medium to about 380 s). Text to audio, audio to audio, inpainting and continuation. No picture input, so timing comes only from the cue sheet and the edit. Prompt: core source, action, production character, `TrackType: SFX`, short durations. Post-trained checkpoints use 8 steps and cfg 1.

## Choosing per cue
Use H3's own audio only for cues inside an H3 clip you keep unretimed, where the sound must lock to what that picture does. Use Stable Audio for everything that must be exact, isolated, reusable, retimed, looped, varied, or attached to picture H3 did not make.
- H3 wins: picture is H3-made and uncut, the sound is diegetic and inseparable from the motion (a splash, a door, the shot's own crowd murmur), and a few frames of drift are tolerable.
- Stable Audio wins: the cue is reused across shots or in a game; the clip is retimed, cut or speed-changed; the picture is silent, from another model or live action; the cue needs variations, a loop, an exact length or mono; H3 audio is muddy or artifact-ridden; or the pack was rendered silent.
- Combine: keep H3 audio as a low glue layer, about 0.35 gain (the value one shipped mix used), and put Stable Audio hits on top at the hard sync points. Drop the glue layer if it fights the music.
- Speech does not belong here. Spoken lines go to the voice team.
- Audio can be lost at a promotion or copy step; one raw promotion stripped it. Run `probe` for the audio stream after every copy, re-mux and promotion. Projects differ on `audio_policy` (some reject a clip with audio, some reject one without), so the brief names it.

## Spotting
- Watch frame strips of the locked cut. Write one cue per row: frame or timecode, subject, sound, class, duration, hard or loose sync, source and reason, variations, loop or one-shot. Picture change after lock voids the moved cues.
- Foley classes: footsteps, props, and cloth as its own pass. Crowds get only the extras you notice. Other classes: event with tail, ambience bed, loop, stinger, speech.
- Motion pacing, weight and material need the owner's eyes and ears; frame strips cannot show them.

## Generating
- 4 to 8 takes per cue, seeds recorded, batch size fixed (solo and batched renders of one seed correlate only about 0.97). Beds render long.
- One-shots came out panned and moving. Steer with "centered, mono, dry studio recording" and a negative prompt. Leave the downmix to the edit.
- Without flash-attn, Medium can emit static. Score takes for noise-like flatness, and the owner hears the first takes of a run. The text encoder may need a network fetch; four records failed offline, so confirm it is cached before an offline run. `preflight` does not check this.
- One GPU job at a time: finish the H3 job and unload before the Stable Audio batch. Only the Render operator submits.

## Conform and layer
- Trim to onset (-30 dB envelope, 4 ms pre-roll) with fades; high-pass at 25 to 30 Hz; loops of unrelated sound get an equal-power crossfade, and joins of the same material an equal-gain one.
- Layer one bed, 0 to 2 mid layers, accents on top. Keep each layer recoverable. Music is the timing authority when it exists.
- Dry cues need a space. Per scene, list the room, the shot scale and the cues for the owner to treat in their audio editor, and report the stems as dry. ffmpeg cannot finish this. Wide shots usually want less level and less top end.
- Hidden speech, singing or melody can sit in a take. A person must hear the full untrimmed take. Trimming hides it.

## Sync and levels
- EBU R37 allows audio +40 ms early to -60 ms late; BT.1359 detectability is about 45 ms early and 125 ms late (secondary sources). One frame is 1000 / fps ms (41.7 ms at 24 fps). Flag a hard-sync cue more than 1 frame early or 2 late (inference).
- Targets are for the final mix, which Mix and delivery owns, and the brief names one. Starting points are in [job-record.md](job-record.md).
- Working loop checks from one project, not standards, and needing a project script: join step under the file's 99.9th-percentile step, edge step under 3 dB, passes after ten tiled repeats, DC near zero, and a mono-fold test. Impact attack under about 60 ms.

## Cost is listening
One run made 1,460 takes in 10 minutes of GPU. At 5 to 10 s of listening per take that is 2 to 4 hours (an estimate; no curation was timed). Plan curation: rank by script, cap takes per cue, and give the owner a shortlist, not the batch.
