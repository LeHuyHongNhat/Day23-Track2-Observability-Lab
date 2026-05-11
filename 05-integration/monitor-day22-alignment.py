"""Stub emitter for Day 22's alignment/eval (DPO model metrics).

Emits `day22_dpo_eval_pass_rate` gauge so the cross-day dashboard
panel "Day 22 — DPO Eval Pass Rate" shows a realistic eval score.
"""
from __future__ import annotations

import os
import random
import time

import requests
from prometheus_client import Gauge, start_http_server

PORT = 9106


def real_scrape(url: str) -> None:
    while True:
        try:
            r = requests.get(url, timeout=2)
            print(f"day22 alignment /metrics: {r.status_code} ({len(r.content)} bytes)")
        except requests.exceptions.RequestException as e:
            print(f"day22 alignment unreachable: {e}")
        time.sleep(15)


def stub_emit() -> None:
    dpo_pass = Gauge(
        "day22_dpo_eval_pass_rate",
        "Stub: DPO evaluation pass rate [0-1]",
    )
    start_http_server(PORT)
    print(f"Stub Day 22 metrics on :{PORT} (add to prometheus.yml as 'day22-stub')")

    while True:
        # Realistic DPO eval pass rate hovering around 0.82-0.88
        dpo_pass.set(0.82 + random.gauss(0.03, 0.01))
        time.sleep(5)


def main() -> int:
    url = os.getenv("DAY22_DPO_METRICS_URL", "")
    if url:
        real_scrape(url)
    else:
        stub_emit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
