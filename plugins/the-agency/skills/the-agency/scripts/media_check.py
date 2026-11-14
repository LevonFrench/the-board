"""Read-only structural checks for the Media division: GPU and queue state, video, audio, job records and runtime sheets.

Each subcommand prints one JSON object with ok, failures and its measurements. Exit 0 when ok, 1 when a check failed,
2 when a tool or file is missing or the usage is bad. Calls ffmpeg, ffprobe and nvidia-smi with argument lists, never
a shell, and starts, stops and submits nothing. The only network use is an optional GET to a local ComfyUI queue.
This proves structure only: it cannot show that anything sounds or looks good. That judgement belongs to a person.
"""
import argparse
import ctypes
import hashlib
import json
import math
import re
import subprocess
import sys
import urllib.error
import urllib.request
from fractions import Fraction
from pathlib import Path
from urllib.parse import urlparse

TIMEOUT = 600
CHUNK = 1 << 20
TEAMS = ("video", "image", "music", "sfx", "voice", "mix")
STATUSES = ("draft", "ready", "queued", "running", "rendered", "validated", "needs_review", "approved", "rejected", "delivered")
NOTHING_MADE_YET = ("draft", "ready", "queued", "running")
LOG_LINE = re.compile(r"^\[([^\]@]+?) @ [0-9a-fA-F]+\] (.*)$")


class CheckError(Exception):
    """A needed tool or file is missing, or the request cannot be made: exit 2, not a failed check."""


def run(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=TIMEOUT, check=False)
    except FileNotFoundError as error:
        raise CheckError(f"{cmd[0]} not found on PATH") from error
    except subprocess.TimeoutExpired as error:
        raise CheckError(f"{cmd[0]} timed out") from error


def number(text):
    """A float from ffmpeg text; None for n/a and for inf or nan, which are not usable measurements."""
    try:
        value = float(text)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def need_file(path):
    if not Path(path).is_file():
        raise CheckError(f"File not found: {path}")


def sha256_of(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def finish(report):
    report["ok"] = not report["failures"]
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["ok"] else 1


def filter_log(stderr):
    """ffmpeg's log as {filter_name: [text, ...]}, e.g. astats lines, in order. Index suffixes are dropped."""
    out = {}
    for line in stderr.splitlines():
        match = LOG_LINE.match(line)
        if match:
            out.setdefault(re.sub(r"^Parsed_|_\d+$", "", match.group(1)), []).append(match.group(2))
    return out


def ffprobe(path):
    done = run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)])
    if done.returncode:
        raise CheckError(f"ffprobe could not read {path}: {done.stderr.strip()[:200]}")
    return json.loads(done.stdout)


def first_stream(info, kind):
    return next((s for s in info.get("streams", []) if s.get("codec_type") == kind), None)


def parse_gpu(text):
    """nvidia-smi csv rows (memory.used, memory.total, utilization.gpu); [N/A] becomes None."""
    rows = []
    for line in text.strip().splitlines():
        used, total, util = ([number(part.strip().strip("[]")) for part in line.split(",")] + [None] * 3)[:3]
        rows.append({"used_mib": used, "total_mib": total, "util_percent": util})
    return rows


def parse_apps(text):
    """nvidia-smi compute app rows (process_name, used_memory). Names may hold commas, so split from the right."""
    apps = []
    for line in text.strip().splitlines():
        name, _, mem = line.rpartition(",")
        apps.append({"name": name.strip(), "used_mib": number(mem.strip().strip("[]"))})
    return apps


def free_ram_gib():
    """(GiB or None, note). Windows uses GlobalMemoryStatusEx, Linux /proc/meminfo."""
    if sys.platform == "win32":
        class Status(ctypes.Structure):
            _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong)] + [(n, ctypes.c_ulonglong) for n in
                       ("phys_total", "phys_free", "page_total", "page_free", "virt_total", "virt_free", "ext_free")]
        status = Status()
        status.length = ctypes.sizeof(status)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return round(status.phys_free / 2**30, 2), None
        return None, "GlobalMemoryStatusEx failed"
    try:
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            if line.startswith("MemAvailable:"):
                return round(int(line.split()[1]) / 2**20, 2), None
    except OSError:
        pass
    return None, "free RAM is not readable on this platform"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def check_local(url):
    parts = urlparse(url)
    if parts.scheme not in ("http", "https") or parts.hostname not in ("127.0.0.1", "localhost"):
        raise CheckError(f"Only a 127.0.0.1 or localhost ComfyUI URL is read: {url}")


