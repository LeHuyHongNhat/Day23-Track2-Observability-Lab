"""Stub emitter for Day 17's data pipeline (Airflow DAG metrics).

Emits a synthetic `airflow_dag_run_duration_seconds` histogram so the
cross-day dashboard panel "Day 17 — Airflow DAG Duration (P95)" renders.
"""
from __future__ import annotations

import math
import os
import random
import time

import requests
from prometheus_client import Histogram, start_http_server

PORT = 9104
BUCKETS = (5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0, float("inf"))


def real_scrape(url: str) -> None:
    while True:
        try:
            r = requests.get(url, timeout=2)
            print(f"day17 pipeline /metrics: {r.status_code} ({len(r.content)} bytes)")
        except requests.exceptions.RequestException as e:
            print(f"day17 pipeline unreachable: {e}")
        time.sleep(15)


def stub_emit() -> None:
    duration = Histogram(
        "airflow_dag_run_duration_seconds",
        "Stub: Airflow DAG run duration",
        ["dag_id"],
        buckets=list(BUCKETS),
    )
    start_http_server(PORT)
    print(f"Stub Day 17 metrics on :{PORT} (add to prometheus.yml as 'day17-stub')")

    dags = ["etl-main", "feature-engineering", "model-training"]
    tick = 0
    while True:
        tick += 1
        for dag in dags:
            # Log-normal DAG durations between 20s and 600s
            base = random.lognormvariate(4.0, 0.5)
            for _ in range(3):  # observe 3 runs per dag per cycle
                duration.labels(dag_id=dag).observe(base + random.gauss(0, 10))
        time.sleep(5)


def main() -> int:
    url = os.getenv("DAY17_AIRFLOW_METRICS_URL", "")
    if url:
        real_scrape(url)
    else:
        stub_emit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
