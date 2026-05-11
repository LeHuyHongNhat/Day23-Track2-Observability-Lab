## Day 23 Track 2 — Observability Lab orchestration
##
## Quick start:
##   make setup    # one-time: pull images, create .env
##   make up       # start the 8-service stack
##   make smoke    # verify all services healthy
##   make demo     # run end-to-end demo (load + alert + trace + drift)
##   make verify   # rubric gate — exit 0 if all checkpoints pass
##   make down     # stop the stack
##   make clean    # stop + remove volumes (destructive)

SHELL := /bin/bash
COMPOSE ?= docker compose

.PHONY: help setup up down restart logs smoke load alert trace drift demo verify clean lint-dashboards integration-stubs kill-stubs bonus-langfuse bonus-pyroscope screenshots

help:
	@grep -E '^##|^[a-zA-Z_-]+:.*?## ' Makefile | sed -E 's/^## ?//; s/:.*## /\t/' | column -t -s $$'\t'

setup: ## one-time install + .env scaffold
	@test -f .env || cp .env.example .env
	@bash 00-setup/pull-images.sh
	@python3 00-setup/verify-docker.py

up: ## start the stack
	$(COMPOSE) up -d
	@echo "Stack starting. Run 'make smoke' to verify (allow ~30s for first start)."

down: ## stop the stack (preserves volumes)
	$(COMPOSE) down

restart: down up ## stop + start

logs: ## tail logs from all services
	$(COMPOSE) logs -f --tail=50

smoke: ## health-check all 8 services
	@echo "Checking services..."
	@curl -fsS http://localhost:8000/healthz   > /dev/null && echo "  app:           OK"
	@curl -fsS http://localhost:9090/-/healthy > /dev/null && echo "  prometheus:    OK"
	@curl -fsS http://localhost:9093/-/healthy > /dev/null && echo "  alertmanager:  OK"
	@curl -fsS http://127.0.0.1:3000/api/health | grep -q '"database.*ok"' && echo "  grafana:       OK"
	@curl -fsS http://localhost:3100/ready     > /dev/null && echo "  loki:          OK"
	@curl -fsS http://localhost:16686/         > /dev/null && echo "  jaeger:        OK"
	@curl -fsS http://localhost:8888/metrics   > /dev/null && echo "  otel-collector: OK"
	@curl -fsS http://localhost:9080/ready      > /dev/null && echo "  promtail:      OK"
	@echo "Stack healthy."

load: ## run baseline locust load (concurrency=10, 60s)
	cd 02-prometheus-grafana/load-test && \
	  locust -f locustfile.py --headless -u 10 -r 2 -t 60s --host http://localhost:8000

alert: ## trigger an alert by killing the app, wait, then restore
	bash scripts/trigger-alert.sh

trace: ## generate an error-trace (100% kept by keep-errors policy) and print trace_id
	@echo "Generating error trace (kept 100% by tail-sampling keep-errors)..."
	@curl -sS -X POST http://127.0.0.1:8000/predict \
	  -H 'Content-Type: application/json' \
	  -d '{"prompt":"trace-demo","fail":true}' 2>/dev/null || true
	@echo ""
	@echo "Also generating a healthy trace (1% chance kept by probabilistic-1pct)..."
	@curl -sS -X POST http://127.0.0.1:8000/predict \
	  -H 'Content-Type: application/json' \
	  -d '{"prompt":"hello"}' | python3 -c 'import json,sys; d=json.load(sys.stdin); print("trace_id:",d.get("trace_id","?"))'
	@echo ""
	@echo "Wait 30s for OTel Collector tail-sampling decision, then search in Jaeger:"
	@echo "  http://127.0.0.1:16686/search"

drift: ## run drift detection notebook (cli mode)
	cd 04-drift-detection && python3 scripts/drift_detect.py

demo: ## end-to-end demo (stubs -> load -> trace -> drift -> alert)
	@echo "=== Day 23 End-to-End Demo ==="
	@echo "1/5 Starting integration stubs (background)..."
	@$(MAKE) integration-stubs
	@sleep 3
	@echo "2/5 Running load test (60s)..."
	@$(MAKE) load
	@echo "3/5 Generating trace..."
	@$(MAKE) trace
	@echo "4/5 Running drift detection..."
	@$(MAKE) drift
	@echo "5/5 Triggering alert fire/resolve..."
	@$(MAKE) alert
	@echo "=== Demo complete. Screenshots: make screenshots ==="