def comfy_queue(url):
    """GET <url>/queue on a local server only. Redirects and proxies are off so the request cannot leave this machine."""
    check_local(url)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect)
    try:
        with opener.open(url.rstrip("/") + "/queue", timeout=10) as response:
            return json.loads(response.read().decode("utf-8", errors="replace"))
    except (urllib.error.URLError, OSError, ValueError) as error:
        raise CheckError(f"ComfyUI queue not readable at {url}: {error}") from error


def cmd_preflight(args):
    failures = []
    report = {"failures": failures}
    if args.comfy:
        check_local(args.comfy)
    report["gpu"] = report["gpu_processes"] = None
    if not args.no_gpu:
        base = ["nvidia-smi", "--format=csv,noheader,nounits"]
        gpu = run(base[:1] + ["--query-gpu=memory.used,memory.total,utilization.gpu"] + base[1:])
        apps = run(base[:1] + ["--query-compute-apps=process_name,used_memory"] + base[1:])
        if gpu.returncode:
            raise CheckError(f"nvidia-smi failed: {gpu.stderr.strip()[:200]}")
        report["gpu"], report["gpu_processes"] = parse_gpu(gpu.stdout), parse_apps(apps.stdout)
        card = report["gpu"][0] if report["gpu"] else {}
        free = card["total_mib"] - card["used_mib"] if card.get("total_mib") is not None and card.get("used_mib") is not None else None
        report["free_vram_mib"] = free
        if args.min_free_vram_mib and (free is None or free < args.min_free_vram_mib):
            failures.append(f"Free VRAM {free} MiB is below the {args.min_free_vram_mib} MiB needed")
    report["free_ram_gib"], report["ram_note"] = free_ram_gib()
    if args.min_free_ram_gib and (report["free_ram_gib"] is None or report["free_ram_gib"] < args.min_free_ram_gib):
        failures.append(f"Free RAM {report['free_ram_gib']} GiB is below the {args.min_free_ram_gib} GiB needed")
    if args.comfy:
        queue = comfy_queue(args.comfy)
        report["queue_running"], report["queue_pending"] = len(queue.get("queue_running", [])), len(queue.get("queue_pending", []))
        if report["queue_running"] or report["queue_pending"]:
            failures.append(f"ComfyUI queue is not empty: {report['queue_running']} running, {report['queue_pending']} pending")
    return finish(report)


def frame_count(path, video):
    """nb_frames when the container states it, otherwise a decoded count from ffprobe -count_frames."""
    if str(video.get("nb_frames", "")).isdigit():
        return int(video["nb_frames"]), "nb_frames"
    done = run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries", "stream=nb_read_frames", "-of", "json", str(path)])
    counted = (json.loads(done.stdout or "{}").get("streams") or [{}])[0].get("nb_read_frames", "")
    return (int(counted), "counted") if str(counted).isdigit() else (None, "unknown")


def intervals(log, total):
    """Freeze and black intervals from filter log lines; an interval still open at the end runs to the end of the clip."""
    found = {"freeze": [], "black": []}
    start = None
    for text in log.get("freezedetect", []):
        key, _, value = text.partition(": ")
        if key.endswith("freeze_start"):
            start = number(value)
        elif key.endswith("freeze_end") and start is not None and number(value) is not None:
            found["freeze"].append({"start": start, "end": number(value)})
            start = None
    if start is not None and total:
        found["freeze"].append({"start": start, "end": total})
    merged = []
    for span in found["freeze"]:  # a keyframe can split one still shot in two; touching spans are one freeze
        if merged and span["start"] - merged[-1]["end"] <= 0.05:
            merged[-1]["end"] = span["end"]
        else:
            merged.append(span)
    found["freeze"] = merged
    for text in log.get("blackdetect", []):
        match = re.search(r"black_start:([\d.]+) black_end:([\d.]+)", text)
        if match:
            found["black"].append({"start": float(match.group(1)), "end": float(match.group(2))})
    return found


