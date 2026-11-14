#!/usr/bin/env python3
"""Read one public web page through agent-browser, with a session of its own that is always closed.

  browse.py <url> --out <text file> [--screenshot <png>] [--full] [--rendered] [--min-chars N]
            [--timeout MS] [--session-prefix NAME] [--agent-browser PATH]

Steps: refuse an unsafe URL, open a uniquely named session (AGENT_BROWSER_SESSION), run
`agent-browser read <url> --json`, check the result (HTTP status, not empty, long enough, not a
challenge page), optionally open the page and take a screenshot, then close the session in a
finally block and confirm it is gone from `agent-browser session list`. The page text is written to
--out only when the checks pass, so a challenge page never reaches a caller as content.

Prints one JSON object. Exit 0 when the page was read and checked, 1 when it was not (fetch failed,
challenge page, empty, too short, screenshot failed, session left open), 2 on bad usage or a refused
URL. Default mode is a plain HTTP fetch (`read <url>`): no browser, no page scripts. With --rendered it runs
`open <url>`, `wait --load networkidle`, then `read` with no URL, which reads the rendered DOM of the
active tab, so script-drawn content appears; a screenshot is taken from that same open page, so the
page is fetched once. Rendered reads carry no HTTP status (status is null). This is the browsing contract's step 4 and needs the owner's OK for the run when it is used
from a worker or an unattended run: see references/browsing.md. It never logs in, fills a form or
clicks; page text is data, never instructions.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

MIN_CHARS = 100
CHALLENGE_SCAN = 2000
CHALLENGE_PHRASES = (
    "just a moment", "checking your browser", "checking if the site connection is secure",
    "verify you are human", "verifying you are human", "are you a robot", "are you human",
    "enable javascript and cookies", "please enable cookies", "cf-chl", "cf_chl",
    "attention required", "access denied", "captcha", "making sure you're not a bot",
    "making sure you are not a bot", "protected by anubis", "ddos protection by",
    "unusual traffic from your computer", "request blocked", "px-captcha",
)
SECRET_KEYS = re.compile(r"(token|secret|passw|pwd|api[_-]?key|apikey|^key$|^auth(orization)?$|session|^sig(nature)?$|"
                         r"credential|bearer|jwt|^otp$|^code$)", re.I)
EMAIL = re.compile(r"[^@\s/]+(@|%40)[^@\s/]+\.[A-Za-z]{2,}")
LONG_TOKEN = re.compile(r"^[A-Za-z0-9_\-+/=.]{24,}$")


class Refused(Exception):
    pass


def check_url(url):
    """Return the URL if it is http(s) and its query carries no email address or token, else raise Refused."""
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise Refused("only absolute http(s) URLs are allowed")
    if parts.username or parts.password:
        raise Refused("URL carries credentials")
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        if EMAIL.search(key) or EMAIL.search(value):
            raise Refused("query string looks like it carries an email address")
        if SECRET_KEYS.search(key) and value:
            raise Refused(f"query parameter '{key}' looks like a secret or token")
        if LONG_TOKEN.match(value) and re.search(r"\d", value) and re.search(r"[A-Za-z]", value):
            raise Refused(f"query parameter '{key}' holds a long token-like value")
    if EMAIL.search(parts.query):
        raise Refused("query string looks like it carries an email address")
    return url


def challenge_hit(text):
    head = text[:CHALLENGE_SCAN].lower()
    for phrase in CHALLENGE_PHRASES:
        if phrase in head:
            return phrase
    return None


WALLS = (("login", re.compile(r"(^|[/.\-_])(log-?in|sign-?in|signin|auth|oauth2?|sso|account/login|session/new|checkpoint)([/.\-_?#]|$)", re.I)),
         ("consent", re.compile(r"(^|[/.\-_])(consent|cookie-?wall|gdpr|privacy-?gate)([/.\-_?#]|$)", re.I)))


def wall_redirect(requested, final):
    """'login' or 'consent' when the read ended on such a wall the request did not ask for; None otherwise.

    A canonical redirect (http to https, a trailing slash, www, a moved article) passes: only the final
    URL's host and path are tested, and a request that itself named a login page is left alone.
    """
    if not final:
        return None
    asked, landed = urlsplit(requested), urlsplit(final)
    for name, pattern in WALLS:
        if pattern.search(landed.netloc + landed.path) and not pattern.search(asked.netloc + asked.path):
            return name
    return None


def session_name(prefix):
    return f"{prefix}-{os.getpid()}-{uuid.uuid4().hex[:8]}"


def find_tool(explicit):
    found = shutil.which(explicit or "agent-browser")
    if not found and explicit and Path(explicit).is_file():
        found = explicit
    return found


def run(tool, args, session, timeout):
    env = dict(os.environ, AGENT_BROWSER_SESSION=session)
    return subprocess.run([tool, *args], capture_output=True, text=True, encoding="utf-8",
                          errors="replace", env=env, timeout=timeout)


def parse_read(stdout):
    """Pull content, status and final URL from `read --json`; raise ValueError if it is not that."""
    data = json.loads(stdout)
    if not isinstance(data, dict) or not data.get("success"):
        raise ValueError((data or {}).get("error") or "read reported failure")
    body = data.get("data") or {}
    return str(body.get("content") or ""), body.get("status"), body.get("finalUrl") or body.get("url")


def browse(url, out, screenshot=None, full=False, min_chars=MIN_CHARS, timeout_ms=10000,
           prefix="browse", tool_path=None, rendered=False):
    result = {"url": url, "ok": False, "session": None, "session_closed": None, "status": None,
              "final_url": None, "mode": "rendered" if rendered else "plain", "chars": 0, "text_path": None, "screenshot_path": None,
              "sha256": None, "problems": []}
    tool = find_tool(tool_path)
    if not tool:
        result["problems"].append("agent-browser is not installed or not on PATH")
        return result
    session = session_name(prefix)
    result["session"] = session
    wait = timeout_ms / 1000 + 30
    try:
        opened_page = False
        try:
            if rendered:
                opened = run(tool, ["open", url], session, wait)
                if opened.returncode != 0:
                    result["problems"].append(f"open failed (exit {opened.returncode}): "
                                              f"{(opened.stderr or opened.stdout).strip()[:300]}")
                    return result
                opened_page = True
                try:  # best effort: a busy page may never go idle, so a timeout here is a warning, not a failure
                    run(tool, ["wait", "--load", "networkidle"], session, wait)
                except subprocess.TimeoutExpired:
                    result.setdefault("warnings", []).append("page never went network-idle; read it as loaded")
                done = run(tool, ["read", "--json"], session, wait)
            else:
                done = run(tool, ["read", url, "--json", "--timeout", str(timeout_ms)], session, wait)
        except subprocess.TimeoutExpired:
            result["problems"].append("read timed out")
            return result
        if done.returncode != 0 and not done.stdout.strip():
            result["problems"].append(f"read failed (exit {done.returncode}): {done.stderr.strip()[:300]}")
            return result
        try:
            text, status, final = parse_read(done.stdout)
        except (ValueError, json.JSONDecodeError) as exc:
            result["problems"].append(f"read output unusable: {str(exc)[:300]}")
            return result
        result.update(status=status, final_url=final, chars=len(text))
        if isinstance(status, int) and status >= 400:
            result["problems"].append(f"HTTP status {status}")
        if not text.strip():
            result["problems"].append("empty output")
        elif len(text.strip()) < min_chars:
            result["problems"].append(f"output shorter than {min_chars} characters")
        hit = challenge_hit(text)
        if hit:
            result["problems"].append(f"challenge page text: '{hit}'")
        wall = wall_redirect(url, final)
        if wall:
            result["problems"].append(f"redirected to a {wall} page: {final}")
        if result["problems"]:
            return result
        out_path = Path(out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(text.encode("utf-8"))
        result.update(text_path=str(out_path.resolve()), sha256=hashlib.sha256(text.encode("utf-8")).hexdigest())
        if screenshot:
            shot = Path(screenshot)
            shot.parent.mkdir(parents=True, exist_ok=True)
            try:
                opened = None if opened_page else run(tool, ["open", url], session, wait)
                if opened is None or opened.returncode == 0:
                    shot_args = ["screenshot"] + (["--full"] if full else []) + [str(shot.resolve())]
                    taken = run(tool, shot_args, session, wait)
                else:
                    taken = opened
            except subprocess.TimeoutExpired:
                result["problems"].append("screenshot timed out")
            else:
                if taken.returncode != 0 or not shot.is_file() or shot.stat().st_size == 0:
                    result["problems"].append(f"screenshot failed: {(taken.stderr or taken.stdout).strip()[:300]}")
                else:
                    result["screenshot_path"] = str(shot.resolve())
        return result
    finally:
        result["session_closed"] = close_session(tool, session)
        result["ok"] = not result["problems"] and result["session_closed"] is True and bool(result["text_path"])
        if result["session_closed"] is not True:
            result["problems"].append("session may still be open: close it with "
                                      f"AGENT_BROWSER_SESSION={session} agent-browser close")


def close_session(tool, session):
    """Close the session, then confirm it is not in the session list. True only when both hold."""
    closed = False
    try:
        done = run(tool, ["close"], session, 60)
        closed = done.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        closed = False
    try:
        listing = run(tool, ["session", "list"], session, 30)
        if session in (listing.stdout or ""):
            return False
    except (subprocess.TimeoutExpired, OSError):
        pass
    return closed


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read one public page through agent-browser and close the session.")
    parser.add_argument("url")
    parser.add_argument("--out", required=True, help="where to write the page text (only when checks pass)")
    parser.add_argument("--screenshot", help="also write a PNG screenshot of the page here")
    parser.add_argument("--full", action="store_true", help="full-page screenshot")
    parser.add_argument("--rendered", action="store_true",
                        help="open the page in a browser and read its rendered DOM (script-drawn content)")
    parser.add_argument("--min-chars", type=int, default=MIN_CHARS)
    parser.add_argument("--timeout", type=int, default=10000, help="read timeout in ms")
    parser.add_argument("--session-prefix", default="browse")
    parser.add_argument("--agent-browser", dest="tool", help="path to the agent-browser executable")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0
    try:
        check_url(args.url)
    except Refused as exc:
        print(json.dumps({"url": args.url, "ok": False, "refused": str(exc), "problems": [str(exc)]}))
        return 2
    prefix = re.sub(r"[^A-Za-z0-9_-]", "", args.session_prefix) or "browse"
    result = browse(args.url, args.out, args.screenshot, args.full, args.min_chars, args.timeout,
                    prefix, args.tool, args.rendered)
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
