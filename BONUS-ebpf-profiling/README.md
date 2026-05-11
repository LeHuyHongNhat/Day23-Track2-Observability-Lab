# BONUS — eBPF Continuous Profiling (Pyroscope)

Capture flame graphs for the Day 23 inference service using Grafana Pyroscope.

## Platform support

| Platform | Method | How |
|---|---|---|
| **Linux** (native or WSL2) | eBPF auto-instrumentation | Pyroscope agent attaches to app PID |
| **macOS** (Apple Silicon / Intel) | Python SDK push-mode | `pyroscope-io` package sends profiles over HTTP |

Linux eBPF gives you full system-level profiles (kernel, I/O, off-CPU). macOS push-mode gives you Python-level CPU profiles — sufficient for the bonus checkpoint.

## Quick start

### 1. Start Pyroscope server

```bash
docker compose -f BONUS-ebpf-profiling/docker-compose.pyroscope.yml up -d
```

Verify: open http://localhost:4040

### 2. Profile the app

**Linux / WSL2 (eBPF — recommended):**

```bash
# Install Pyroscope agent on the host
wget https://github.com/grafana/pyroscope/releases/download/v1.7.0/pyroscope-agent_1.7.0_linux_amd64.tar.gz
tar xzf pyroscope-agent_*.tar.gz

# Attach to the running app container's Python process
sudo ./pyroscope agent \
  --server-address=http://localhost:4040 \
  --application-name=day23-inference-api \
  --tags=service=inference-api,env=lab \
  --target-pid=$(docker inspect day23-app --format '{{.State.Pid}}') \
  --spy-name=python
```

**macOS (Python SDK):**

```bash
pip install pyroscope-io

# Run the app with profiling enabled
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317 \
OTEL_SERVICE_NAME=inference-api \
python BONUS-ebpf-profiling/pyroscope-app.py
```

### 3. Generate load to see profile data

```bash
make load
```

### 4. View flame graph

Open http://localhost:4040 → select `day23-inference-api` application.

The flame graph should clearly show:

```
predict() → simulate_inference()  (dominates CPU time)
├── hashlib.sha256()              (prompt hashing)
├── random.gauss()                (latency simulation)
├── random.randint()              (token count generation)
└── time.sleep()                  (off-CPU — visible in wall-time profile)
```

## Scoring (bonus)

- Start Pyroscope: `docker compose -f BONUS-ebpf-profiling/docker-compose.pyroscope.yml up -d`
- Run app with profiling + apply load for ~30s
- Open Pyroscope UI → flame graph → screenshot
- Save screenshot: `submission/screenshots/pyroscope-flamegraph.png`

## Cleanup

```bash
docker compose -f BONUS-ebpf-profiling/docker-compose.pyroscope.yml down -v
```