def cmd_probe(args):
    need_file(args.file)
    failures, info = [], ffprobe(args.file)
    video, audio = first_stream(info, "video"), first_stream(info, "audio")
    report = {"failures": failures, "format": info.get("format", {}), "streams": info.get("streams", [])}
    if video is None:
        failures.append("No video stream")
    else:
        rate = video.get("avg_frame_rate") if video.get("avg_frame_rate") not in (None, "0/0") else video.get("r_frame_rate")
        fps = Fraction(rate) if rate and not rate.endswith("/0") else None
        fps_text = f"{fps.numerator}/{fps.denominator}" if fps else None
        frames, how = frame_count(args.file, video) if (args.frames is not None or args.frame_grid or args.defects) else (None, None)
        report.update(fps=fps_text, frames=frames, frames_from=how, width=video.get("width"), height=video.get("height"))
        if args.fps and fps != Fraction(args.fps):
            failures.append(f"fps is {fps_text}, expected {args.fps}")
        if args.frames is not None and frames != args.frames:
            failures.append(f"frame count is {frames}, expected {args.frames}")
        if args.frame_grid:
            step, offset = (int(part) for part in args.frame_grid.split(","))
            if frames is None or frames < offset or (frames - offset) % step:
                failures.append(f"frame count {frames} is not {offset} + k*{step}")
        for name, want in (("width", args.width), ("height", args.height)):
            if want is not None and video.get(name) != want:
                failures.append(f"{name} is {video.get(name)}, expected {want}")
        durations = [number(s.get("duration")) for s in (video, audio) if s]
        if audio and fps and None not in durations and abs(durations[0] - durations[1]) > float(1 / fps):
            failures.append(f"Audio and video durations differ by {abs(durations[0] - durations[1]):.3f} s, more than one frame")
    if args.audio == "required" and audio is None:
        failures.append("Audio stream required but absent")
    if args.audio == "forbidden" and audio is not None:
        failures.append("Audio stream present but forbidden")
    if not args.no_decode:
        done = run(["ffmpeg", "-v", "error", "-xerror", "-nostdin", "-i", str(args.file), "-f", "null", "-"])
        report["decode_errors"] = done.stderr.strip().splitlines()[:10]
        if done.returncode or done.stderr.strip():
            failures.append("Full decode reported errors: " + (done.stderr.strip().splitlines() or [f"exit {done.returncode}"])[0][:200])
    if args.defects and video is not None:
        total = number(video.get("duration")) or number(info.get("format", {}).get("duration"))
        done = run(["ffmpeg", "-hide_banner", "-nostats", "-nostdin", "-i", str(args.file), "-map", "0:v:0", "-an", "-vf",
                    "freezedetect=d=0.2,blackdetect=d=0.1,mpdecimate", "-f", "null", "-"])
        found = intervals(filter_log(done.stderr), total)
        kept = re.findall(r"frame=\s*(\d+)", done.stderr)
        report.update(freeze=found["freeze"], black=found["black"],
                      duplicate_ratio=round(1 - int(kept[-1]) / report["frames"], 4) if kept and report.get("frames") else None)
        for kind, limit in (("freeze", args.max_freeze), ("black", args.max_black)):
            longest = max((i["end"] - i["start"] for i in found[kind]), default=0)
            if limit is not None and longest > limit:
                failures.append(f"Longest {kind} interval is {longest:.2f} s, over {limit} s")
    return finish(report)


def parse_loudness(stderr):
    """Integrated loudness, LRA and true peak from the ebur128 summary block at the end of the log."""
    summary = stderr[stderr.rfind("Summary:"):] if "Summary:" in stderr else ""
    pick = lambda label: number((re.search(rf"^\s*{label}:\s*(\S+)", summary, re.M) or [None, None])[1])
    return {"integrated_lufs": pick("I"), "lra_lu": pick("LRA"), "true_peak_dbfs": pick("Peak")}


def parse_astats(lines):
    """Sample peak, DC offset, peak count and samples per channel from the Overall block of astats."""
    block = lines[len(lines) - lines[::-1].index("Overall"):] if "Overall" in lines else []
    got = {key.strip(): value.strip() for key, _, value in (line.partition(":") for line in block)}
    peak = number(got.get("Peak level dB"))
    return {"sample_peak_dbfs": peak, "dc_offset": number(got.get("DC offset")),
            "clipped_samples": int(number(got.get("Peak count")) or 0) if peak is not None and peak >= -0.01 else 0,
            "samples_per_channel": int(number(got.get("Number of samples")) or 0) or None, "peak_is_silent": "Peak level dB" in got and peak is None}


def parse_silence(stderr, total):
    """(start, end) pairs from silencedetect; a start with no end runs to the end of the file."""
    spans, start = [], None
    for text in filter_log(stderr).get("silencedetect", []):
        value = number(text.partition(": ")[2].split(" ")[0])
        if text.startswith("silence_start") and value is not None:
            start = value
        elif text.startswith("silence_end") and start is not None and value is not None:
            spans.append((start, value))
            start = None
    return spans + ([(start, total)] if start is not None and total else [])


