# Submission Screenshot Checklist

Each rubric checkpoint that requires visual evidence is listed below.
Save all screenshots to `submission/screenshots/`.

## Core (100 pts)

### Track 01 — Instrumentation

- [ ] **Checkpoint #4** — `inference_active_gauge` rises during load, returns to 0 after
  - URL: `http://localhost:8000/metrics` — search for `inference_active_gauge`
  - Save as: `submission/screenshots/metrics-active-gauge.png`
  - How: `watch -n 1 'curl -s http://localhost:8000/metrics | grep inference_active_gauge'` during `make load`

### Track 02 — Dashboards & Alerts

- [ ] **Checkpoint #7** — AI Service Overview 6 panels with data after load
  - URL: `http://localhost:3000/d/day23-ai-overview`
  - Save as: `submission/screenshots/dashboard-overview.png`
  - Pre-condition: `make load` completed

- [ ] **Checkpoint #8** — SLO burn-rate dashboard populates
  - URL: `http://localhost:3000/d/day23-slo`
  - Save as: `submission/screenshots/slo-burn-rate.png`
  - Pre-condition: some errors generated (use `ERROR_RATE=0.2 make load`)

- [ ] **Checkpoint #9** — Cost-and-tokens dashboard shows non-zero $/hr
  - URL: `http://localhost:3000/d/day23-cost-tokens`
  - Save as: `submission/screenshots/cost-and-tokens.png`
  - Pre-condition: `make load` completed

- [ ] **Checkpoint #10** — Alertmanager shows `ServiceDown` firing
  - URL: `http://localhost:9093/#/alerts`
  - Save as: `submission/screenshots/alertmanager-firing.png`
  - How: run `make alert`, capture during Step 2 while alert is active

- [ ] **Checkpoint #11** — Slack receives fire AND resolve
  - Save as: `submission/screenshots/slack-firing.png` and `submission/screenshots/slack-resolved.png`
  - Pre-condition: `SLACK_WEBHOOK_URL` set in `.env`

### Track 03 — Tracing & Logs

- [ ] **Checkpoint #12** — Jaeger trace with 3 child spans for `POST /predict`
  - URL: `http://localhost:16686/search` → find a trace → expand
  - Save as: `submission/screenshots/jaeger-trace.png`
  - How: `make trace`, copy the trace_id, paste into Jaeger search

- [ ] **Checkpoint #13** — Span attributes follow GenAI semantic conventions
  - URL: Same trace as above → click `generate-tokens` span → Tags tab
  - Save as: `submission/screenshots/jaeger-genai-attrs.png`
  - Show: `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`, `gen_ai.response.finish_reason`

### Track 04 — Drift

- [ ] **Checkpoint #17** — Evidently HTML report renders
  - Open: `04-drift-detection/reports/drift-report.html` in browser
  - Save as: `submission/screenshots/drift-report.png`

### Track 05 — Integration

- [ ] **Checkpoint #19** — At least 1 prior-day source connected
  - URL: `http://localhost:8000/metrics` on one of the stub ports (9101-9106)
  - Save as: `submission/screenshots/day19-metrics.png`
  - Or show: `http://localhost:3000/d/day23-cross-day` with data in Day 19 panel

- [ ] **Checkpoint #20** — Cross-day dashboard with all 6 panels
  - URL: `http://localhost:3000/d/day23-cross-day`
  - Save as: `submission/screenshots/cross-day-dashboard.png`

## Bonus (20 pts)

- [ ] **Bonus B1** — Pyroscope flame graph
  - URL: `http://localhost:4040` → select `day23-inference-api`
  - Save as: `submission/screenshots/pyroscope-flamegraph.png`

- [ ] **Bonus B2** — Langfuse LLM trace
  - URL: `http://localhost:3001` → Traces → click trace
  - Save as: `submission/screenshots/langfuse-trace.png`

---

## Quick capture order (one session)

```bash
# 1. Start everything
make setup          # one time
make up             # start 8-service stack
make integration-stubs  # start Day 16-22 stubs
sleep 30            # wait for Grafana provisioning

# 2. Generate data
make load           # populate dashboards (60s)
make trace          # get a trace_id

# 3. Screenshots: dashboards
open http://localhost:3000/d/day23-ai-overview   → screenshot
open http://localhost:3000/d/day23-slo            → screenshot
open http://localhost:3000/d/day23-cost-tokens    → screenshot
open http://localhost:3000/d/day23-cross-day      → screenshot

# 4. Screenshots: tracing
open http://localhost:16686/search                → screenshot trace flame graph

# 5. Screenshots: alerting
make alert          # in separate terminal, screenshot Alertmanager UI during fire
# then screenshot Slack after resolve

# 6. Screenshots: drift
make drift
open 04-drift-detection/reports/drift-report.html → screenshot

# 7. Screenshots: bonus
make bonus-langfuse
python3 BONUS-llm-native-obs/langfuse-trace.py
open http://localhost:3001                        → screenshot Langfuse trace

make bonus-pyroscope
python3 BONUS-ebpf-profiling/pyroscope-app.py &
make load
open http://localhost:4040                        → screenshot flame graph

# 8. Verify
make verify
```

## Auto-captured evidence

Run `make screenshots` to auto-capture:

- `submission/screenshots/metrics.txt` — metric families
- `submission/screenshots/dashboards.json` — Grafana dashboard list
- `submission/screenshots/alerts.json` — Alertmanager alert state
- `submission/screenshots/drift-summary.json` — drift results (copied from reports/)
