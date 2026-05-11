"""Stub emitter for Day 16's cloud infrastructure (EC2/EKS node_exporter).

Emits fake node_exporter `up` metrics so the cross-day dashboard
panel "Day 16 — Cloud Hosts Up" renders a value (3 hosts).
"""
from __future__ import annotations

import os
import random
import time

import requests
from prometheus_client import Gauge, start_http_server

PORT = 9103


def real_scrape(url: str) -> None:
    while True:
        try:
            r = requests.get(url, timeout=2)
            print(f"day16 cloud /metrics: {r.status_code} ({len(r.content)} bytes)")
        except requests.exceptions.RequestException as e:
            print(f"day16 cloud unreachable: {e}")
        time.sleep(15)


def stub_emit() -> None:
    up_gauge = Gauge("up", "Stub: node_exporter up (1=healthy)", ["job", "instance"])
    start_http_server(PORT)
    print(f"Stub Day 16 metrics on :{PORT} (add to prometheus.yml as 'day16-stub')")
    instances = [
        ("node-exporter", "host-1:9100"),
        ("node-exporter", "host-2:9100"),
        ("node-exporter", "host-3:9100"),
    ]
    while True:
        for job, inst in instances:
            up_gauge.labels(job=job, instance=inst).set(1)
        # Occasionally simulate a host going down briefly
        time.sleep(0.5)
        up_gauge.labels(job="node-exporter", instance="host-3:9100").set(
            0 if random.random() < 0.02 else 1
        )
        time.sleep(14.5)


def main() -> int:
    url = os.getenv("DAY16_NODE_EXPORTER_URL", "")
    if url:
        real_scrape(url)
    else:
        stub_emit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
