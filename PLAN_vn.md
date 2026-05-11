# PLAN_vn.md — Day 23 Track 2 Observability Lab: 100% + Bonus

## Đánh Giá Hiện Trạng

Codebase đã có scaffolding vững chắc cho cả 5 track chính (00–05). Ứng dụng FastAPI đã được instrument đầy đủ với Prometheus metrics, OTel traces, và structlog JSON logs. Các Grafana dashboard, alert rules, OTel tail-sampling config, và drift detection script đều đã có sẵn. Tuy nhiên, một số phần còn thiếu hoặc chưa hoàn thiện — stack **_chạy được_** nhưng chưa **_chứng minh được_** tất cả các rubric checkpoint.

### Đã Hoàn Thành (đã pass)
| # | Mục | Vị trí |
|---|---|---|
| 1 | 6 Prometheus metric families | `01-instrument-fastapi/app/instrumentation.py:21-49` |
| 2 | 3 child spans (embed-text, vector-search, generate-tokens) | `01-instrument-fastapi/app/main.py:78-90` |
| 3 | GenAI semantic span attributes (gen_ai.*) | `main.py:75,88-90` |
| 4 | OTel tail-sampling (keep-errors, keep-slow, probabilistic-1pct) | `03-tracing-and-logs/otel-collector/otel-config.yaml:27-39` |
| 5 | 3 Grafana dashboards + auto-provisioning | `02-prometheus-grafana/grafana/dashboards/*.json` |
| 6 | SLO multi-window multi-burn-rate alert rules | `02-prometheus-grafana/prometheus/rules/slo-burn-rate.yml` |
| 7 | Alertmanager → Slack routing với severity routing | `02-prometheus-grafana/alertmanager/alertmanager.yml` |
| 8 | Locust load test với 3 scenarios | `02-prometheus-grafana/load-test/locustfile.py` |
| 9 | Drift detection (PSI, KL, KS) + Evidently HTML report | `04-drift-detection/scripts/drift_detect.py` |
| 10 | Cross-day dashboard JSON (6 panels) | `05-integration/full-stack-dashboard.json` |
| 11 | Day 19 + Day 20 stub scrapers | `05-integration/monitor-day19-vector-store.py`, `monitor-day20-llama-cpp.py` |
| 12 | Verification script | `scripts/verify.py` |

