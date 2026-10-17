#!/usr/bin/env bash
# Start VOICEVOX engine (docker) + HTTPS wrapper in the foreground. Ctrl+C stops both.
set -euo pipefail
cd "$(dirname "$0")"

ENGINE_IMAGE="${VV_ENGINE_IMAGE:-voicevox/voicevox_engine:cpu-latest}"
CONTAINER=voicevox-engine

[ -f certs/server.crt ] || ./gen-cert.sh

if [ -f .env ]; then set -a; . ./.env; set +a; fi

cleanup() {
  echo "stopping engine..."
  docker stop "$CONTAINER" >/dev/null 2>&1 || true
}
trap cleanup EXIT

if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  docker run -d --rm --name "$CONTAINER" -p 127.0.0.1:50021:50021 "$ENGINE_IMAGE" >/dev/null
fi

echo -n "waiting for engine"
for _ in $(seq 60); do
  curl -sf http://127.0.0.1:50021/version >/dev/null && break
  echo -n "."; sleep 1
done
echo

python3 server.py
