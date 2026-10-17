#!/usr/bin/env python3
"""VOICEVOX HTTPS wrapper: receive text over HTTPS and speak it on this machine's speaker."""
import hmac
import json
import os
import queue
import ssl
import subprocess
import tempfile
import threading
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.environ.get("VV_ENGINE", "http://127.0.0.1:50021")
HOST = os.environ.get("VV_HOST", "0.0.0.0")
PORT = int(os.environ.get("VV_PORT", "8443"))
TOKEN = os.environ.get("VV_TOKEN", "")
CERT = os.environ.get("VV_CERT", os.path.join(BASE_DIR, "certs", "server.crt"))
KEY = os.environ.get("VV_KEY", os.path.join(BASE_DIR, "certs", "server.key"))
DEFAULT_SPEAKER = int(os.environ.get("VV_SPEAKER", "3"))  # 3 = ずんだもん(ノーマル)
PLAYER = os.environ.get("VV_PLAYER", "pw-play").split()
MAX_TEXT = 1000
WAIT_TIMEOUT = float(os.environ.get("VV_WAIT_TIMEOUT", "300"))

jobs: "queue.Queue[dict]" = queue.Queue(maxsize=50)


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


def synthesize(job):
    query = json.loads(engine_request("/audio_query", {"text": job["text"], "speaker": job["speaker"]}))
    for key, field in (("speed", "speedScale"), ("pitch", "pitchScale"),
                       ("intonation", "intonationScale"), ("volume", "volumeScale")):
        if job.get(key) is not None:
            query[field] = float(job[key])
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


class Handler(BaseHTTPRequestHandler):
    server_version = "voicevox-wrapper"

    def _send(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
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

    def _enqueue(self, params):
        text = str(params.get("text", "")).strip()
        if not text:
            return self._send(400, {"error": "text is required"})
        if len(text) > MAX_TEXT:
            return self._send(400, {"error": f"text must be <= {MAX_TEXT} chars"})
        try:
            job = {"text": text, "speaker": int(params.get("speaker", DEFAULT_SPEAKER))}
            for k in ("speed", "pitch", "intonation", "volume"):
                if params.get(k) is not None:
                    job[k] = float(params[k])
        except (ValueError, TypeError):
            return self._send(400, {"error": "speaker/speed/pitch/intonation/volume must be numbers"})
        wait = str(params.get("wait", True)).lower() not in ("false", "0", "no")
        task = {"job": job, "done": threading.Event(), "error": None}
        try:
            jobs.put_nowait(task)
        except queue.Full:
            return self._send(503, {"error": "queue is full"})
        if not wait:
            return self._send(202, {"status": "queued", "queue": jobs.qsize(), **job})
        if not task["done"].wait(WAIT_TIMEOUT):
            return self._send(504, {"status": "timeout", "error": "still queued or playing", **job})
        if task["error"]:
            return self._send(502, {"status": "failed", "error": task["error"], **job})
        self._send(200, {"status": "spoken", **job})

    def do_GET(self):
        path = self._path()
        if path == "/health":
            try:
                version = engine_request("/version").decode().strip('"')
                return self._send(200, {"status": "ok", "engine": version, "queue": jobs.qsize()})
            except Exception as e:
                return self._send(503, {"status": "engine unreachable", "error": str(e)})
        if not self._authorized():
            return self._send(401, {"error": "unauthorized"})
        if path == "/speakers":
            speakers = json.loads(engine_request("/speakers"))
            return self._send(200, [{"name": s["name"],
                                     "styles": [{"id": st["id"], "name": st["name"]} for st in s["styles"]]}
                                    for s in speakers])
        if path == "/speak":
            return self._send(405, {"error": "use POST /speak"})
        self._send(404, {"error": "not found"})

    def do_POST(self):
        path, params = self._path(), {}
        if not self._authorized():
            return self._send(401, {"error": "unauthorized"})
        if path != "/speak":
            return self._send(404, {"error": "not found"})
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b""
        ctype = self.headers.get("Content-Type", "")
        try:
            if "json" in ctype:
                body = json.loads(raw or b"{}")
                if not isinstance(body, dict):
                    raise ValueError("JSON body must be an object")
                params.update(body)
            elif "form" in ctype:
                params.update({k: v[0] for k, v in urllib.parse.parse_qs(raw.decode()).items()})
            elif raw:
                params["text"] = raw.decode()
        except (ValueError, UnicodeDecodeError):
            return self._send(400, {"error": "invalid body"})
        self._enqueue(params)

    def log_message(self, fmt, *args):
        print(f"{self.address_string()} {fmt % args}", flush=True)


def main():
    threading.Thread(target=worker, daemon=True).start()
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    scheme = "http"
    if os.path.exists(CERT) and os.path.exists(KEY):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(CERT, KEY)
        httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
        scheme = "https"
    print(f"listening on {scheme}://{HOST}:{PORT} (engine={ENGINE}, auth={'on' if TOKEN else 'off'})", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