def cmd_audio(args):
    need_file(args.file)
    failures, info = [], ffprobe(args.file)
    audio = first_stream(info, "audio")
    report = {"failures": failures}
    if audio is None:
        failures.append("No audio stream")
        return finish(report)
    total = number(audio.get("duration")) or number(info.get("format", {}).get("duration"))
    done = run(["ffmpeg", "-hide_banner", "-nostats", "-nostdin", "-i", str(args.file), "-vn", "-map", "0:a:0", "-af",
                "ebur128=peak=true,astats,silencedetect=noise=-60dB:d=0.05", "-f", "null", "-"])
    measured, stats = parse_loudness(done.stderr), parse_astats(filter_log(done.stderr).get("astats", []))
    spans = parse_silence(done.stderr, total)
    head = next((end for start, end in spans if start <= 0.001), 0.0)
    tail = next((total - start for start, end in spans if total and end >= total - 0.01), 0.0)
    report.update(measured, sample_rate=int(audio.get("sample_rate", 0)), channels=audio.get("channels"), duration=total,
                  samples=stats.pop("samples_per_channel"), head_silence_s=round(head, 3), tail_silence_s=round(tail, 3),
                  longest_gap_s=round(max((end - start for start, end in spans), default=0), 3), **stats)
    del report["peak_is_silent"]
    if done.returncode:
        failures.append("ffmpeg could not analyse the audio: " + done.stderr.strip().splitlines()[-1][:200])
    elif measured["integrated_lufs"] is None or measured["true_peak_dbfs"] is None and not stats["peak_is_silent"]:
        failures.append("Loudness is not finite")
    if stats["peak_is_silent"] or measured["true_peak_dbfs"] is None or (total and any(s <= 0.001 and e >= total - 0.01 for s, e in spans)):
        failures.append("Audio is entirely silent")
    if args.lufs is not None and measured["integrated_lufs"] is not None and abs(measured["integrated_lufs"] - args.lufs) > args.lufs_tol:
        failures.append(f"Integrated loudness {measured['integrated_lufs']} LUFS is outside {args.lufs} +/- {args.lufs_tol}")
    if args.true_peak_max is not None and (measured["true_peak_dbfs"] or -math.inf) > args.true_peak_max:
        failures.append(f"True peak {measured['true_peak_dbfs']} dBFS is over {args.true_peak_max}")
    for label, value, limit in (("Head", head, args.max_head_silence), ("Tail", tail, args.max_tail_silence)):
        if limit is not None and value > limit:
            failures.append(f"{label} silence {value:.3f} s is over {limit} s")
    return finish(report)


def cmd_job(args):
    need_file(args.record)
    failures, folder = [], Path(args.record).resolve().parent
    report = {"failures": failures}
    try:
        record = json.loads(Path(args.record).read_text(encoding="utf-8-sig"))
        if not isinstance(record, dict):
            raise ValueError("top level is not an object")
    except ValueError as error:
        failures.append(f"Record is not a valid JSON object: {error}")
        return finish(report)
    for field in ("job_id", "team", "deliverable", "review"):
        if record.get(field) in (None, "", [], {}):
            failures.append(f"Missing field: {field}")
    if record.get("team") and record["team"] not in TEAMS:
        failures.append(f"team {record['team']!r} is not one of {', '.join(TEAMS)}")
    review = record.get("review") if isinstance(record.get("review"), dict) else {}
    if not record.get("outputs") and review.get("status") not in NOTHING_MADE_YET:
        failures.append("Missing field: outputs")
    if record.get("review") and review.get("status") not in STATUSES:
        failures.append(f"review.status {review.get('status')!r} is not in the vocabulary")
    if review.get("status") in ("approved", "delivered") and not str(review.get("human_receipt") or "").strip():
        failures.append(f"review.status is {review['status']} but human_receipt is empty")
    report["outputs"] = []
    for item in record.get("outputs") or []:
        target, row = folder / str(item.get("path", "")), {"path": item.get("path")}
        if not item.get("path") or not target.is_file():
            failures.append(f"Output missing on disk: {item.get('path')}")
        else:
            row.update(bytes=target.stat().st_size, sha256=sha256_of(target))
            if item.get("bytes") != row["bytes"]:
                failures.append(f"Output {item['path']} is {row['bytes']} bytes, record says {item.get('bytes')}")
            if row["sha256"] != item.get("sha256"):
                failures.append(f"Output {item['path']} sha256 does not match the record")
        report["outputs"].append(row)
    for need in record.get("needs") or []:
        target = folder / str(need.get("path", ""))
        if not need.get("path") or not target.is_file():
            failures.append(f"stale: need {need.get('job_id')} file is missing: {need.get('path')}")
        elif sha256_of(target) != need.get("sha256"):
            failures.append(f"stale: need {need.get('job_id')} hash changed: {need['path']}")
    return finish(report)