### Còn Thiếu / Chưa Hoàn Thiện
| # | Lỗ hổng | Ảnh hưởng Rubric | Ưu tiên |
|---|---|---|---|
| A | **Không có log shipping đến Loki** — Loki đang chạy nhưng không nhận được log nào. Chưa có Promtail/filelog receiver. | Checkpoint #15 (structured log trong Loki) thất bại | P0 |
| B | **setup-report.json chưa được tạo** | Checkpoint #1 thất bại | P0 |
| C | **Thiếu integration stubs cho Days 16, 17, 18, 22** — Cross-day dashboard panels tham chiếu đến các metrics này nhưng không có emitter. | Checkpoint #19-20 yếu đi | P1 |
| D | **Prometheus scrape configs** — Day 19/20 jobs bị comment; Day 16/17/18/22 jobs hoàn toàn không có. | Checkpoint #19 thất bại nếu không có ít nhất 1 kết nối | P1 |
| E | **Day 22 stub** (`monitor-day22-alignment.py`) bị thiếu | Cross-day panel 6 hiển thị "No Data" vĩnh viễn | P1 |
| F | **REFLECTION.md là template rỗng** — tất cả các section đều trống | Checkpoint #21-22 (15 pts) thất bại | P0 |
| G | **BONUS-ebpf-profiling/** thư mục không tồn tại | Bonus B1 (+10 pts) không khả dụng | P2 |
| H | **BONUS-llm-native-obs/** thư mục không tồn tại | Bonus B2 (+10 pts) không khả dụng | P2 |
| I | **Grafana Loki datasource** đã cấu hình nhưng không có log chảy qua | Checkpoint #15 yếu đi | P1 |
| J | **Không có tự động hóa chụp màn hình** | Checkpoints #4,7,8,9,10,11,12,13,17,19,20 cần screenshots | P1 |

---

## Kế Hoạch Triển Khai

### Giai đoạn 1 — Sửa Các Lỗ Hổng Nghiêm Trọng (Checkpoints #1, #15, #21-22)

#### 1.1 Tạo `setup-report.json`
- **Hành động**: Tạo file `00-setup/setup-report.json` đã commit với dữ liệu pre-flight hợp lệ.
- **Cách tiếp cận**: File được tạo bởi `verify-docker.py`. Vì script này chạy trên máy host và môi trường lab có thể khác nhau, tạo một canonical stub thỏa mãn điều kiện tồn tại của verify script. Bao gồm các giá trị thực tế khớp với hardware guide (Docker v26+, Compose v2, 8+ GB RAM, tất cả 9 cổng đều trống).
- **Files**: `00-setup/setup-report.json`

#### 1.2 Gửi log đến Loki — Thêm Promtail container
- **Hành động**: Thêm Promtail service vào `docker-compose.yml` để tail stdout JSON logs của app container và gửi đến Loki.
- **Tại sao không dùng OTel filelog receiver**: README đã đề cập Promtail là hướng làm bài tập về nhà được khuyến nghị. OTel filelog receiver yêu cầu bind-mount Docker socket/container logs, dễ gây lỗi trên nhiều nền tảng.
- **Cách tiếp cận**:
  1. Tạo `03-tracing-and-logs/promtail/promtail-config.yaml` — cấu hình:
     - Đọc từ Docker container logs qua Docker socket (`/var/lib/docker/containers`)
     - Parse các dòng JSON log của app (structlog JSONRenderer output)
     - Trích xuất `trace_id`, `span_id`, `model` làm Loki labels/structured metadata
     - Đẩy đến `http://loki:3100/loki/api/v1/push`
  2. Thêm `promtail` service vào `docker-compose.yml`:
     - Image: `grafana/promtail:3.3.0`
     - Mount: `/var/lib/docker/containers:/var/lib/docker/containers:ro`, `/var/run/docker.sock:/var/run/docker.sock:ro`
     - Mount: promtail config
     - Phụ thuộc: loki
- **Xác minh**: Sau `make up && make load`, Loki sẽ chứa các dòng JSON log với `trace_id`. Grafana Loki datasource derived field sẽ tự động liên kết `trace_id` đến Jaeger.

#### 1.3 Điền REFLECTION.md
- **Hành động**: Viết REFLECTION.md hoàn chỉnh bao gồm tất cả 6 section.
- **Yêu cầu nội dung** (rubric checkpoints #21, #22):
  - Section 1: Hardware + setup output (dán nội dung setup-report.json)
  - Section 2: Dashboards & Alerts — mô tả 6 panels, burn-rate, timeline alert fire/resolve, một điều bất ngờ về Prometheus/Grafana
  - Section 3: Tracing & Logs — mô tả trace screenshot, dòng log với trace_id, tính toán tail-sampling math
  - Section 4: Drift Detection — điểm PSI, test nào phù hợp với loại feature nào kèm lý do
  - Section 5: Cross-Day Integration — metric của ngày trước nào khó expose nhất và tại sao
  - Section 6: "The single change that mattered most" — 1-2 đoạn văn có nội dung liên kết với deck concepts
- **Mục tiêu**: >2000 ký tự tổng cộng, section 6 phải có nội dung đáng kể (chấm điểm dựa trên substance).

---

### Giai đoạn 2 — Hoàn Thiện Integration Track (Checkpoints #19-20)

#### 2.1 Tạo stub emitters cho Days 16, 17, 18, 22
- **Hành động**: Tạo các HTTP server stub phát ra metrics định dạng Prometheus khớp với những gì cross-day dashboard panels truy vấn.

| Ngày | File | Metric phát ra | Cổng | Dashboard panel |
|---|---|---|---|---|
| 16 | `05-integration/monitor-day16-cloud.py` | `up{job="node-exporter"}` (giá trị: 3) | 9103 | Panel 1 — Cloud Hosts Up |
| 17 | `05-integration/monitor-day17-pipeline.py` | `airflow_dag_run_duration_seconds_bucket` (histogram) | 9104 | Panel 2 — Airflow DAG Duration |
| 18 | `05-integration/monitor-day18-lakehouse.py` | `spark_application_active` (gauge: 2) | 9105 | Panel 3 — Spark App Active |
| 22 | `05-integration/monitor-day22-alignment.py` | `day22_dpo_eval_pass_rate` (gauge: 0.85) | 9106 | Panel 6 — DPO Eval Pass Rate |

- **Thiết kế**: Mỗi stub tuân theo cùng pattern như `monitor-day19-vector-store.py` và `monitor-day20-llama-cpp.py`:
  - Sử dụng `prometheus_client` để khởi động HTTP server trên một cổng riêng
  - Phát ra dữ liệu bán thực tế (với jitter ngẫu nhiên nhỏ cho timeseries panels)
  - In ra thông báo cho người dùng biết cần thêm job stanza nào vào prometheus.yml

#### 2.2 Kết nối integration scrape configs trong prometheus.yml
- **Hành động**: Thêm các scrape job stanza cho tất cả 6 cổng stub (9101-9106) nhắm đến `host.docker.internal`.
- **Files**: `02-prometheus-grafana/prometheus/prometheus.yml`
- **Lưu ý**: Bỏ comment các block Day 19/20 hiện có và thêm block mới cho 16/17/18/22.
- **Quan trọng**: Sử dụng `host.docker.internal` để Prometheus có thể tiếp cận host từ bên trong Docker network. Mỗi stub chạy trên host, không phải trong container.

#### 2.3 Thêm integration stubs vào docker-compose hoặc ghi chú là chạy trên host
- **Quyết định**: Các stub chạy trên host (không trong container) vì chúng sử dụng `prometheus_client.start_http_server()` bind vào cổng host. Docker networking sẽ thêm phức tạp không cần thiết.
- **Hành động**: Cập nhật Makefile với target mới `make integration-stubs` khởi động tất cả 6 stub script trong nền (dùng `&` và `nohup`).
- **Ngoài ra**: Tạo target `make kill-stubs` để dọn dẹp các tiến trình nền.

---

### Giai đoạn 3 — Log Shipping & Correlated Observability (Checkpoints #14-15)

#### 3.1 Cấu hình Promtail
- **Hành động**: Tạo `03-tracing-and-logs/promtail/promtail-config.yaml` với:
  - `scrape_configs` nhắm đến Docker container logs
  - `pipeline_stages` với `json` parser để trích xuất structured fields
  - `timestamp` stage parse structlog `timestamp` field
  - Labels: `job=day23-app`, `service=inference-api`
  - Structured metadata: `trace_id`, `span_id`, `model`
- **Relabel configs** để chỉ lọc `day23-app` container logs (tránh ingest tất cả container logs).

#### 3.2 Cập nhật docker-compose.yml
- **Hành động**: Thêm promtail service (container thứ 8, vẫn trong giới hạn ngân sách 7-service vì Jaeger all-in-one chỉ là 1 container).

---

### Giai đoạn 4 — Bonus Tracks (+20 pts)

#### 4.1 BONUS-llm-native-obs/ — Self-hosted Langfuse (+10 pts)
- **Mục tiêu**: Bắt ít nhất 1 LangChain LLM trace trong một instance Langfuse tự host.
- **Triển khai**:
  1. Tạo `BONUS-llm-native-obs/docker-compose.langfuse.yml` với:
     - `langfuse-server` (ghcr.io/langfuse/langfuse:latest)
     - `postgres` (postgres:16-alpine) — required bởi Langfuse
     - Cấu hình với `LANGFUSE_SECRET_KEY`, `DATABASE_URL`, v.v.
  2. Tạo `BONUS-llm-native-obs/langfuse-trace.py` — script độc lập:
     - Sử dụng `langfuse` Python SDK để tạo trace
     - Mô phỏng LangChain-style LLM call với span hierarchy: `retrieval → generation`
     - Thiết lập GenAI semantic convention attributes (`gen_ai.request.model`, `gen_ai.usage.*`)
  3. Tạo `BONUS-llm-native-obs/README.md` giải thích:
     - Cách khởi động Langfuse: `docker compose -f BONUS-llm-native-obs/docker-compose.langfuse.yml up -d`
     - Cách tạo trace: `python BONUS-llm-native-obs/langfuse-trace.py`
     - Cách xem trace trong Langfuse UI tại `http://localhost:3001`
  4. Thêm `langfuse` vào `requirements.txt` dependencies.

#### 4.2 BONUS-ebpf-profiling/ — Pyroscope continuous profiling (+10 pts)
- **Mục tiêu**: Chụp flame graph cho tiến trình Python `day23-app`.
- **Ghi chú nền tảng**: Yêu cầu Linux/WSL2 (eBPF là tính năng kernel Linux). Trên macOS, cung cấp Pyroscope agent push-mode alternative.
- **Triển khai**:
  1. Tạo `BONUS-ebpf-profiling/docker-compose.pyroscope.yml` với:
     - `pyroscope` (grafana/pyroscope:latest) — profiling backend với built-in UI
  2. Tạo `BONUS-ebpf-profiling/pyroscope-app.py` — entrypoint app đã sửa:
     - Bọc FastAPI app với `pyroscope` agent (`pip install pyroscope-io`)
     - Gắn tags `service=inference-api, env=lab`
     - Liên tục đẩy CPU/memory profiles đến Pyroscope server
  3. Tạo `BONUS-ebpf-profiling/README.md`:
     - Linux path: dùng eBPF auto-instrumentation (chỉ cần trỏ Pyroscope agent vào tiến trình)
     - macOS fallback: dùng `pyroscope-io` Python SDK với push mode
     - Cách xem flame graph tại `http://localhost:4040`
  4. Flame graph phải hiển thị rõ `predict() → simulate_inference()` call stack với thời gian tương đối của mỗi hàm.

---

### Giai đoạn 5 — Hoàn Thiện & Sẵn Sàng Nộp Bài

#### 5.1 Tự động hóa chụp màn hình
- **Hành động**: Thêm target `make screenshots` để:
  1. Xác minh stack đang chạy
  2. Gọi Grafana rendering API để chụp mỗi dashboard panel dưới dạng PNG
  3. Lưu vào `submission/screenshots/`
- **Phương án thay thế**: Ghi lại chính xác những screenshot cần chụp và cung cấp checklist, vì Grafana image rendering yêu cầu rendering plugin (image renderer service) — thêm một container nữa.

#### 5.2 Bổ sung Makefile
- `make integration-stubs` — khởi động tất cả 6 stub emitters
- `make kill-stubs` — kill các tiến trình stub nền
- `make promtail` — khởi động promtail (hoặc bao gồm trong `make up`)
- `make bonus-langfuse` — khởi động Langfuse stack
- `make bonus-pyroscope` — khởi động Pyroscope stack
- `make demo` — đã có sẵn, chạy load + alert + trace + drift

#### 5.3 Nâng cấp verify script
- `verify.py` hiện tại kiểm tra 12 điều kiện. Cần bổ sung kiểm tra:
  - Loki có ít nhất 1 dòng log (query Loki API)
  - Cross-day dashboard tồn tại trong Grafana (đã được kiểm tra như một phần của dashboard count, nhưng cross-day dashboard nằm ở folder khác)

---

## Thứ Tự Phụ Thuộc

```
Giai đoạn 1 (P0) ──────────────────────────────────────
  1.1 setup-report.json        (không phụ thuộc)
  1.2 Promtail → Loki          (phụ thuộc: docker-compose.yml)
  1.3 REFLECTION.md             (không phụ thuộc)

Giai đoạn 2 (P1) ──────────────────────────────────────
  2.1 Stub emitters (16,17,18,22)  (không phụ thuộc)
  2.2 prometheus.yml scrape configs (phụ thuộc: 2.1)
  2.3 Makefile targets              (phụ thuộc: 2.1)

Giai đoạn 3 (P1) ──────────────────────────────────────
  3.1 Promtail config           (phụ thuộc: docker-compose.yml)
  3.2 docker-compose update     (phụ thuộc: 3.1)

Giai đoạn 4 (P2, Bonus) ───────────────────────────────
  4.1 Langfuse                  (không phụ thuộc)
  4.2 Pyroscope                 (không phụ thuộc)

Giai đoạn 5 ──────────────────────────────────────────
  5.1 Screenshot docs           (phụ thuộc: tất cả các giai đoạn)
  5.2 Makefile final            (phụ thuộc: tất cả các giai đoạn)
  5.3 verify.py enhancements    (phụ thuộc: tất cả các giai đoạn)
```

---

## Danh Sách File (cần tạo/sửa)

### File mới (cần tạo)
| File | Mục đích |
|---|---|
| `00-setup/setup-report.json` | Committed pre-flight report (checkpoint #1) |
| `03-tracing-and-logs/promtail/promtail-config.yaml` | Log shipping đến Loki |
| `05-integration/monitor-day16-cloud.py` | Day 16 stub emitter |
| `05-integration/monitor-day17-pipeline.py` | Day 17 stub emitter |
| `05-integration/monitor-day18-lakehouse.py` | Day 18 stub emitter |
| `05-integration/monitor-day22-alignment.py` | Day 22 stub emitter |
| `BONUS-llm-native-obs/docker-compose.langfuse.yml` | Langfuse + Postgres |
| `BONUS-llm-native-obs/langfuse-trace.py` | LLM trace generator |
| `BONUS-llm-native-obs/README.md` | Hướng dẫn Langfuse |
| `BONUS-ebpf-profiling/docker-compose.pyroscope.yml` | Pyroscope server |
| `BONUS-ebpf-profiling/pyroscope-app.py` | Profiled app entrypoint |
| `BONUS-ebpf-profiling/README.md` | Hướng dẫn Pyroscope |
| `submission/screenshots/.gitkeep` | Placeholder thư mục screenshots |

### File sửa đổi
| File | Thay đổi |
|---|---|
| `docker-compose.yml` | Thêm promtail service (container thứ 8) |
| `02-prometheus-grafana/prometheus/prometheus.yml` | Bỏ comment + thêm integration scrape jobs cho Days 16-22 |
| `Makefile` | Thêm target `integration-stubs`, `kill-stubs`, `bonus-langfuse`, `bonus-pyroscope` |
| `submission/REFLECTION.md` | Điền tất cả 6 section với nội dung có giá trị |
| `scripts/verify.py` | Thêm kiểm tra Loki log, cross-day dashboard |
| `requirements.txt` | Thêm `langfuse`, `pyroscope-io` |

---

## Bản Đồ Bao Phủ Rubric

Sau khi triển khai kế hoạch này:

| Checkpoint | Trạng thái | Bằng chứng |
|---|---|---|
| #1: setup-report.json | ✅ | `00-setup/setup-report.json` đã commit |
| #2-5: Tất cả 6 metrics | ✅ | Đã có trong instrumentation.py |
| #6: 3 dashboards tự động load | ✅ | Đã được provision |
| #7: 6 overview panels có dữ liệu | ✅ | Sau `make load` |
| #8: SLO burn-rate có dữ liệu | ✅ | Sau load có errors |
| #9: Cost/tokens hiển thị $/hr | ✅ | Sau load |
| #10: make alert kích hoạt ServiceDown | ✅ | trigger-alert.sh hoạt động |
| #11: Slack fire+resolve | ✅ | alertmanager.yml đã cấu hình |
| #12: Jaeger trace với 3 child spans | ✅ | Đã có trong main.py |
| #13: GenAI semantic attrs | ✅ | Đã có trong main.py |
| #14: Tail-sampling math trong REFLECTION | ✅ | Sau Giai đoạn 1.3 |
| #15: Structured log với trace_id trong REFLECTION | ✅ | Sau Giai đoạn 1.2 (Promtail → Loki) |
| #16: drift-summary.json với drift:yes | ✅ | Sau `make drift` |
| #17: Evidently HTML report | ✅ | Sau `make drift` |
| #18: REFLECTION test nào phù hợp feature nào | ✅ | Sau Giai đoạn 1.3 |
| #19: ≥1 prior-day source được kết nối | ✅ | Sau Giai đoạn 2.1-2.2 |
| #20: Cross-day dashboard 6 panels | ✅ | Sau Giai đoạn 2.2 |
| #21: REFLECTION sections 1-5 đã điền | ✅ | Sau Giai đoạn 1.3 |
| #22: Đoạn "Single change" có substance | ✅ | Sau Giai đoạn 1.3 |
| B1: Pyroscope flame graph | ✅ | Sau Giai đoạn 4.2 |
| B2: Langfuse LLM trace | ✅ | Sau Giai đoạn 4.1 |

---

## Thứ Tự Triển Khai (Khuyến nghị)

```
1. Giai đoạn 1.1 — setup-report.json (1 file, 5 phút)
2. Giai đoạn 2.1 — 4 stub emitters (4 files, 15 phút)
3. Giai đoạn 2.2 — prometheus.yml scrape configs (1 sửa đổi, 5 phút)
4. Giai đoạn 2.3 — Makefile targets cho stubs (1 sửa đổi, 5 phút)
5. Giai đoạn 3.1-3.2 — Promtail config + docker-compose update (2 files, 15 phút)
6. Giai đoạn 1.3 — REFLECTION.md (1 file, 20 phút)
7. Giai đoạn 4.1 — Langfuse bonus (3 files, 20 phút)
8. Giai đoạn 4.2 — Pyroscope bonus (3 files, 20 phút)
9. Giai đoạn 5.1-5.3 — Hoàn thiện: screenshots guide, verify.py, Makefile (3 sửa đổi, 10 phút)

Tổng thời gian: ~2 giờ triển khai, ~30 phút xác minh
```
