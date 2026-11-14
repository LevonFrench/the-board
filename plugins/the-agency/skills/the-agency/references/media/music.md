# Music craft

Load for the music team, after the [Media contract](../media.md). Job fields are in [job-record.md](job-record.md). Scripted checks: `python scripts/media_check.py` with `preflight`, `probe`, `audio` and `job`. No role here can hear. Anything marked "ear" goes to the owner on a short listening sheet.

## The model
- Stable Audio 3 is a family of latent diffusion models with a 44.1 kHz stereo output. Medium (1.4B) needs a CUDA GPU and makes up to about 380 s. Small-Music (433M) makes up to 120 s and can run on CPU. Large is API-only. Local docs disagree on Medium's limit (380 s or about 4.75 min); the model config says 380.4 s, so use 380 s.
- Post-trained checkpoints use 8 steps and cfg 1. Base checkpoints, meant for LoRA training, want about 50 steps.
- Conditioning is text and a total duration. Nothing else. There is no BPM input and no key input, so tempo and key are prompt words and no source measured how well the model obeys them.
- The model is instrumental only. A brief that needs sung vocals or lyrics is out of scope for this team. Stop and report it to the parent.
- Prompt: genre, instruments, mood, then tempo as prose ("120 BPM"). Add `TrackType: Music, VocalType: Instrumental`, or `TrackType: Instrument` for a solo part. The guide defines no BPM tag. The text encoder reads at most 256 tokens. Vocal-like textures can still appear, so listen for them.
- Modes: text to audio, audio to audio (`init_noise_level`), inpainting (one or several regions) and causal continuation. For continuation and inpainting, audio context matters more than the prompt. Try a continuation or a large mask before rewording.

## Decision order
1. Brief: destination, length, loop or not, instrumental, sample rate, bit depth, loudness target, whether stems are needed.
2. Reference, if supplied: `audio` gives loudness and peaks, not tempo or key. A project detector may offer candidates. The owner confirms by ear, or supplies tempo, downbeat and sections.
3. One tempo and one key. Pick a tempo that divides cleanly into the target: bars x 4 x 60 / BPM = seconds. Generate padded (about 2 s extra) and trim to the bar grid. The padding is a cut margin, not a promise that bar 1 starts at sample 0. Where a project script can, measure each take's tempo and downbeat offset, mark them unconfirmed and cut on measured downbeats near the nominal grid. The owner hears the first join or seam before the rest are built.
4. Generate several seeds. 5. Script screen, then the owner auditions what is left. 6. Arrange. 7. Stems. 8. Mix. 9. Master. 10. Scripted QC, then the owner's ear.

## Tempo and key
- Half-time against full-time is often not an error. Fast bass music is tagged both ways, so ask which one the brief means before calling a mismatch.
- Detectors can be confidently wrong. In one local test a detector got 8 of 16 synthetic tracks within 1 BPM at confidence above 0.98 and read minor tracks as their relative major, though the test progression may itself sit there. Report detector output as unconfirmed until the owner confirms by ear.
- A length-on-grid check (length x BPM / 60 within 0.03 beat of a multiple of 4 beats; a working tolerance, not a standard) says nothing about what the audio plays. Chords named in a prompt are text, not verified.

## What generation cannot do
Guarantee tempo or key. Plan an arranged song with sections. Sing. Give true stems. Guarantee a loop point. Meet a loudness or true-peak spec. Reproduce a take across batch sizes. Judge its own quality. A secondary review reports that rhythmic genres (drum and bass named) flatten toward average, that one prompt across seeds gives near-identical melodies, and that song structure is weaker than in competing tools. Treat that as one reviewer's view, not a measurement.

## Stems
- The model has no stem output. Route 1: generate each part alone with `TrackType: Instrument` at the same tempo and key. Parts drift in groove and key (inference).
- Route 2: separate a finished mix with a source-separation model such as Demucs. Separated stems carry artifacts. A separator not in the capability snapshot is a gap to report; installing one needs the owner's words.
- Sections are separate generations. Harmony carries across them only if continuation conditions it.

## Reproducibility
- Same seed and same batch size gives near-identical audio (correlation 0.99998). Solo against batched gives 0.97. Keep batch size fixed and record it with the seed.
- Pin one checkpoint hash for the job and record it. One project's records held two different Medium hashes.
- Without flash-attn, Medium can emit static. Takes were produced, but no listening record says they are free of static, so the first takes of every run go to the owner's ear.
- The text encoder may need a network fetch. A run offline failed, so confirm it is cached before an offline run. `preflight` does not check this.

## Delivery
- Loudness is a brief field. Streaming is commonly -14 LUFS integrated. Spotify advises true peak below -2 dBTP when integrated loudness is above -14 LUFS, and its Loud setting uses -11 with a -1 limiter ceiling. Apple at -16 and YouTube at -14 are widely quoted and weakly documented. No primary game-music target was found: the brief names one. Other starting points are in [job-record.md](job-record.md).
- A generated take is a draft, not a master. One past review found a 7.8 LU spread and a +0.4 dBTP file because no target was named.
- Converting to 16 bit: triangular dither, applied last, after any resample, and recorded. ffmpeg does not dither unless told (`aresample=dither_method=triangular`): in a local test a tone near -100 dBFS went to digital silence without it, and triangular dither kept it.
- The model writes 44.1 kHz. Picture work is often 48 kHz. Resample once, in float, before the final bit reduction, at the rate named in the brief, and recompute bar positions in samples afterwards.

## Ears and numbers
Script: `audio` with `--lufs`, `--lufs-tol`, `--true-peak-max`, `--max-head-silence`, `--max-tail-silence`, which also reports rate and sample count; `job` for the record. `probe` needs a video stream. Ear: groove and swing, felt tempo, harmony clashes, melodic interest, warble and smeared transients, static, loop seam, section flow, mood against the brief, any vocal-like texture. Workers do not approve; the owner does.
