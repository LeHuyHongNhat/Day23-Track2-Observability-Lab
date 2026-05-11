"""Stub emitter for Day 18's lakehouse (Spark / Delta metrics).

Emits `spark_application_active` gauge so the cross-day dashboard
panel "Day 18 — Spark App Active" shows running Spark applications.
"""
from __future__ import annotations

import os
import random
import time

import requests
from prometheus_client import Gauge, start_http_server

PORT = 9105


def real_scrape(url: str) -> None:
    while True:
        try:
            r = requests.get(url, timeout=2)
            print(f"day18 lakehouse /metrics: {r.status_code} ({len(r.content)} bytes)")
        except requests.exceptions.RequestException as e:
            print(f"day18 lakehouse unreachable: {e}")
        time.sleep(15)


def stub_emit() -> None:
    spark_active = Gauge(
        "spark_application_active",
        "Stub: number of active Spark applications",
        ["app_name"],
    )
    start_http_server(PORT)
    print(f"Stub Day 18 metrics on :{PORT} (add to prometheus.yml as 'day18-stub')")

    apps = ["delta-compaction", "feature-builder"]
    while True:
        for app in apps:
            spark_active.labels(app_name=app).set(random.choice([1, 1, 1, 2]))
        time.sleep(5)


def main() -> int:
    url = os.getenv("DAY18_SPARK_METRICS_URL", "")
    if url:
        real_scrape(url)
    else:
        stub_emit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
