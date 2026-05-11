"""Run the FastAPI app with Pyroscope continuous profiling enabled.

On macOS: uses pyroscope-io Python SDK (push mode) to send CPU profiles
           to the Pyroscope server.
On Linux:  can also use eBPF auto-instrumentation — just point the Pyroscope
           agent at PID 1 of the app container (see README).

Usage:
  # 1. Start Pyroscope server first:
  docker compose -f BONUS-ebpf-profiling/docker-compose.pyroscope.yml up -d

  # 2. Install SDK:
  pip install pyroscope-io

  # 3. Run the app with profiling:
  OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317 \
  OTEL_SERVICE_NAME=inference-api \
  python BONUS-ebpf-profiling/pyroscope-app.py
"""
from __future__ import annotations

import os
import sys

# Ensure app module is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "01-instrument-fastapi", "app"))

import uvicorn

try:
    import pyroscope
except ImportError:
    print("pyroscope-io not installed. Run: pip install pyroscope-io")
    print("Continuing without profiling...")
    pyroscope = None


def main() -> int:
    if pyroscope is not None:
        pyroscope.configure(
            application_name="day23-inference-api",
            server_address="http://localhost:4040",
            sample_rate=100,  # Hz — 100 samples/sec per thread
            detect_subprocesses=True,
            oncpu=True,
            native=False,  # macOS: use Python CPU profiler; Linux: set True for eBPF
            tags={
                "service": "inference-api",
                "environment": "lab",
                "track": "day23",
            },
            # Profile only the inference code, not uvicorn internals
            report_pid=True,
            report_thread_id=True,
            report_thread_name=True,
        )
        print(f"Pyroscope profiling active → http://localhost:4040")
    else:
        print("Pyroscope disabled (install: pip install pyroscope-io)")

    # Import app here so Pyroscope wraps the main thread.
    from main import app  # noqa: E402

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
