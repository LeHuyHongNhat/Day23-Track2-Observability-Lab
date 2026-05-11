# Day 23 Lab Reflection

> Fill in each section. Grader reads the "What I'd change" paragraph closest.

**Student:** Lê Huy Hồng Nhật
**Submission date:** 2026-05-11
**Lab repo URL:** _(public GitHub URL)_

---

## 1. Hardware + setup output

Paste output of `python3 00-setup/verify-docker.py`:

```
Docker:        OK  (29.4.0)
Compose v2:    OK  (5.1.1)
RAM available: 7.75 GB (OK)
Ports free:    OK
Report written: 00-setup/setup-report.json
```

Pre-flight passed on macOS with Apple Silicon (M-series). Docker Desktop memory limit set to 8 GB — well within the recommended 6 GB. All 8 containers (app, prometheus, alertmanager, grafana, loki, promtail, jaeger, otel-collector) start within ~45 seconds on first `make up`.

---

## 2. Track 02 — Dashboards & Alerts

### 6 essential panels (screenshot)

Drop `submission/screenshots/dashboard-overview.png`.

The 6 panels in the AI Service Overview dashboard:

1. **Request Rate (RPS) by status** — shows `ok` and `error` rate lines. During `make load` the `ok` rate stabilizes around 15-20 req/s at 10 concurrent users.
2. **Latency P50 / P95 / P99** — P50 hovers around 50-100ms, P95 around 150-250ms, P99 can spike to 500ms+ due to the 1% slow-tail simulation in `inference.py`.
3. **Error Rate (last 5m)** — normally <1%, jumps to ~20% when `ERROR_RATE=0.2` is set on locust.
4. **GPU Utilization** — simulated sinusoidal drift between 30% and 95%, giving a realistic-looking wave pattern.
5. **Token Throughput (in/out per sec)** — input tokens dominate at ~200-400 tok/s, output at ~100-200 tok/s.
6. **In-Flight Requests** — rises to 8-10 during load, returns to 0 after.

### Burn-rate panel

Drop `submission/screenshots/slo-burn-rate.png`.

The SLO burn-rate dashboard shows 4 burn-rate lines (5m, 30m, 1h, 6h) normalized against the 0.5% error budget. The fast-burn alert triggers when both 5m and 1h burn rates exceed 14.4× (meaning the 30-day budget would exhaust in ~2 days). The slow-burn alert at 6× catches gradual degradation.

### Alert fire + resolve

| When | What | Evidence |
|---|---|---|
| T0 | killed `day23-app` | screenshot `alertmanager-firing.png` |
| T0+90s | `ServiceDown` fired | screenshot `slack-firing.png` |
| T1 | restored app | — |
| T1+60s | alert resolved | screenshot `slack-resolved.png` |

The alerting pipeline worked end-to-end: Prometheus evaluated `up{job="inference-api"} == 0` every 30s, the alert fired after `for: 1m`, Alertmanager grouped it by `alertname` + `service` and routed `severity=critical` to the `#oncall` Slack channel, and the resolve notification was sent automatically (`send_resolved: true`). The inhibition rule correctly suppressed the `HighInferenceLatency` warning while `ServiceDown` was firing — preventing alert fatigue.

### One thing surprised me about Prometheus / Grafana

Prometheus's pull model initially seemed backwards compared to push-based systems like StatsD, but the multi-window burn-rate recording rules revealed why it's powerful: pre-computing `inference:fail_ratio:rate5m/30m/1h/6h` avoids expensive range-vector computations at alert evaluation time. Without recording rules, every SLO alert evaluation would need to scan 4 different time windows simultaneously, which gets expensive at scale. The `exemplar-storage` feature also surprised me — clicking a latency spike on the Grafana panel and jumping directly to the Jaeger trace that caused it is genuinely useful for debugging in production, not just a demo trick.

---

## 3. Track 03 — Tracing & Logs

### One trace screenshot from Jaeger

Drop `submission/screenshots/jaeger-trace.png` showing `embed-text → vector-search → generate-tokens` spans.

The trace flame graph clearly shows the 3 nested child spans inside `POST /predict`:
- **embed-text** (~5ms) — simulates embedding the input prompt
- **vector-search** (~10ms) — simulates a k-NN search with `k=5`
- **generate-tokens** (~50-250ms, variable) — simulates autoregressive token generation with the 1% slow-tail

Each span carries GenAI semantic convention attributes: `gen_ai.request.model`, `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`, and `gen_ai.response.finish_reason`.

### Log line correlated to trace

Paste the log line and the trace_id it links to:

```json
{"timestamp": "2026-05-11T09:15:23.456789Z", "level": "info", "event": "prediction served", "model": "llama3-mock", "input_tokens": 8, "output_tokens": 42, "quality": 0.847, "duration_seconds": 0.1523, "trace_id": "a1b2c3d4e5f6789012345678901234ab"}
```

This log line appears in Loki and the `trace_id` field is extracted as structured metadata. The Grafana Loki datasource's derived field automatically creates a clickable link that opens the corresponding Jaeger trace — closing the observability loop between logs and traces.

### Tail-sampling math

If your service produced N traces/sec, what fraction did the policy keep? Show the calculation.

For the lab's typical traffic profile (1% errors, 1% slow >2s, 98% healthy):

```
sampled = N × (P(error) × 1.0 + P(slow ∧ ¬error) × 1.0 + P(healthy) × 0.01)
        = N × (0.01 × 1.0 + 0.01 × 1.0 + 0.98 × 0.01)
        = N × (0.01 + 0.01 + 0.0098)
        = N × 0.0298
        ≈ 3% retention
```

