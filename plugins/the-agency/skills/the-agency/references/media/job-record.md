# Media job record

One JSON file beside each deliverable, named `<deliverable>.job.json`, with one writer. `python scripts/media_check.py job <record>` checks it. Extra fields are allowed.

| Field | Meaning |
|---|---|
| `job_id`, `team`, `deliverable`, `project`, `created_at` | Identity. `team` is video, image, music, sfx, voice or mix |
| `parent_job` | The job this one serves, if any |
| `needs` | List of `{job_id, path, sha256}` this job consumed. A changed hash voids the job |
| `authority` | music, picture or vo |
| `clock` | `fps` as a fraction, `sample_rate`, `start_sample`, `end_sample`, whichever apply |
| `audio_policy` | For example silent plate, generated kept, external master |
| `loudness_target` | Integrated LUFS and true-peak ceiling, or null |
| `run` | `runtime`, `workflow_hash`, `model_files` with hashes, `seed`, `prompt_hash`, `started`, `ended`, `fresh_process`, `retry` (0 or 1), `failure` |
| `outputs` | List of `{path, sha256, bytes}`, empty until something is rendered. Relative paths resolve from the record's folder |
| `evidence` | List of `{level, check, command, result}` |
| `review` | `{status, human_receipt}` |

`review.status` is one of draft, ready, queued, running, rendered, validated, needs_review, approved, rejected, delivered. Automation may reach `validated`. `approved` and `delivered` need `human_receipt`: the path of the owner's note, or the chat date and words.

A project with its own stricter receipt format keeps it, and adds any of these fields it lacks.

## Loudness starting points

The brief names the target. These are proposals to confirm against the destination's delivery document.

| Destination | Starting point | Source |
|---|---|---|
| Film and broadcast | -23 LUFS, -1 dBTP | EBU R128 |
| US broadcast | -24 LKFS, -2 dBTP | ATSC A/85, secondary summaries |
| Streaming drama | -27 LKFS dialogue-gated, plus or minus 2 LU, -2 dBTP | One streamer's mix specification |
| Web video | -16 to -14 LUFS, true peak -1.5 to -1 dBTP | Past practice and secondary summaries, weakly documented |
| Games | -24 LUFS plus or minus 2 on consoles, -18 plus or minus 2 handheld, on the whole mix. A project's per-kind spec wins | Vendor guidance and an ITU report, secondary |
| Audiobook | RMS -23 to -18 dB, peak -3 dB, noise floor -60 dB | Forum summaries, secondary |
| Music streaming | See [music.md](music.md) | |

`media_check.py audio` measures programme loudness only. For a dialogue-gated target the owner confirms with a meter that supports it, and the sheet says so.