EVIDENCE = ("on_disk", "documented", "verified")
SHEET_FIELDS = ("runtime", "kind", "evidence", "start", "canary", "limits", "stall_signs", "post_checks")
COMFY_SHEET_FIELDS = ("engine_version", "port", "monitor_port", "workflow")


def minutes_ok(value):
    number = lambda v: isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0
    if isinstance(value, list):
        return len(value) == 2 and all(map(number, value)) and value[0] <= value[1]
    return number(value)


def cmd_sheet(args):
    """A runtime specialist's sheet for one job: the operator follows it, so its claims must hold.

    The rule it enforces most: a run is only evidence for the engine it ran on. After an engine
    update, "verified" needs a receipt from the new engine, or the evidence drops and a canary goes first.
    """
    need_file(args.sheet)
    failures, folder = [], Path(args.sheet).resolve().parent
    report = {"failures": failures, "warnings": []}
    try:
        sheet = json.loads(Path(args.sheet).read_text(encoding="utf-8-sig"))
        if not isinstance(sheet, dict):
            raise ValueError("top level is not an object")
    except ValueError as error:
        failures.append(f"Sheet is not a valid JSON object: {error}")
        return finish(report)
    for field in SHEET_FIELDS:
        if sheet.get(field) in (None, "", [], {}):
            failures.append(f"Missing field: {field}")
    comfy = sheet.get("kind") == "comfyui"
    if sheet.get("kind") not in ("comfyui", "python", "other"):
        failures.append(f"kind {sheet.get('kind')!r} is not comfyui, python or other")
    if comfy:
        for field in COMFY_SHEET_FIELDS:
            if sheet.get(field) in (None, ""):
                failures.append(f"Missing field for a ComfyUI runtime: {field}")
    if sheet.get("evidence") not in EVIDENCE:
        failures.append(f"evidence {sheet.get('evidence')!r} is not one of {', '.join(EVIDENCE)}")
    # Absent is not ready: an empty list says the specialist checked and found nothing missing.
    if not isinstance(sheet.get("models_missing"), list):
        failures.append("Missing field: models_missing (an empty list when every model is present)")
    elif sheet["models_missing"]:
        failures.append(f"workflow is not ready: {len(sheet['models_missing'])} model file(s) missing")

    receipts = []
    for item in sheet.get("receipts") or []:
        path = Path(str(item.get("path", "")))
        path = path if path.is_absolute() else folder / path
        receipts.append({"path": item.get("path"), "exists": path.is_file(), "engine_version": item.get("engine_version")})
        if not path.is_file():
            failures.append(f"Receipt missing on disk: {item.get('path')}")
    report["receipts"] = receipts
    if sheet.get("evidence") == "verified":
        on_engine = [r for r in receipts if r["exists"] and (not comfy or r["engine_version"] == sheet.get("engine_version"))]
        if not on_engine:
            failures.append("evidence is verified but no receipt on disk ran on this engine version: "
                            "mark it documented and run the canary first")
    minutes = sheet.get("expected_minutes")
    if minutes is None:
        failures.append("Missing field: expected_minutes (minutes, or [low, high])")
    elif not minutes_ok(minutes):
        failures.append(f"expected_minutes {minutes!r} is not a positive number or a [low, high] range")
    elif not receipts and not sheet.get("estimate_basis"):
        failures.append("expected_minutes has no receipts and no estimate_basis")

    if args.snapshot:
        snapshot = json.loads(Path(args.snapshot).read_text(encoding="utf-8-sig"))
        runtime = next((r for r in snapshot.get("runtimes", []) if r.get("name") == sheet.get("runtime")), None)
        if runtime is None:
            failures.append(f"runtime {sheet.get('runtime')!r} is not in the capability snapshot")
        else:
            for field, key in (("engine_version", "comfyui_version"), ("port", "port")):
                if comfy and runtime.get(key) is not None and sheet.get(field) != runtime.get(key):
                    failures.append(f"{field} {sheet.get(field)!r} differs from the snapshot's {runtime.get(key)!r}")
            stored = runtime.get("workflows") or []
            if comfy and sheet.get("workflow") and stored:
                flow = next((w for w in stored
                             if str(w.get("name") or w.get("file") or "").replace("\\", "/").endswith(str(sheet["workflow"]).replace("\\", "/"))), None)
                if flow is None:
                    failures.append(f"workflow {sheet['workflow']!r} is not in the snapshot for this runtime")
                elif flow.get("ready") is False:
                    failures.append(f"the snapshot marks workflow {sheet['workflow']!r} not ready")
            elif comfy and sheet.get("workflow"):
                # Some lanes build their graph outside the runtime and submit it over the API, so the
                # scanner sees no stored workflow. Then the sheet must name that graph's source file.
                source = Path(str(sheet.get("graph_source") or ""))
                source = source if source.is_absolute() else folder / source
                if not sheet.get("graph_source"):
                    failures.append("the snapshot lists no stored workflows for this runtime: "
                                    "name the file that builds or holds the graph in graph_source")
                elif not source.is_file():
                    failures.append(f"graph_source not found on disk: {sheet['graph_source']}")
                else:
                    report["warnings"].append("graph built outside the runtime: the snapshot cannot confirm its "
                                              "readiness, so models_missing rests on the specialist's own reading")
            report["snapshot_scanned_at"] = snapshot.get("scanned_at")
    else:
        report["warnings"].append("no --snapshot given: engine version, port and workflow readiness not cross-checked")
    return finish(report)


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    pre = sub.add_parser("preflight", help="GPU memory, free RAM and an optional empty-queue check")
    pre.add_argument("--min-free-vram-mib", type=int, default=0, help="0 reports only")
    pre.add_argument("--min-free-ram-gib", type=float, default=0, help="0 reports only")
    pre.add_argument("--comfy", metavar="URL", help="local ComfyUI base URL; fails when the queue is not empty")
    pre.add_argument("--no-gpu", action="store_true", help="skip nvidia-smi on a machine without one")
    pre.set_defaults(func=cmd_preflight)
    probe = sub.add_parser("probe", help="video structure: fps, frames, grid, size, audio rule, decode")
    probe.add_argument("file", type=Path)
    probe.add_argument("--fps", help="expected rate as a fraction, e.g. 24/1")
    probe.add_argument("--frames", type=int)
    probe.add_argument("--frame-grid", metavar="STEP,OFFSET", help="frame count must be OFFSET + k*STEP")
    probe.add_argument("--width", type=int)
    probe.add_argument("--height", type=int)
    probe.add_argument("--audio", choices=("required", "forbidden", "any"), default="any")
    probe.add_argument("--defects", action="store_true", help="report freeze, black and duplicate-frame measurements")
    probe.add_argument("--max-freeze", type=float, metavar="SECONDS", help="with --defects, fail on a longer freeze")
    probe.add_argument("--max-black", type=float, metavar="SECONDS", help="with --defects, fail on a longer black run")
    probe.add_argument("--no-decode", action="store_true", help="skip the full decode")
    probe.set_defaults(func=cmd_probe)
    aud = sub.add_parser("audio", help="loudness, peaks, silence and format of an audio file or the audio of a video")
    aud.add_argument("file", type=Path)
    aud.add_argument("--lufs", type=float)
    aud.add_argument("--lufs-tol", type=float, default=1.0)
    aud.add_argument("--true-peak-max", type=float, metavar="DBFS")
    aud.add_argument("--max-head-silence", type=float, metavar="SECONDS")
    aud.add_argument("--max-tail-silence", type=float, metavar="SECONDS")
    aud.set_defaults(func=cmd_audio)
    job = sub.add_parser("job", help="check a job record against the files on disk")
    job.add_argument("record", type=Path)
    job.set_defaults(func=cmd_job)
    sheet = sub.add_parser("sheet", help="check a runtime specialist's sheet: fields, readiness, evidence on this engine")
    sheet.add_argument("sheet", type=Path)
    sheet.add_argument("--snapshot", type=Path, help="capability snapshot JSON to cross-check engine, port and workflow")
    sheet.set_defaults(func=cmd_sheet)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (CheckError, ValueError, ZeroDivisionError, AttributeError, TypeError) as error:  # bad input is exit 2, never a failed check
        print(json.dumps({"ok": False, "failures": [str(error)]}, indent=2, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
