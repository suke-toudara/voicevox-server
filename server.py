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
        job = jobs.get()
        try:
            wav = synthesize(job)
            with tempfile.NamedTemporaryFile(suffix=".wav") as f:
                f.write(wav)
                f.flush()
                subprocess.run(PLAYER + [f.name], check=False)
        except Exception as e:  # keep the worker alive whatever happens
            print(f"[error] {e!r} text={job['text'][:40]!r}", flush=True)
        finally:
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

    def _authorized(self, params):
        if not TOKEN:
            return True
        auth = self.headers.get("Authorization", "")
        given = auth[7:] if auth.startswith("Bearer ") else params.get("token", "")
        return hmac.compare_digest(given, TOKEN)

    def _params(self):
        parsed = urllib.parse.urlparse(self.path)
        params = {k: v[0] for k, v in urllib.parse.parse_qs(parsed.query).items()}
        return parsed.path, params

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
        except ValueError:
            return self._send(400, {"error": "speaker/speed/pitch/intonation/volume must be numbers"})
        try:
            jobs.put_nowait(job)
        except queue.Full:
            return self._send(503, {"error": "queue is full"})
        self._send(202, {"status": "queued", "queue": jobs.qsize(), **job})

    def do_GET(self):
        path, params = self._params()
        if path == "/health":
            try:
                version = engine_request("/version").decode().strip('"')
                return self._send(200, {"status": "ok", "engine": version, "queue": jobs.qsize()})
            except Exception as e:
                return self._send(503, {"status": "engine unreachable", "error": str(e)})
        if not self._authorized(params):
            return self._send(401, {"error": "unauthorized"})
        if path == "/speakers":
            speakers = json.loads(engine_request("/speakers"))
            return self._send(200, [{"name": s["name"],
                                     "styles": [{"id": st["id"], "name": st["name"]} for st in s["styles"]]}
                                    for s in speakers])
        if path == "/speak":
            return self._enqueue(params)
        self._send(404, {"error": "not found"})

    def do_POST(self):
        path, params = self._params()
        if not self._authorized(params):
            return self._send(401, {"error": "unauthorized"})
        if path != "/speak":
            return self._send(404, {"error": "not found"})
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b""
        ctype = self.headers.get("Content-Type", "")
        try:
            if "json" in ctype:
                params.update(json.loads(raw or b"{}"))
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
