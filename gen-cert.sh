#!/usr/bin/env bash
# Generate a self-signed certificate valid for this host's name and IP addresses.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p certs

SAN="DNS:$(hostname),DNS:localhost,IP:127.0.0.1"
for ip in $(hostname -I); do
  case "$ip" in 172.*|*:*) continue ;; esac  # skip docker bridges and IPv6
  SAN="$SAN,IP:$ip"
done

openssl req -x509 -newkey rsa:2048 -nodes -days 3650 \
  -keyout certs/server.key -out certs/server.crt \
  -subj "/CN=$(hostname)" -addext "subjectAltName=$SAN"
chmod 600 certs/server.key
echo "generated certs/server.crt ($SAN)"