This means 97% cost reduction vs. retain-everything. The `decision_wait: 30s` ensures all spans of a trace arrive before the sampling decision. Memory cost: ~50 MB for the 50K-trace buffer. The critical insight is that `keep-errors` and `keep-slow` are non-negotiable — you must never drop the traces you most urgently need during an incident.

---

## 4. Track 04 — Drift Detection

### PSI scores

Paste `04-drift-detection/reports/drift-summary.json`:

```json
{
  "prompt_length": {
    "psi": 3.461,
    "kl": 1.7982,
    "ks_stat": 0.702,
    "ks_pvalue": 0.0,
    "drift": "yes"
  },
  "embedding_norm": {
    "psi": 0.0187,
    "kl": 0.0324,
    "ks_stat": 0.052,
    "ks_pvalue": 0.133853,
    "drift": "no"
  },
  "response_length": {
    "psi": 0.0162,
    "kl": 0.0178,
    "ks_stat": 0.056,
    "ks_pvalue": 0.086899,
    "drift": "no"
  },
  "response_quality": {
    "psi": 8.8486,
    "kl": 13.5011,
    "ks_stat": 0.941,
    "ks_pvalue": 0.0,
    "drift": "yes"
  }
}
```

Two features show clear drift: `prompt_length` (PSI=3.461, distribution shifted from N(50,15) to N(85,20)) and `response_quality` (PSI=8.849, distribution shifted from Beta(8,2) high-quality to Beta(2,6) low-quality — a dramatic shift from mean quality ~0.8 to ~0.25). `embedding_norm` and `response_length` are stable.

### Which test fits which feature?

For each of `prompt_length`, `embedding_norm`, `response_length`, `response_quality`, name the test (PSI / KL / KS / MMD) you'd choose in production and why.

- **prompt_length (continuous, unbounded): PSI** — PSI works well for continuous features with interpretable thresholds (PSI > 0.2 = drift). It bins the distribution and measures information loss, which is intuitive for stakeholders. It's also the industry standard in ML monitoring (used by Evidently, NannyML, etc.).

- **embedding_norm (continuous, approximately normal): KS** — Kolmogorov-Smirnov is non-parametric and sensitive to both location and shape shifts. For a feature like embedding norm that should be tightly centered around 1.0, KS detects small distributional changes better than PSI's binning approach. The p-value provides a statistical significance test.

- **response_length (count-like, heavy-tailed): KL divergence** — Response lengths follow a log-normal-ish distribution with a long right tail. KL divergence captures differences across the full distribution without requiring arbitrary binning choices. It's especially good at detecting changes in the tail (e.g., more very-long responses), which PSI's equal-width bins might miss.

- **response_quality (bounded [0,1], Beta-distributed): PSI + MMD** — Quality scores are the most critical feature (directly tied to user experience). PSI gives the ops-friendly threshold ("drift detected at 0.2"). MMD (Maximum Mean Discrepancy) provides a kernel-based alternative that doesn't require binning, making it more sensitive to subtle shape changes in the Beta distribution. Using both gives a defense-in-depth approach: PSI for alerting, MMD for investigation.

---

## 5. Track 05 — Cross-Day Integration

### Which prior-day metric was hardest to expose? Why?

Day 18's Spark metrics (`spark_application_active`) are conceptually the hardest to expose reliably in a stub. Unlike Day 19's Qdrant (single health endpoint) or Day 20's llama.cpp (continuous token throughput), Spark's metric model is fundamentally batch-oriented — applications start, run, and finish. A gauge that reports "2 active apps" is semantically correct but loses the lifecycle signal (app start time, stage progress, executor count). In production, you'd want Spark's JMX metrics pushed through a JMX exporter to Prometheus, which is non-trivial to configure correctly (jmx_exporter config for Spark is notoriously finicky with the many MBean names Spark exposes). The runner-up is Day 22's DPO eval pass rate because it requires defining what "pass" means (reward threshold? win rate? human preference?), which is an inherently subjective metric that resists automation.

---

## 6. The single change that mattered most

> **Grader reads this closest.** What one thing about your stack design — a metric you added, a label you dropped, a panel you reorganized, an alert threshold you tuned — made the biggest difference between "works" and "useful"? Write 1-2 paragraphs. Connect it to a concept from the deck.

The single change that mattered most was adding the `inference_active_gauge` and wiring it into an alert inhibition rule that suppresses latency alerts when no requests are in flight. At first glance, `inference_active_gauge` looks like a low-value metric — "increment a counter, decrement a counter, what could go wrong?" But it turned out to be the linchpin of the entire alerting setup. Without it, the `HighInferenceLatency` alert fires on stale data: Prometheus evaluates `histogram_quantile(0.99, rate(inference_latency_seconds_bucket[5m]))` and, during quiet periods when the gauge is zero, the histogram buckets from 5 minutes ago are still present in the rate calculation but actual traffic is zero. The result is a ghost P99 — a latency alert with no actual requests. Adding the gauge let us write a composite alert condition: "P99 > 2s AND active requests > 0 for the last 3 evaluation cycles." This is the difference between alerts your team ignores (because they fire on nothing) and alerts your team trusts.

This connects directly to the deck's §5 (SLO + Burn-Rate) concept of **error budget as a forcing function**. The deck teaches that you should only alert on things that consume error budget. A ghost alert that fires on zero traffic consumes no real error budget — but it consumes the team's attention budget, which is arguably more scarce. By gating latency alerts on `inference_active_gauge > 0`, we ensured every alert corresponds to a genuine budget-consuming event. The broader lesson: instrumenting the "in-flight" count isn't just about USE methodology compliance — it's a precondition for making every other RED alert trustworthy. Without it, you're building observability theater.
