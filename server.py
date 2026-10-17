#!/usr/bin/env python3
"""VOICEVOX HTTP wrapper: receive text over HTTP and speak it on this machine's speaker."""
import hmac
import json
import os
import queue
import subprocess
import tempfile
import threading
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.environ.get("VV_ENGINE", "http://127.0.0.1:50021")
HOST = os.environ.get("VV_HOST", "0.0.0.0")
PORT = int(os.environ.get("VV_PORT", "8080"))
TOKEN = os.environ.get("VV_TOKEN", "")
PLAYER = os.environ.get("VV_PLAYER", "pw-play").split()
SETTINGS_FILE = os.environ.get("VV_SETTINGS_FILE", os.path.join(BASE_DIR, "data", "settings.json"))
UI_FILE = os.path.join(BASE_DIR, "static", "index.html")

# Voice parameters: name -> (audio_query field, min, max, step, default, label)
VOICE_PARAMS = {
    "speed": ("speedScale", 0.5, 2.0, 0.01, 1.0, "速さ"),
    "pitch": ("pitchScale", -0.15, 0.15, 0.01, 0.0, "高さ"),
    "intonation": ("intonationScale", 0.0, 2.0, 0.01, 1.0, "抑揚"),
    "volume": ("volumeScale", 0.0, 2.0, 0.01, 1.0, "音量"),
    "pre_silence": ("prePhonemeLength", 0.0, 1.5, 0.01, 0.1, "開始前の無音（秒）"),
    "post_silence": ("postPhonemeLength", 0.0, 1.5, 0.01, 0.1, "終了後の無音（秒）"),
    "pause": ("pauseLengthScale", 0.0, 2.0, 0.01, 1.0, "句読点の長さ"),
}
# Behaviour settings: name -> (min, max, default, label)
BEHAVIOUR_PARAMS = {
    "wait_timeout": (1, 3600, int(os.environ.get("VV_WAIT_TIMEOUT", "300")), "待ち時間の上限（秒）"),
    "max_text": (1, 10000, 1000, "最大文字数"),
}
DEFAULT_SPEAKER = os.environ.get("VV_SPEAKER", "3")  # id or "名前[/話し方]"; 3 = ずんだもん/ノーマル

jobs: "queue.Queue[dict]" = queue.Queue(maxsize=50)
settings_lock = threading.Lock()
speakers_cache = None


def engine_request(path, params=None, body=None):
    url = ENGINE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    data = json.dumps(body).encode() if body is not None else None
    method = "POST" if data is not None or path in ("/audio_query", "/synthesis") else "GET"
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as res:
        return res.read()


# ---------- speakers ----------

class SpeakerError(ValueError):
    def __init__(self, message, choices=None):
        super().__init__(message)
        self.choices = choices


def get_speakers():
    """Talk-capable speakers from the engine, cached after the first successful fetch."""
    global speakers_cache
    if speakers_cache is None:
        speakers = json.loads(engine_request("/speakers"))
        speakers_cache = [
            {"name": s["name"],
             "styles": [{"id": st["id"], "name": st["name"]}
                        for st in s["styles"] if st.get("type", "talk") == "talk"]}
            for s in speakers
        ]
        speakers_cache = [s for s in speakers_cache if s["styles"]]
    return speakers_cache


def resolve_speaker(value):
    """Turn an id or "名前[/話し方]" into (style id, "名前/話し方")."""
    speakers = get_speakers()
    if isinstance(value, bool):
        raise SpeakerError("speaker must be an id or a name")
    if isinstance(value, int) or (isinstance(value, str) and value.strip().isdigit()):
        sid = int(value)
        for s in speakers:
            for st in s["styles"]:
                if st["id"] == sid:
                    return sid, f"{s['name']}/{st['name']}"
        raise SpeakerError(f"unknown speaker id: {sid}")
    if not isinstance(value, str):
        raise SpeakerError("speaker must be an id or a name")
    name, _, style = (part.strip() for part in value.partition("/"))
    character = next((s for s in speakers if s["name"] == name), None)
    if character is None:
        raise SpeakerError(f"unknown speaker: {name}", [s["name"] for s in speakers])
    styles = character["styles"]
    if style:
        st = next((st for st in styles if st["name"] == style), None)
        if st is None:
            raise SpeakerError(f"unknown style for {name}: {style}", [st["name"] for st in styles])
    else:
        st = next((st for st in styles if st["name"] == "ノーマル"), styles[0])
    return st["id"], f"{name}/{st['name']}"


