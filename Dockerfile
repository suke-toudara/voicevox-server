FROM python:3.12-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends pulseaudio-utils \
 && rm -rf /var/lib/apt/lists/*
# Dummy cookie: PipeWire ignores it, but paplay warns when none exists
RUN head -c 256 /dev/zero > /etc/pulse-cookie && chmod 444 /etc/pulse-cookie

WORKDIR /app
COPY server.py .

ENV VV_PLAYER=paplay \
    PULSE_COOKIE=/etc/pulse-cookie \
    PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["python3", "server.py"]