screenshots: ## capture key evidence for submission
	@mkdir -p submission/screenshots
	@echo "Capturing submission evidence..."
	@echo "--- /metrics (first 6 metric families) ---"
	@curl -fsS http://localhost:8000/metrics 2>/dev/null | grep -E '^inference_|^gpu_' | head -20 > submission/screenshots/metrics.txt || echo "(stack not running — run make up first)"
	@echo "--- Grafana dashboards ---"
	@curl -fsS -u admin:admin http://localhost:3000/api/search?query=Day 2>/dev/null | python3 -m json.tool > submission/screenshots/dashboards.json 2>/dev/null || echo "(grafana not reachable)"
	@echo "--- Alertmanager alerts ---"
	@curl -fsS http://localhost:9093/api/v2/alerts 2>/dev/null | python3 -m json.tool > submission/screenshots/alerts.json 2>/dev/null || echo "(alertmanager not reachable)"
	@echo "--- Drift summary ---"
	@cp 04-drift-detection/reports/drift-summary.json submission/screenshots/ 2>/dev/null || echo "(drift not yet run — make drift)"
	@echo ""
	@echo "Evidence captured in submission/screenshots/"
	@echo ""
	@echo "Manual screenshots still needed (open these URLs):"
	@echo "  Grafana Overview:  http://localhost:3000/d/day23-ai-overview"
	@echo "  Grafana SLO:       http://localhost:3000/d/day23-slo"
	@echo "  Grafana Cost:      http://localhost:3000/d/day23-cost-tokens"
	@echo "  Grafana Cross-Day: http://localhost:3000/d/day23-cross-day"
	@echo "  Jaeger trace:      http://localhost:16686/search"
	@echo "  Alertmanager:      http://localhost:9093/#/alerts"
	@echo "  Drift report:      open 04-drift-detection/reports/drift-report.html"
	@echo "  Langfuse (bonus):  http://localhost:3001"
	@echo "  Pyroscope (bonus): http://localhost:4040"

verify: ## rubric gate — exits 0 only if all checkpoints pass
	python3 scripts/verify.py

lint-dashboards: ## validate Grafana dashboard JSONs
	python3 scripts/lint-dashboards.py 02-prometheus-grafana/grafana/dashboards/*.json

integration-stubs: ## start all 6 Day 16-22 stub emitters on host
	@echo "Starting integration stubs on ports 9101-9106..."
	@python3 05-integration/monitor-day19-vector-store.py &
	@python3 05-integration/monitor-day20-llama-cpp.py &
	@python3 05-integration/monitor-day16-cloud.py &
	@python3 05-integration/monitor-day17-pipeline.py &
	@python3 05-integration/monitor-day18-lakehouse.py &
	@python3 05-integration/monitor-day22-alignment.py &
	@echo "All stubs running. Prometheus scrapes them on next scrape_interval."
	@echo "Kill with: make kill-stubs"

kill-stubs: ## kill all integration stub processes
	@pkill -f 'monitor-day1[6-9]' 2>/dev/null || true
	@pkill -f 'monitor-day2[0-2]' 2>/dev/null || true
	@echo "Stubs killed."

bonus-langfuse: ## start self-hosted Langfuse (Bonus B2)
	docker compose -f BONUS-llm-native-obs/docker-compose.langfuse.yml up -d
	@echo "Langfuse UI: http://localhost:3001"
	@echo "Generate trace: python3 BONUS-llm-native-obs/langfuse-trace.py"

bonus-pyroscope: ## start Pyroscope profiling server (Bonus B1)
	docker compose -f BONUS-ebpf-profiling/docker-compose.pyroscope.yml up -d
	@echo "Pyroscope UI: http://localhost:4040"
	@echo "Profile app: python3 BONUS-ebpf-profiling/pyroscope-app.py"

clean: ## stop stack + remove volumes (DESTRUCTIVE)
	$(COMPOSE) down -v