# ---------- settings ----------

def default_settings():
    s = {"speaker": DEFAULT_SPEAKER}
    s.update({k: v[4] for k, v in VOICE_PARAMS.items()})
    s.update({k: v[2] for k, v in BEHAVIOUR_PARAMS.items()})
    return s


def load_settings():
    s = default_settings()
    try:
        with open(SETTINGS_FILE, encoding="utf-8") as f:
            saved = json.load(f)
        s.update({k: v for k, v in saved.items() if k in s})
    except FileNotFoundError:
        pass
    except (OSError, ValueError) as e:
        print(f"[warn] ignoring {SETTINGS_FILE}: {e}", flush=True)
    return s


def save_settings(s):
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    tmp = SETTINGS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=2)
    os.replace(tmp, SETTINGS_FILE)


settings = load_settings()


def validate_number(name, value, lo, hi, cast=float):
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a number")
    try:
        v = cast(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be a number") from None
    if not lo <= v <= hi:
        raise ValueError(f"{name} must be between {lo} and {hi}")
    return v


def validate_voice(params):
    """Validate per-request voice params; returns {name: float} for the ones given."""
    out = {}
    for k, (_, lo, hi, *_rest) in VOICE_PARAMS.items():
        if params.get(k) is not None:
            out[k] = validate_number(k, params[k], lo, hi)
    return out


def settings_view():
    with settings_lock:
        s = dict(settings)
    try:
        s["speaker"], voice = resolve_speaker(s["speaker"])
    except Exception:  # engine down or bad VV_SPEAKER: still show what we have
        voice = None
    limits = {k: {"min": lo, "max": hi, "step": step, "default": d, "label": label}
              for k, (_, lo, hi, step, d, label) in VOICE_PARAMS.items()}
    limits.update({k: {"min": lo, "max": hi, "step": 1, "default": d, "label": label}
                   for k, (lo, hi, d, label) in BEHAVIOUR_PARAMS.items()})
    return {"settings": s, "voice": voice, "limits": limits}


# ---------- playback ----------

def synthesize(job):
    query = json.loads(engine_request("/audio_query", {"text": job["text"], "speaker": job["speaker"]}))
    for k, (field, *_rest) in VOICE_PARAMS.items():
        query[field] = job[k]
    return engine_request("/synthesis", {"speaker": job["speaker"]}, query)


def worker():
    while True:
        task = jobs.get()
        job = task["job"]
        try:
            wav = synthesize(job)
            with tempfile.NamedTemporaryFile(suffix=".wav") as f:
                f.write(wav)
                f.flush()
                rc = subprocess.run(PLAYER + [f.name], check=False).returncode
            if rc != 0:
                raise RuntimeError(f"{PLAYER[0]} exited with {rc}")
        except Exception as e:  # keep the worker alive whatever happens
            task["error"] = str(e)
            print(f"[error] {e!r} text={job['text'][:40]!r}", flush=True)
        finally:
            task["done"].set()
            jobs.task_done()


# ---------- HTTP ----------

class Handler(BaseHTTPRequestHandler):
    server_version = "voicevox-server"

    def _send(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_ui(self):
        with open(UI_FILE, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _authorized(self):
        if not TOKEN:
            return True
        auth = self.headers.get("Authorization", "")
        return auth.startswith("Bearer ") and hmac.compare_digest(auth[7:].encode(), TOKEN.encode())

    def _path(self):
        return urllib.parse.urlparse(self.path).path

    def _read_body(self, json_only=False):
        """Parse the request body into a dict; returns None after sending 400."""
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b""
        ctype = self.headers.get("Content-Type", "")
        try:
            if "json" in ctype or json_only:
                body = json.loads(raw or b"{}")
                if not isinstance(body, dict):
                    raise ValueError("JSON body must be an object")
                return body
            if "form" in ctype:
                return {k: v[0] for k, v in urllib.parse.parse_qs(raw.decode()).items()}
            return {"text": raw.decode()} if raw else {}
        except (ValueError, UnicodeDecodeError):
            self._send(400, {"error": "invalid body"})
            return None

    def _engine_error(self, e):
        self._send(503, {"error": f"engine unreachable: {e}"})

    def _speaker_error(self, e):
        body = {"error": str(e)}
        if e.choices:
            body["choices"] = e.choices
        self._send(400, body)

    def _speak(self, params):
        with settings_lock:
            current = dict(settings)
        text = str(params.get("text", "")).strip()
        if not text:
            return self._send(400, {"error": "text is required"})
        if len(text) > current["max_text"]:
            return self._send(400, {"error": f"text must be <= {current['max_text']} chars"})
        try:
            sid, voice = resolve_speaker(params.get("speaker", current["speaker"]))
            overrides = validate_voice(params)
        except SpeakerError as e:
            return self._speaker_error(e)
        except ValueError as e:
            return self._send(400, {"error": str(e)})
        except OSError as e:
            return self._engine_error(e)
        job = {"text": text, "speaker": sid, "voice": voice,
               **{k: current[k] for k in VOICE_PARAMS}, **overrides}
        wait = str(params.get("wait", True)).lower() not in ("false", "0", "no")
        task = {"job": job, "done": threading.Event(), "error": None}
        try:
            jobs.put_nowait(task)
        except queue.Full:
            return self._send(503, {"error": "queue is full"})
        if not wait:
            return self._send(202, {"status": "queued", "queue": jobs.qsize(), **job})
        if not task["done"].wait(current["wait_timeout"]):
            return self._send(504, {"status": "timeout", "error": "still queued or playing", **job})
        if task["error"]:
            return self._send(502, {"status": "failed", "error": task["error"], **job})
        self._send(200, {"status": "spoken", **job})

    def _update_settings(self, body):
        global settings
        unknown = set(body) - set(default_settings())
        if unknown:
            return self._send(400, {"error": f"unknown settings: {', '.join(sorted(unknown))}"})
        try:
            new = {}
            if "speaker" in body:
                new["speaker"], _ = resolve_speaker(body["speaker"])
            new.update(validate_voice(body))
            for k, (lo, hi, *_rest) in BEHAVIOUR_PARAMS.items():
                if k in body:
                    new[k] = validate_number(k, body[k], lo, hi, int)
        except SpeakerError as e:
            return self._speaker_error(e)
        except ValueError as e:
            return self._send(400, {"error": str(e)})
        except OSError as e:
            return self._engine_error(e)
        with settings_lock:
            settings = {**settings, **new}
            try:
                save_settings(settings)
            except OSError as e:
                return self._send(500, {"error": f"applied but could not save {SETTINGS_FILE}: {e}"})
        self._send(200, settings_view())

    def do_GET(self):
        path = self._path()
        if path in ("/", "/index.html"):
            return self._send_ui()
        if path == "/health":
            try:
                version = engine_request("/version").decode().strip('"')
                return self._send(200, {"status": "ok", "engine": version, "queue": jobs.qsize()})
            except Exception as e:
                return self._send(503, {"status": "engine unreachable", "error": str(e)})
        if not self._authorized():
            return self._send(401, {"error": "unauthorized"})
        if path == "/speakers":
            try:
                return self._send(200, get_speakers())
            except OSError as e:
                return self._engine_error(e)
        if path == "/settings":
            return self._send(200, settings_view())
        if path == "/speak":
            return self._send(405, {"error": "use POST /speak"})
        self._send(404, {"error": "not found"})

    def do_POST(self):
        path = self._path()
        if not self._authorized():
            return self._send(401, {"error": "unauthorized"})
        if path != "/speak":
            return self._send(404, {"error": "not found"})
        body = self._read_body()
        if body is not None:
            self._speak(body)

    def do_PUT(self):
        path = self._path()
        if not self._authorized():
            return self._send(401, {"error": "unauthorized"})
        if path != "/settings":
            return self._send(404, {"error": "not found"})
        body = self._read_body(json_only=True)
        if body is not None:
            self._update_settings(body)

    def do_DELETE(self):
        global settings
        path = self._path()
        if not self._authorized():
            return self._send(401, {"error": "unauthorized"})
        if path != "/settings":
            return self._send(404, {"error": "not found"})
        with settings_lock:
            settings = default_settings()
            try:
                os.remove(SETTINGS_FILE)
            except FileNotFoundError:
                pass
        self._send(200, settings_view())

    def log_message(self, fmt, *args):
        print(f"{self.address_string()} {fmt % args}", flush=True)


def main():
    threading.Thread(target=worker, daemon=True).start()
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"listening on http://{HOST}:{PORT} (engine={ENGINE}, auth={'on' if TOKEN else 'off'})", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
